import asyncio
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import (APIRouter, BackgroundTasks, File, Form, HTTPException,
                     UploadFile)
from fastapi.responses import StreamingResponse

from app.database.connection import db_manager
from app.models.schemas import (ChatResponse, ConversationCreate,
                                ConversationResponse, FileUploadResponse,
                                MessageRequest, MessageResponse, MessageType,
                                RAGQueryRequest, RAGResponse)
from app.services.cache_service import cache_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(conversation: ConversationCreate):
    """Create new conversation"""
    try:
        async with await db_manager.get_connection() as conn:
            query = """
                INSERT INTO conversations (user_id, title) 
                VALUES ($1, $2) 
                RETURNING id, user_id, title, created_at
            """
            result = await conn.fetchrow(
                query, conversation.user_id, conversation.title
            )

            return ConversationResponse(
                id=result["id"],
                user_id=result["user_id"],
                title=result["title"],
                created_at=result["created_at"],
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create conversation: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(user_id: str, limit: int = 20):
    """List user conversations with message counts"""
    try:
        async with await db_manager.get_connection() as conn:
            query = """
                SELECT c.id, c.user_id, c.title, c.created_at,
                       COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.user_id = $1
                GROUP BY c.id, c.user_id, c.title, c.created_at
                ORDER BY c.created_at DESC
                LIMIT $2
            """
            results = await conn.fetch(query, user_id, limit)

            return [
                ConversationResponse(
                    id=row["id"],
                    user_id=row["user_id"],
                    title=row["title"],
                    created_at=row["created_at"],
                    message_count=row["message_count"],
                )
                for row in results
            ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch conversations: {str(e)}"
        )


@router.get(
    "/conversations/{conversation_id}/messages", response_model=List[MessageResponse]
)
async def get_conversation_messages(conversation_id: int, limit: int = 50):
    """Get conversation messages - Redis cache first (100ms target)"""
    start_time = time.time()

    try:
        # Check Redis cache first...
        cached_messages = await cache_service.get_recent_messages(
            str(conversation_id), limit
        )
        if cached_messages:
            print(f"Cache hit - {int((time.time() - start_time) * 1000)}ms")
            messages = []
            for msg_data in cached_messages:
                try:
                    # Add missing required fields
                    if "conversation_id" not in msg_data:
                        msg_data["conversation_id"] = conversation_id
                    if "user_id" not in msg_data:
                        # Get user_id from database for this conversation
                        async with await db_manager.get_connection() as conn:
                            user_result = await conn.fetchrow(
                                "SELECT user_id FROM messages WHERE conversation_id = $1 LIMIT 1",
                                conversation_id,
                            )
                            if user_result:
                                msg_data["user_id"] = user_result["user_id"]
                            else:
                                continue

                    # Fix datetime and content handling...
                    if isinstance(msg_data.get("created_at"), str):
                        dt_str = msg_data["created_at"]
                        if dt_str.endswith("Z"):
                            dt_str = dt_str.replace("Z", "+00:00")
                        elif not dt_str.endswith("+00:00") and "T" in dt_str:
                            dt_str = dt_str + "+00:00" if "+" not in dt_str else dt_str
                        msg_data["created_at"] = datetime.fromisoformat(dt_str)

                    if isinstance(msg_data.get("content"), str):
                        try:
                            msg_data["content"] = json.loads(msg_data["content"])
                        except json.JSONDecodeError:
                            msg_data["content"] = {"text": msg_data["content"]}
                    elif msg_data.get("content") is None:
                        msg_data["content"] = {"text": ""}
                    elif not isinstance(msg_data.get("content"), dict):
                        msg_data["content"] = {"text": str(msg_data["content"])}

                    if "text" not in msg_data["content"]:
                        if (
                            isinstance(msg_data["content"], dict)
                            and len(msg_data["content"]) > 0
                        ):
                            msg_data["content"]["text"] = str(
                                list(msg_data["content"].values())[0]
                            )
                        else:
                            msg_data["content"]["text"] = ""

                    messages.append(MessageResponse(**msg_data))
                except Exception as e:
                    print(f"Error processing cached message: {e}")
                    continue

            if messages:
                return messages

        # Fallback to database - FIX THE FIELD NAMES HERE
        async with await db_manager.get_connection() as conn:
            query = """
            SELECT id, conversation_id, user_id, content, message_type, created_at
            FROM messages 
            WHERE conversation_id = $1 
            ORDER BY created_at ASC 
            LIMIT $2
            """
            results = await conn.fetch(query, conversation_id, limit)

            messages = []
            for row in results:
                try:
                    content = row["content"]
                    if isinstance(content, str):
                        try:
                            content = json.loads(content)
                        except json.JSONDecodeError:
                            content = {"text": content}
                    elif content is None:
                        content = {"text": ""}
                    elif not isinstance(content, dict):
                        content = {"text": str(content)}

                    if "text" not in content:
                        if isinstance(content, dict) and len(content) > 0:
                            content["text"] = str(list(content.values())[0])
                        else:
                            content["text"] = ""

                    message = MessageResponse(
                        id=row["id"],
                        conversation_id=row["conversation_id"],
                        user_id=row["user_id"],
                        content=content,
                        message_type=MessageType(row["message_type"]),
                        created_at=row["created_at"],
                    )
                    messages.append(message)
                except Exception as e:
                    print(
                        f"Error processing DB message {row.get('id', 'unknown')}: {e}"
                    )
                    continue

            print(f"DB query - {int((time.time() - start_time) * 1000)}ms")
            return messages

    except Exception as e:
        print(f"Error in get_conversation_messages: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch messages: {str(e)}"
        )


@router.post("/messages/stream")
async def send_message_stream(request: MessageRequest):
    """Send message and stream the AI response"""
    try:
        # Validate request
        if not request.content.strip():
            raise HTTPException(
                status_code=400, detail="Message content cannot be empty"
            )

        # Create or get conversation
        conversation_id = await get_or_create_conversation(
            request.user_id, request.conversation_id
        )

        # Save user message
        user_message = await save_message(
            conversation_id=conversation_id,
            user_id=request.user_id,
            content={"text": request.content},
            message_type="user",
        )

        # Cache user message
        await cache_service.cache_message(
            str(conversation_id),
            {
                "id": user_message["id"],
                "content": user_message["content"],
                "message_type": user_message["message_type"],
                "created_at": user_message["created_at"].isoformat(),
            },
        )

        # Generate streaming response
        return StreamingResponse(
            generate_ai_response(request.content, conversation_id, request.user_id),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process message: {str(e)}"
        )


@router.post("/messages/rag/stream")
async def send_rag_message_stream(request: MessageRequest):
    """Send RAG message and stream the response with caching"""
    
    def generate_rag_stream():
        async def _generate():
            try:
                rag_start = time.time()
                
                # Generate consistent cache key
                cache_key = cache_service._generate_rag_cache_key(request.content, request.user_id)
                
                # Check cache first
                cached_rag = await cache_service.get_rag_response(cache_key)
                if cached_rag:
                    try:
                        rag_data = json.loads(cached_rag)
                        content = rag_data.get("content", "")
                        
                        if content and content.strip():  # Only use cache if content exists
                            # Stream cached response
                            words = content.split(" ")
                            for word in words:
                                if word.strip():
                                    yield f"data: {json.dumps({'type': 'chunk', 'content': word + ' '})}\n\n"
                                    await asyncio.sleep(0.01)
                            
                            # Send completion with cached flag
                            rag_response = RAGResponse(
                                answer=content,
                                sources=rag_data.get("sources", []),
                                cached=True,
                                response_time_ms=int((time.time() - rag_start) * 1000)
                            )
                            
                            yield f"data: {json.dumps({'type': 'complete', 'rag_response': rag_response.dict()})}\n\n"
                            yield "data: [DONE]\n\n"
                            return
                        else:
                            # Invalid cache, delete it
                            await cache_service.delete_cache_key(cache_key)
                            
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Cache parsing error: {e}")
                        await cache_service.delete_cache_key(cache_key)

                # Generate new response
                full_answer = ""
                sources = []
                
                async for chunk in rag_service.query(request.content, user_id=request.user_id):
                    if chunk.get("type") == "chunk":
                        content = chunk.get("content", "")
                        full_answer += content
                        yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
                    elif chunk.get("type") == "complete":
                        sources = chunk.get("sources", [])
                        break
                    elif chunk.get("type") == "thinking":
                        yield f"data: {json.dumps({'type': 'thinking', 'message': chunk.get('message', '')})}\n\n"
                    elif chunk.get("type") == "error":
                        yield f"data: {json.dumps({'type': 'error', 'message': chunk.get('message', '')})}\n\n"
                        return
                
                # Cache the response if it's valid
                if full_answer.strip():
                    cache_data = {
                        "content": full_answer,
                        "sources": sources,
                        "cached": False
                    }
                    await cache_service.cache_rag_response(cache_key, json.dumps(cache_data))
                
                # Send final response
                rag_response = RAGResponse(
                    answer=full_answer,
                    sources=sources,
                    cached=False,
                    response_time_ms=int((time.time() - rag_start) * 1000)
                )
                
                yield f"data: {json.dumps({'type': 'complete', 'rag_response': rag_response.dict()})}\n\n"
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                yield "data: [DONE]\n\n"

        return _generate()
    
    return StreamingResponse(
        generate_rag_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/stream",
        }
    )



