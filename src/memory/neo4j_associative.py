from __future__ import annotations

import os
import re
from typing import List, Dict, Any, Optional

from neo4j import GraphDatabase, basic_auth

try:
   
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


REL_TYPE_REGEX = re.compile(r"^[A-Z][A-Z0-9_]*$")  


class Neo4jAssociativeStore:
    

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        self._uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self._user = user or os.getenv("NEO4J_USER", "neo4j")
        self._password = password or os.getenv("NEO4J_PASSWORD", "neo4j")
        self._database = database or os.getenv("NEO4J_DATABASE", "neo4j")

        
        self._driver = GraphDatabase.driver(
            self._uri,
            auth=basic_auth(self._user, self._password),
        )

       
        try:
            self._driver.verify_connectivity()
        except Exception as e:
            raise RuntimeError(
                f"Neo4j connectivity/auth failed for {self._uri} as {self._user}: {e!r}"
            )

    
    def startup(self) -> None:
        self._ensure_constraints()

    def close(self) -> None:
        self._driver.close()

    

    def _session(self):
        
        return self._driver.session(database=self._database)

    def _ensure_constraints(self) -> None:
        stmts = [
            
            "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
        ]
        with self._session() as s:
            for q in stmts:
                s.run(q)

    # ---------- Entities ----------

    def upsert_entity(
        self,
        name: str,
        labels: Optional[List[str]] = None,
        props: Optional[Dict[str, Any]] = None,
    ) -> None:
        labels = [lbl for lbl in (labels or []) if lbl]  
        props = props or {}

      
        safe_labels = []
        for lbl in labels:
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", lbl):
                raise ValueError(f"Invalid label: {lbl!r}")
            safe_labels.append(lbl)

        label_str = ":".join(["Entity"] + safe_labels)
        cypher = f"MERGE (e:{label_str} {{name: $name}}) SET e += $props"

        with self._session() as s:
            s.run(cypher, name=name, props=props)

    def get_entity(self, name: str) -> Dict[str, Any] | None:
        q = "MATCH (e:Entity {name: $name}) RETURN labels(e) AS labels, e AS node"
        with self._session() as s:
            rec = s.run(q, name=name).single()
            if not rec:
                return None
            node = rec["node"]
            
            data = {k: v for k, v in node.items() if k != "name"}
            data.update({"name": node["name"], "labels": rec["labels"]})
            return data

    # ---------- Relations ----------

    def upsert_relation(
        self,
        source: str,
        rel_type: str,
        target: str,
        rel_props: Optional[Dict[str, Any]] = None,
    ) -> None:
        rel_props = rel_props or {}

       
        if not REL_TYPE_REGEX.fullmatch(rel_type):
            raise ValueError(
                f"Invalid relation type {rel_type!r}. "
                "Must be UPPERCASE letters, digits, underscore; start with a letter."
            )

        cypher = (
            f"MERGE (a:Entity {{name: $source}}) "
            f"MERGE (b:Entity {{name: $target}}) "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            f"SET r += $rel_props"
        )
        with self._session() as s:
            s.run(cypher, source=source, target=target, rel_props=rel_props)

    def get_outbound(self, source: str) -> List[Dict[str, Any]]:
        q = (
            "MATCH (a:Entity {name: $source})-[r]->(b:Entity) "
            "RETURN type(r) AS rel, b.name AS name, properties(r) AS props"
        )
        with self._session() as s:
            return [dict(row) for row in s.run(q, source=source)]

    def get_inbound(self, target: str) -> List[Dict[str, Any]]:
        q = (
            "MATCH (a:Entity)-[r]->(b:Entity {name: $target}) "
            "RETURN type(r) AS rel, a.name AS name, properties(r) AS props"
        )
        with self._session() as s:
            return [dict(row) for row in s.run(q, target=target)]

    def path_between(self, a: str, b: str, max_hops: int = 4) -> List[Dict[str, Any]]:
      
        if not isinstance(max_hops, int) or max_hops < 1 or max_hops > 10:
            raise ValueError("max_hops must be an integer between 1 and 10")

        q = (
            f"MATCH p = shortestPath((x:Entity {{name: $a}})-[*..{max_hops}]-(y:Entity {{name: $b}})) "
            f"RETURN [n IN nodes(p) | n.name] AS nodes, [r IN relationships(p) | type(r)] AS rels"
        )
        with self._session() as s:
            rec = s.run(q, a=a, b=b).single()
            if not rec:
                return []
            return [{"nodes": rec["nodes"], "relations": rec["rels"]}]
