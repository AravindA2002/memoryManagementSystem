from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import re
from supermemory import Supermemory
from ..config.settings import SUPERMEMORY_API_KEY


class SupermemorySemanticStore:
    """Supermemory integration using official SDK"""
    
    def __init__(self):
        self.api_key = SUPERMEMORY_API_KEY
        
        if not self.api_key:
            raise ValueError("SUPERMEMORY_API_KEY not found in settings. Please set it in .env file")
        
        # Initialize Supermemory client
        self.client = Supermemory(api_key=self.api_key)
        print("Supermemory SDK initialized successfully")
    
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
    
    # COMMENTED OUT - LLM-based keyword extraction (can be re-enabled if needed)
    '''
    async def _extract_search_terms_with_llm(self, query: str) -> str:
        """
        Use LLM to dynamically extract KEY ENTITIES/KEYWORDS from queries
        Focus on nouns, names, and important terms only
        """
        try:
            from openai import AsyncOpenAI
            from ..config.settings import OPENAI_API_KEY
            
            if not OPENAI_API_KEY:
                print("OpenAI API key not found, falling back to simple extraction")
                return self._extract_key_terms_simple(query)
            
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
            return self._extract_key_terms_simple(query)
    
    #COMMENTED OUT - Simple keyword extraction fallback
    def _extract_key_terms_simple(self, query: str) -> str:
        """
        Simple keyword extraction without LLM
        Removes common stop words and extracts key terms
        """
        import re
        
        query_lower = query.lower().strip()
        
        # Common stop words to remove
        stop_words = {
            'tell', 'me', 'about', 'what', 'is', 'are', 'the', 'a', 'an',
            'who', 'where', 'when', 'why', 'how', 'does', 'do', 'did',
            'can', 'could', 'would', 'should', 'will', 'shall',
            'give', 'show', 'find', 'search', 'get', 'fetch',
            'information', 'details', 'info', 'all', 'any',
            'please', 'you', 'your', 'i', 'my', 'we', 'our'
        }
        
        # Remove question marks and punctuation
        query_clean = re.sub(r'[?!.,;:]', '', query_lower)
        
        # Split into words
        words = query_clean.split()
        
        # Filter out stop words and very short words
        keywords = [w for w in words if w not in stop_words and len(w) > 1]
        
        # If we removed everything, return original
        if not keywords:
            return query.strip()
        
        result = ' '.join(keywords)
        print(f"Simple keyword extraction: '{query}' -> '{result}'")
        return result'''
    
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
        """
        Search memories in Supermemory filtered by container_tag (agent_id)
        
        Uses Supermemory's built-in rewrite_query for handling conversational queries
        
        Args:
            agent_id: Agent identifier for filtering
            query: Search query (can be conversational)
            limit: Maximum number of results
            spaces: Optional space filters
        
        Returns:
            List of memories with similarity scores, context, and metadata
        """
        try:
            print(f"Searching Supermemory with rewrite_query - Query: '{query}', Agent ID: {agent_id}, Limit: {limit}")
            
            # Use Supermemory's built-in rewrite_query for conversational queries
            response = self.client.search.memories(
                q=query,
                container_tag=agent_id,
                limit=limit,
                
                rerank=True,  # Enable reranking for better results
                rewrite_query=True  # Let Supermemory rewrite conversational queries
            )
            
            print(f"Search response type: {type(response)}")
            
            # Access the results attribute directly
            if hasattr(response, 'results'):
                results_list = response.results
                print(f"Found {len(results_list)} results")
            else:
                results_dict = response.__dict__ if hasattr(response, '__dict__') else {}
                results_list = results_dict.get('results', [])
                print(f"Found {len(results_list)} results via dict access")
            
            # Convert results to proper dict format
            formatted_results = []
            for result in results_list:
                if hasattr(result, '__dict__'):
                    result_dict = result.__dict__
                elif isinstance(result, dict):
                    result_dict = result
                else:
                    continue
                
                # Format the result with all available fields
                formatted_result = {
                    "id": result_dict.get("id"),
                    "content": result_dict.get("memory") or result_dict.get("content"),
                    "metadata": result_dict.get("metadata"),
                    "similarity": result_dict.get("similarity"),
                    "updated_at": result_dict.get("updatedAt") or result_dict.get("updated_at"),
                    "context": result_dict.get("context"),
                    "version": result_dict.get("version"),
                    "root_memory_id": result_dict.get("rootMemoryId") or result_dict.get("root_memory_id"),
                    "original_query": query
                }
                
                formatted_results.append(formatted_result)
            
            print(f"Returning {len(formatted_results)} formatted results")
            return formatted_results
            
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
    
    async def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update an existing memory"""
        try:
            update_params = {"id": memory_id}
            
            if content is not None:
                update_params["content"] = content
            
            if metadata is not None:
                update_params["metadata"] = self._flatten_metadata(metadata)
            
            response = self.client.memories.update(**update_params)
            
            if hasattr(response, '__dict__'):
                return response.__dict__
            elif isinstance(response, dict):
                return response
            else:
                return {"status": "updated", "id": memory_id}
                
        except Exception as e:
            print(f"Error updating memory: {e}")
            raise
    
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
    
    async def list_all(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """List all memories for an agent using container_tag"""
        try:
            try:
                results = self.client.memories.list(limit=limit, container_tag=agent_id)
            except TypeError:
                results = self.client.memories.list(limit=limit)
            
            if hasattr(results, '__dict__'):
                results_data = results.__dict__
            elif isinstance(results, dict):
                results_data = results
            else:
                results_data = {"memories": []}
            
            if isinstance(results_data, dict):
                results_list = results_data.get("memories", []) or results_data.get("data", []) or []
            elif isinstance(results_data, list):
                results_list = results_data
            else:
                results_list = []
            
            filtered = []
            for result in results_list:
                if hasattr(result, '__dict__'):
                    result = result.__dict__
                
                result_metadata = result.get("metadata", {}) if isinstance(result, dict) else {}
                if result_metadata.get("agent_id") == agent_id:
                    filtered.append(result)
            
            return filtered
            
        except Exception as e:
            print(f"Error listing memories: {e}")
            return []
    
    async def list_spaces(self) -> List[Dict[str, Any]]:
        """List all available spaces"""
        return []
    
    async def create_space(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new space"""
        raise NotImplementedError("Space creation not implemented yet")
    
    async def close(self):
        """Close the client"""
        if hasattr(self.client, 'close') and callable(self.client.close):
            self.client.close()