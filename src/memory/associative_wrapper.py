import json
import sys
from typing import List, Dict, Any, Optional
from openai import OpenAI

if __name__ == "__main__":
    from src.config.settings import OPENAI_API_KEY
    from src.memory.neo4j_associative import Neo4jAssociativeStore
else:
    from ..config.settings import OPENAI_API_KEY
    from .neo4j_associative import Neo4jAssociativeStore


class AssociativeMemoryWrapper:
    
    def __init__(self, neo4j_store: Optional[Neo4jAssociativeStore] = None):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.neo4j = neo4j_store or Neo4jAssociativeStore()
        self.model = "gpt-4o-mini"
    
    def _extract_entities_and_relationships(self, text: str) -> Dict[str, Any]:
        """Use OpenAI to extract entities and relationships"""
        
        system_prompt = """You are an expert knowledge graph builder. Extract entities and relationships from text.

Return JSON with this structure:
{
  "entities": [
    {
      "name": "entity_name",
      "labels": ["Label1", "Label2"],
      "props": {
        "description": "brief description",
        "key": "value"
      }
    }
  ],
  "relationships": [
    {
      "source": "entity1_name",
      "relation": "RELATIONSHIP_TYPE",
      "target": "entity2_name",
      "props": {
        "description": "relationship description"
      }
    }
  ]
}

Rules:
- Entity names: clear identifiers (e.g., "Dhoni", "CSK", "IPL")
- Labels: categorize entities (e.g., ["Person"], ["Organization", "SportsTeam"])
- Relationship types: UPPERCASE with underscores (e.g., "CAPTAIN_OF", "PLAYS_IN")
- Always include "description" in props
- Only relationships between extracted entities
- Return empty arrays if no clear entities/relationships"""

        user_prompt = f"""Analyze this text and extract entities and relationships:

"{text}"

Return only valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3, 
                response_format={"type": "json_object"} 
            )
            
            content = response.choices[0].message.content
            extracted_data = json.loads(content)
            
            # Validate structure
            for entity in extracted_data.get("entities", []):
                if "name" not in entity:
                    entity["name"] = "Unknown"
                if "labels" not in entity:
                    entity["labels"] = []
                if "props" not in entity:
                    entity["props"] = {}
            
            for rel in extracted_data.get("relationships", []):
                if "source" not in rel or "relation" not in rel or "target" not in rel:
                    continue
                if "props" not in rel:
                    rel["props"] = {}
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Response content: {content}")
            return {"entities": [], "relationships": []}
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return {"entities": [], "relationships": []}
    
    def process_text(
        self, 
        text: str, 
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract and store entities/relationships"""
        
        print(f"Analyzing text with {self.model}")
        extracted = self._extract_entities_and_relationships(text)
        
        entities_created = []
        relationships_created = []
        errors = []
        
        # Create entities
        print(f"Creating {len(extracted.get('entities', []))} entities")
        for entity in extracted.get("entities", []):
            try:
                name = entity.get("name")
                labels = entity.get("labels", [])
                props = entity.get("props", {})
                
                if agent_id:
                    props["agent_id"] = agent_id
                
                props["created_by"] = "associative_wrapper"
                props["source_text"] = text[:200]
                
                self.neo4j.upsert_entity(name, labels, props)
                entities_created.append({
                    "name": name,
                    "labels": labels,
                    "props": props
                })
                
            except Exception as e:
                errors.append(f"Error creating entity {entity.get('name')}: {str(e)}")
        
        # Create relationships
        print(f"Creating {len(extracted.get('relationships', []))} relationships")
        for rel in extracted.get("relationships", []):
            try:
                source = rel.get("source")
                relation = rel.get("relation")
                target = rel.get("target")
                props = rel.get("props", {})
                
                if agent_id:
                    props["agent_id"] = agent_id
                
                self.neo4j.upsert_entity(source)
                self.neo4j.upsert_entity(target)
                
                rel_type = relation.strip().upper().replace(" ", "_")
                self.neo4j.upsert_relation(source, rel_type, target, props)
                
                relationships_created.append({
                    "source": source,
                    "relation": rel_type,
                    "target": target,
                    "props": props
                })
                
            except Exception as e:
                errors.append(f"Error creating relationship {rel.get('source')} -> {rel.get('target')}: {str(e)}")
        
        print(f"Created {len(entities_created)} entities and {len(relationships_created)} relationships")
        
        return {
            "status": "success",
            "text_analyzed": text,
            "entities_created": entities_created,
            "relationships_created": relationships_created,
            "entity_count": len(entities_created),
            "relationship_count": len(relationships_created),
            "errors": errors if errors else None
        }


if __name__ == "__main__":
    print("=" * 70)
    
    try:
        wrapper = AssociativeMemoryWrapper()
        print("Connected to OpenAI and Neo4j\n")
    except Exception as e:
        print(f"Error initializing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("Enter text to analyze and store in knowledge graph.")
    print("AI will extract entities and relationships.\n")
    
    text = input("Enter your text:\n> ").strip()
    
    if not text:
        print("Exiting")
        sys.exit(1)
    
    agent_id = input("\nEnter agent_id (optional):\n> ").strip() or None
    
    print(f"\n{'='*70}")
    print(f"Text to analyze:\n{text}")
    print(f"Agent ID: {agent_id or 'None'}")
    
    try:
        result = wrapper.process_text(text, agent_id)
        
        print(f"\n{'='*70}")
        print("RESULTS")
        print(f"{'='*70}\n")
        
        print(f"Status: {result['status']}")
        print(f"Entities created: {result['entity_count']}")
        print(f"Relationships created: {result['relationship_count']}")
        
        if result['entities_created']:
            print(f"\n{'='*70}")
            print("ENTITIES:")
            print(f"{'='*70}")
            for i, entity in enumerate(result['entities_created'], 1):
                print(f"\n  [{i}] {entity['name']}")
                print(f"      Labels: {', '.join(entity['labels'])}")
                print(f"      Properties:")
                for key, value in entity['props'].items():
                    print(f"        - {key}: {value}")
        
        if result['relationships_created']:
            print(f"\n{'='*70}")
            print("RELATIONSHIPS:")
            print(f"{'='*70}")
            for i, rel in enumerate(result['relationships_created'], 1):
                print(f"\n  [{i}] {rel['source']} --[{rel['relation']}]--> {rel['target']}")
                if rel['props']:
                    print(f"      Properties:")
                    for key, value in rel['props'].items():
                        print(f"        - {key}: {value}")
        
        if result.get('errors'):
            print(f"\n{'='*70}")
            print("ERRORS:")
            print(f"{'='*70}")
            for error in result['errors']:
                print(f"{error}")
        
        print(f"\n{'='*70}")
        print("Graph Updated")
        print(f"{'='*70}\n")
        
        continue_prompt = input("Continue? (y/n): ").strip().lower()
        if continue_prompt == 'y':
            print("\n" + "="*70 + "\n")
            import subprocess
            subprocess.call([sys.executable, __file__])
        
    except Exception as e:
        print(f"Error processing text: {e}")
        import traceback
        traceback.print_exc()