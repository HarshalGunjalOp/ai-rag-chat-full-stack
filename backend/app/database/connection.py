import logging
from typing import Optional

import asyncpg
from asyncpg import Pool

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.pool: Optional[Pool] = None

    async def connect(self):
        """Initialize the connection pool with proper error handling"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=5,
                max_size=settings.DB_POOL_SIZE,
                command_timeout=60,
                server_settings={
                    "jit": "off"  # Disable JIT for better connection stability
                },
            )

            # Test connection
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")

            await self.create_tables()
            logger.info("âœ… Database connected successfully")

        except Exception as e:
            logger.error(f"âŒ Database connection failed: {e}")
            raise

    async def create_tables(self):
        """Create tables with proper error handling"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        async with self.pool.acquire() as conn:
            # Create tables with proper constraints
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    title VARCHAR(255),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                    user_id VARCHAR(100) NOT NULL,
                    content JSONB NOT NULL,
                    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'assistant', 'system')),
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    content_type VARCHAR(100),
                    file_size INTEGER,
                    chunks_processed INTEGER DEFAULT 0,
                    status VARCHAR(50) DEFAULT 'processing',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                -- Performance indexes
                CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
                CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
                CREATE INDEX IF NOT EXISTS idx_messages_content_gin ON messages USING GIN(content);
                CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
                CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
            """
            )

    async def get_connection(self):
        """Safe connection acquisition"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        return self.pool.acquire()

    async def execute_query(self, query: str, *args):
        """Execute query with proper error handling"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)


db_manager = DatabaseManager()