async def generate_ai_response(query: str, conversation_id: int, user_id: str):
    """Generate streaming AI response with improved caching"""
    try:
        yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id})}\n\n"
        
        # Generate consistent cache key
        cache_key = cache_service._generate_rag_cache_key(query, user_id)
        
        # Check cache first
        cached_response = await cache_service.get_rag_response(cache_key)
        if cached_response:
            try:
                response_data = json.loads(cached_response)
                content = response_data.get("content", "")
                
                if content and content.strip():
                    # Stream cached content
                    for word in content.split(" "):
                        if word.strip():
                            yield f"data: {word + ' '}\n\n"
                            await asyncio.sleep(0.01)
                    return
                else:
                    # Invalid cache, delete it
                    await cache_service.delete_cache_key(cache_key)
            except (json.JSONDecodeError, KeyError):
                await cache_service.delete_cache_key(cache_key)

        # Generate new response
        full_response = ""
        sources = []

        async for chunk in rag_service.query(query, user_id=user_id):
            if chunk.get("type") == "chunk":
                content = chunk.get("content", "")
                full_response += content
                yield f"data: {content}\n\n"
            elif chunk.get("type") == "complete":
                sources = chunk.get("sources", [])
                break
            elif chunk.get("type") == "error":
                yield f"data: ERROR: {chunk.get('message', '')}\n\n"
                return

        # Cache the response if valid
        if full_response.strip():
            cache_data = {
                "content": full_response,
                "sources": sources,
                "cached": False
            }
            await cache_service.cache_rag_response(cache_key, json.dumps(cache_data))

    except Exception as e:
        yield f"data: ERROR: {str(e)}\n\n"


