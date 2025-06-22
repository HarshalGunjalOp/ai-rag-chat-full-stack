import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import db_manager
from app.routes.chat import router as chat_router
from app.services.cache_service import cache_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Initialize services
        await db_manager.connect()
        await cache_service.connect()
        print("âœ… All services initialized")
        yield
    except Exception as e:
        print(f"âŒ Startup failed: {e}")
        raise
    finally:
        # Cleanup
        if db_manager.pool:
            await db_manager.pool.close()


app = FastAPI(title="RAG Chat API", version="1.0.0", lifespan=lifespan)

# Fixed CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "https://ai-rag-chat-full-stack-1.onrender.com",
        "https://ai-rag-chat-full-stack.onrender.com"
    ],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
