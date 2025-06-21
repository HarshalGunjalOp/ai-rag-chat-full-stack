import json
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

    async def get_rag_response(self, query_hash: str) -> Optional[str]:
        """Get cached RAG response (1 hour TTL as per plan)"""
        key = f"rag:{query_hash}"
        return await self.redis_client.get(key)

    async def cache_rag_response(self, query_hash: str, response: str):
        """Cache RAG response for 1 hour"""
        key = f"rag:{query_hash}"
        await self.redis_client.setex(key, settings.CACHE_TTL, response)


cache_service = CacheService()