async def get_or_create_conversation(
    user_id: str, conversation_id: Optional[int] = None
) -> int:
    """Get existing conversation or create new one"""
    if conversation_id:
        # Verify conversation exists and belongs to user
        async with await db_manager.get_connection() as conn:
            result = await conn.fetchrow(
                "SELECT id FROM conversations WHERE id = $1 AND user_id = $2",
                conversation_id,
                user_id,
            )
            if result:
                return conversation_id

    # Create new conversation
    async with await db_manager.get_connection() as conn:
        result = await conn.fetchrow(
            "INSERT INTO conversations (user_id, title) VALUES ($1, $2) RETURNING id",
            user_id,
            "New Conversation",
        )
        return result["id"]


async def save_message(
    conversation_id: int, user_id: str, content: dict, message_type: str
) -> dict:
    """Save message to database"""
    async with await db_manager.get_connection() as conn:
        result = await conn.fetchrow(
            """INSERT INTO messages (conversation_id, user_id, content, message_type) 
               VALUES ($1, $2, $3, $4) 
               RETURNING id, conversation_id, user_id, content, message_type, created_at""",
            conversation_id,
            user_id,
            json.dumps(content),
            message_type,
        )
        return dict(result)


async def stream_rag_response(query: str):
    """Stream RAG response using OpenAI streaming API"""
    try:
        # Get relevant documents first
        rag_result = await rag_service.query(query, topk=5, relevance_threshold=0.3)

        context = "\n".join([doc for doc in rag_result.get("sources", [])])

        # Create streaming OpenAI request
        from openai import AsyncOpenAI

        client = AsyncOpenAI()

        messages = [
            {
                "role": "system",
                "content": f"This is the context provided by the user. If you find the answer to the query in the context, then answer based on that, else use your own knowlege to answer the question: {context}",
            },
            {"role": "user", "content": query},
        ]

        stream = await client.chat.completions.create(
            model="o3-mini",
            messages=messages,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        yield f"\n\nError: {str(e)}"



@router.post("/upload", response_model=FileUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(...),
):
    """Upload single document for RAG (supports PDF, TXT, MD, Images)"""
    try:
        # Enhanced file type validation
        allowed_extensions = {
            ".pdf",
            ".txt",
            ".md",
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".gif",
        }
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
            )

        # Validate file size (e.g., 50MB limit)
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(
                status_code=400, detail="File too large. Maximum size: 50MB"
            )

        # FIX: Process in background with user_id
        background_tasks.add_task(
            rag_service.process_multimodal_document,
            file.filename,
            content,
            user_id,  # Added user_id parameter
        )

        return FileUploadResponse(
            filename=file.filename,
            status="processing",
            chunks_processed=0,
            message=f"Document '{file.filename}' uploaded successfully, processing in background",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload document: {str(e)}"
        )


