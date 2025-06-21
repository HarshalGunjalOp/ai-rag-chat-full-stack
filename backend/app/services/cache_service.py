import json
import hashlib
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from app.config import settings


class CacheService:
    def __init__(self):
        self.redis_client = None

    async def connect(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)

    async def get_recent_messages(
        self, conversation_id: str, limit: int = 50
    ) -> Optional[List[Dict]]:
        """Get recent 50 messages per conversation as per plan"""
        key = f"messages:{conversation_id}"
        messages = await self.redis_client.lrange(key, -limit, -1)
        return [json.loads(msg) for msg in messages] if messages else None

    async def cache_message(self, conversation_id: str, message: Dict[str, Any]):
        """Cache message with Redis list"""
        key = f"messages:{conversation_id}"
        await self.redis_client.lpush(key, json.dumps(message))
        await self.redis_client.expire(key, settings.CACHE_TTL)

    def _generate_rag_cache_key(self, query: str, user_id: str) -> str:
        """Generate consistent cache key for RAG responses"""
        content_for_cache = f"{query}:{user_id}"
        return f"rag:{hashlib.md5(content_for_cache.encode()).hexdigest()}"

    async def get_rag_response(self, cache_key: str) -> Optional[str]:
        """Get cached RAG response with error handling"""
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                print(f"Cache hit - key: {cache_key}, length: {len(cached)}")  # Debug
                return cached
            else:
                print(f"Cache miss - key: {cache_key}")  # Debug
                return None
        except Exception as e:
            print(f"Cache retrieval error: {e}")
            return None

    async def cache_rag_response(self, cache_key: str, response: str):
        """Cache RAG response with validation"""
        try:
            if not response or not response.strip():
                print(f"WARNING: Attempted to cache empty response for key: {cache_key}")
                return
            
            # Validate JSON structure
            try:
                parsed = json.loads(response)
                content = parsed.get("content", "")
                if not content or not content.strip():
                    print(f"WARNING: Response content is empty for key: {cache_key}")
                    return
            except json.JSONDecodeError:
                print(f"WARNING: Invalid JSON format for caching: {cache_key}")
                return
            
            await self.redis_client.setex(cache_key, settings.CACHE_TTL, response)
            print(f"Successfully cached response - key: {cache_key}, length: {len(response)}")  # Debug
            
        except Exception as e:
            print(f"Cache storage error for key {cache_key}: {e}")

    async def delete_cache_key(self, cache_key: str):
        """Delete invalid cache entry"""
        try:
            await self.redis_client.delete(cache_key)
            print(f"Deleted invalid cache key: {cache_key}")
        except Exception as e:
            print(f"Error deleting cache key {cache_key}: {e}")


cache_service = CacheService()

