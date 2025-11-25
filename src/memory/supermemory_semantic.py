from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import re
from supermemory import Supermemory
from ..config.settings import SUPERMEMORY_API_KEY
from .embeddings import openai_embed 


class SupermemorySemanticStore:
    """Supermemory integration using official SDK"""
    
    def __init__(self):
        self.api_key = SUPERMEMORY_API_KEY
        
        if not self.api_key:
            raise ValueError("API key not found")
        
        # Initialize Supermemory client
        self.client = Supermemory(api_key=self.api_key)
        print("Supermemory SDK initialized")
    
    def _flatten_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten metadata to only primitive types (string, number, boolean, array of strings)
        Supermemory only accepts these types in metadata
        """
        flattened = {}
        
        for key, value in metadata.items():
            if value is None:
                continue
            elif isinstance(value, (str, int, float, bool)):
                flattened[key] = value
            elif isinstance(value, list):
                # Convert list to array of strings
                flattened[key] = [str(item) for item in value]
            elif isinstance(value, dict):
                # Convert dict to JSON string
                if value:  # Only add non-empty dicts
                    flattened[key] = json.dumps(value)
            else:
                # Convert everything else to string
                flattened[key] = str(value)
        
        return flattened
    
    
    
    async def _extract_search_terms_with_llm(self, query: str) -> str:
        """
        Use LLM to dynamically extract KEY ENTITIES/KEYWORDS from queries
        Focus on nouns, names, and important terms only
        """
        try:
            from openai import AsyncOpenAI
            from ..config.settings import OPENAI_API_KEY
            
            
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            
            system_prompt = """You are a keyword extraction expert. Extract ONLY the key entities, names, and important nouns from queries.
    
    Rules:
    1. Extract names, entities, organizations, products, concepts
    2. Remove all verbs, articles, prepositions, question words
    3. Return ONLY the keywords separated by spaces
    4. Keep proper nouns as-is (capitalization matters)
    5. If multiple keywords, return all of them
    
    Examples:
    - "tell me about elon musk" -> "elon musk"
    - "what does spacelink do" -> "spacelink"
    - "rajamouli directed rrr" -> "rajamouli rrr"
    - "who owns tesla cars?" -> "tesla cars"
    - "give me information about machine learning algorithms" -> "machine learning algorithms"
    - "what is the capital of france" -> "capital france"
    - "how does photosynthesis work" -> "photosynthesis"
    - "elon musk" -> "elon musk"
    
    Return ONLY the keywords, nothing else. No explanation."""
    
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,
                max_tokens=30
            )
            
            extracted = response.choices[0].message.content.strip()
            print(f"LLM keyword extraction: '{query}' -> '{extracted}'")
            return extracted
            
        except Exception as e:
            print(f"Error using LLM for keyword extraction: {e}")
            
    
  
    
    
    async def _rerank_with_original_query(
    self,
    results: List[Dict[str, Any]],
    original_query: str
) -> List[Dict[str, Any]]:
        
        """Re-rank results using vector similarity with original query"""
        try:
            query_embedding = openai_embed(original_query)
            
            reranked_results = []
            for result in results:
                content = result.get("content", "")
                if not content:
                    continue
                
                content_embedding = openai_embed(content)
                
                similarity = self._cosine_similarity(query_embedding, content_embedding)
                
                result["similarity"] = similarity
                result["reranked"] = True
                reranked_results.append(result)
            
            reranked_results.sort(key=lambda x: x["similarity"], reverse=True)
            
            print(f"Re-ranked {len(reranked_results)} results using original query")
            return reranked_results
            
        except Exception as e:
            print(f"Error re-ranking results: {e}")
            return results

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def add(
        self,
        agent_id: str,
        content: str,
        message_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        spaces: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add memory to Supermemory using SDK with agent_id as container_tag
        
        The container_tag groups memories together and enables automatic memory graph creation
        """
        try:
            # Prepare base metadata
            base_metadata = {
                "agent_id": agent_id,
                "message_id": message_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add additional metadata if provided
            if metadata:
                # Flatten nested structures
                extra_metadata = self._flatten_metadata(metadata)
                base_metadata.update(extra_metadata)
            
            print(f"Sending to Supermemory - Content: {content[:50]}...")
            print(f"Metadata: {base_metadata}")
            print(f"container_tag: {agent_id}")
            
            # Add memory with container_tag set to agent_id for memory graph grouping
            response = self.client.memories.add(
                content=content,
                container_tag=agent_id,
                metadata=base_metadata
            )
            
            print(f"Memory added successfully: {response}")
            
            # Handle response format
            if hasattr(response, '__dict__'):
                result = response.__dict__
            elif isinstance(response, dict):
                result = response
            else:
                result = {"id": str(response), "status": "success"}
            
            # Add our tracking info
            result["agent_id"] = agent_id
            result["message_id"] = message_id
            result["container_tag"] = agent_id
            
            return result
            
        except Exception as e:
            print(f"Error adding memory to Supermemory: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def search(
    self,
    agent_id: str,
    query: str,
    limit: int = 10,
    spaces: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
        """Search with LLM preprocessing and re-ranking"""
        try:
            processed_query = await self._extract_search_terms_with_llm(query)
            print(f"Original: '{query}' -> Processed: '{processed_query}'")
            
            response = self.client.search.memories(
                q=processed_query,
                container_tag=agent_id,
                limit=limit * 2,  # Fetch more for re-ranking
                rerank=True,
                rewrite_query=False
            )
            
            if hasattr(response, 'results'):
                results_list = response.results
            else:
                results_dict = response.__dict__ if hasattr(response, '__dict__') else {}
                results_list = results_dict.get('results', [])
            
            formatted_results = []
            for result in results_list:
                if hasattr(result, '__dict__'):
                    result_dict = result.__dict__
                elif isinstance(result, dict):
                    result_dict = result
                else:
                    continue
                
                formatted_result = {
                    "id": result_dict.get("id"),
                    "content": result_dict.get("memory") or result_dict.get("content"),
                    "metadata": result_dict.get("metadata"),
                    "similarity": result_dict.get("similarity"),
                    "updated_at": result_dict.get("updatedAt") or result_dict.get("updated_at"),
                    "context": result_dict.get("context"),
                    "version": result_dict.get("version"),
                    "root_memory_id": result_dict.get("rootMemoryId") or result_dict.get("root_memory_id"),
                    "original_query": query,
                    "processed_query": processed_query
                }
                
                formatted_results.append(formatted_result)
            
            reranked_results = await self._rerank_with_original_query(formatted_results, query)
            
            final_results = reranked_results[:limit]
            
            print(f"Returned {len(final_results)} re-ranked results")
            return final_results
            
        except Exception as e:
            print(f"Error searching Supermemory: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by ID"""
        try:
            memory = self.client.memories.get(memory_id)
            
            if hasattr(memory, '__dict__'):
                return memory.__dict__
            elif isinstance(memory, dict):
                return memory
            else:
                return {"id": memory_id, "data": str(memory)}
                
        except Exception as e:
            print(f"Error getting memory: {e}")
            return None
    

    
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID"""
        try:
            self.client.memories.delete(memory_id)
            return True
        except Exception as e:
            print(f"Error deleting memory: {e}")
            return False
    
    async def delete_by_message_id(self, agent_id: str, message_id: str) -> bool:
        """Delete memories by message_id"""
        try:
            memories = await self.search(agent_id, "", limit=1000)
            
            deleted = False
            for mem in memories:
                if mem.get("metadata", {}).get("message_id") == message_id:
                    memory_id = mem.get("id")
                    if memory_id:
                        result = await self.delete(memory_id)
                        if result:
                            deleted = True
            
            return deleted
        except Exception as e:
            print(f"Error deleting by message_id: {e}")
            return False
    
   