@router.post("/upload/multiple", response_model=List[FileUploadResponse])
async def upload_multiple_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    user_id: str = Form(...),
):
    """Upload multiple documents for RAG context (batch processing)"""
    try:
        if len(files) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Maximum 10 files per batch")

        allowed_extensions = {
            ".pdf",
            ".txt",
            ".md",
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".gif",
        }
        responses = []

        for file in files:
            file_ext = Path(file.filename).suffix.lower()

            if file_ext not in allowed_extensions:
                responses.append(
                    FileUploadResponse(
                        filename=file.filename,
                        status="error",
                        chunks_processed=0,
                        message=f"Unsupported file type: {file_ext}",
                    )
                )
                continue

            # Read and validate file
            content = await file.read()
            if len(content) > 50 * 1024 * 1024:  # 50MB per file
                responses.append(
                    FileUploadResponse(
                        filename=file.filename,
                        status="error",
                        chunks_processed=0,
                        message="File too large. Maximum size: 50MB",
                    )
                )
                continue

            # Process in background
            background_tasks.add_task(
                rag_service.process_multimodal_document, file.filename, content, user_id
            )

            responses.append(
                FileUploadResponse(
                    filename=file.filename,
                    status="processing",
                    chunks_processed=0,
                    message="Uploaded successfully, processing in background",
                )
            )

        return responses

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload documents: {str(e)}"
        )



@router.post("/rag/query", response_model=RAGResponse)
async def query_rag(rag_query: RAGQueryRequest):
    """Direct multimodal RAG query endpoint (1.5s target, 500ms if cached)"""
    start_time = time.time()

    try:
        # Check if user has documents
        if not await rag_service.has_documents(rag_query.user_id):
            raise HTTPException(status_code=400, detail="No documents uploaded for RAG")

        # Enhanced cache key with user context
        cache_key_content = f"{rag_query.query}:{rag_query.user_id}"
        if rag_query.conversation_id:
            cache_key_content += f":{rag_query.conversation_id}"

        query_hash = hashlib.md5(cache_key_content.encode()).hexdigest()
        cached_response = await cache_service.get_rag_response(query_hash)

        if cached_response:
            return RAGResponse(
                answer=cached_response,
                sources=[],
                cached=True,
                response_time_ms=int((time.time() - start_time) * 1000),
            )

        # 🔥 FIX: Consume the async generator properly
        full_answer = ""
        sources = []
        
        async for chunk in rag_service.query(rag_query.query, user_id=rag_query.user_id):
            if chunk.get("type") == "chunk":
                full_answer += chunk.get("content", "")
            elif chunk.get("type") == "complete":
                sources = chunk.get("sources", [])
                break
            elif chunk.get("type") == "error":
                raise HTTPException(status_code=500, detail=chunk.get("message", "Unknown error"))

        # Cache the response
        await cache_service.cache_rag_response(query_hash, full_answer)

        response_time = int((time.time() - start_time) * 1000)


        return RAGResponse(
            answer=full_answer,
            sources=sources,
            cached=False,
            response_time_ms=response_time,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")



@router.get("/documents/status")
async def get_document_status(user_id: str):
    """Get current document processing status for a specific user"""
    try:
        has_docs = await rag_service.has_documents(user_id)
        total_chunks = len(rag_service.user_documents[user_id]) if has_docs else 0

        user_documents = []
        if has_docs:
            # Get unique sources from actual documents
            user_docs = rag_service.user_documents[user_id]
            sources = list(
                set(doc.metadata.get("source", "unknown") for doc in user_docs)
            )

            for source in sources:
                user_documents.append(
                    {
                        "filename": source,
                        "type": "processed",  # or derive from document metadata
                        "status": "processed",
                        "user_id": user_id,
                    }
                )

        return {
            "user_id": user_id,
            "has_documents": len(user_documents) > 0,
            "document_count": len(user_documents),
            "total_chunks": total_chunks,
            "documents": user_documents,
            "supported_formats": [
                ".pdf",
                ".txt",
                ".md",
                ".jpg",
                ".jpeg",
                ".png",
                ".bmp",
                ".gif",
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get document status: {str(e)}"
        )


@router.delete("/documents/clear")
async def clear_all_documents(user_id: str):
    """Clear all documents from RAG context (admin function)"""
    try:
        # Reset the advanced RAG service
        rag_service.user_documents[user_id] = []
        rag_service.document_metadata = {}
        rag_service.faiss_index = None
        rag_service.bm25_index = None

        # Clear related caches
        # Note: In production, you might want to clear only user-specific documents
        await cache_service.redis_client.flushdb()  # Clear all cache (use carefully)

        return {
            "message": "All documents cleared successfully",
            "user_id": user_id,
            "cleared_at": time.time(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clear documents: {str(e)}"
        )
