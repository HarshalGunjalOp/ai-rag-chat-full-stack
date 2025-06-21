from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[int] = None
    user_id: str = Field(..., min_length=1, max_length=100)


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    user_id: str
    content: Dict[str, Any]
    message_type: MessageType
    created_at: datetime


class ConversationCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    title: Optional[str] = Field(None, max_length=255)


class ConversationResponse(BaseModel):
    id: int
    user_id: str
    title: Optional[str]
    created_at: datetime
    message_count: Optional[int] = 0


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[int] = None
    user_id: str = Field(..., min_length=1, max_length=100)


class RAGResponse(BaseModel):
    answer: str
    sources: List[str] = []
    cached: bool = False
    response_time_ms: int


class ChatResponse(BaseModel):
    message: MessageResponse
    rag_response: Optional[RAGResponse] = None


class FileUploadResponse(BaseModel):
    filename: str
    status: str
    chunks_processed: int
    message: str
