# File: app/services/rag_service.py
import asyncio
import base64
import hashlib
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import faiss
import numpy as np
import PyPDF2
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import (MarkdownHeaderTextSplitter,
                                      RecursiveCharacterTextSplitter)
from openai import AsyncOpenAI
from rank_bm25 import BM25Okapi

from app.config import settings
from app.services.cache_service import cache_service


class RAGService:
    def __init__(self):
        self.embeddings = None
        self.text_llm = None
        self.vision_llm = None

        # User-specific data structures
        self.user_faiss_indexes = {}  # user_id -> faiss_index
        self.user_bm25_indexes = {}  # user_id -> bm25_index
        self.user_documents = {}  # user_id -> List[Document]
        self.user_metadata = {}  # user_id -> metadata
        self.user_image_cache = {}  # user_id -> {filename: base64_image}

        # Configuration for hybrid behavior
        self.hybrid_config = {
            "semantic_weight": 0.7,
            "min_relevance_threshold": 0.3,
            "fallback_to_general": True,
            "max_context_length": 4000,
            "default_topk": 5,
            "enable_query_expansion": True,
            "cache_responses": True,
        }

        # Text splitters for different document types
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )

        self.md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]
        )

        self.initialize()

    def initialize(self):
        """Initialize OpenAI components"""
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Text processing LLM
        self.text_llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model="o3-mini",
            max_completion_tokens=2000,
            timeout=30,
            max_retries=2,
        )

        # Vision LLM for image processing
        self.vision_llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model="gpt-4o",
            max_completion_tokens=1000,
            timeout=30,
            max_retries=2,
        )

    def _ensure_user_data(self, user_id: str):
        """Ensure user-specific data structures exist"""
        if user_id not in self.user_documents:
            self.user_documents[user_id] = []
        if user_id not in self.user_metadata:
            self.user_metadata[user_id] = {}
        if user_id not in self.user_image_cache:
            self.user_image_cache[user_id] = {}

    async def has_documents(self, user_id: str) -> bool:
        """Check if user has any documents loaded"""
        return user_id in self.user_documents and len(self.user_documents[user_id]) > 0

    async def query(
        self, query: str, user_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream the RAG response with user-specific context"""
        try:
            # Validate user_id
            if not user_id or not user_id.strip():
                yield {"type": "error", "message": "user_id is required"}
                return

            self._ensure_user_data(user_id)

            # Check user-specific cache first
            cache_key = f"rag:{user_id}:{hash(query)}"
            cached_response = await cache_service.get_rag_response(cache_key)

            if cached_response:
                response_data = json.loads(cached_response)
                for chunk in response_data.get("content", "").split():
                    yield {"type": "chunk", "content": chunk + " "}
                    await asyncio.sleep(0.01)
                yield {"type": "complete", "sources": response_data.get("sources", [])}
                return

            yield {"type": "thinking", "message": "Searching user documents..."}

            # Check if user has documents
            if await self.has_documents(user_id):
                # Search user-specific documents
                relevant_docs = await self.hybrid_search(
                    query, user_id, self.hybrid_config["default_topk"]
                )

                if (
                    relevant_docs
                    and self.get_max_relevance_score(relevant_docs)
                    > self.hybrid_config["min_relevance_threshold"]
                ):
                    async for chunk in self.generate_context_answer_stream(
                        query, relevant_docs, user_id
                    ):
                        if chunk["type"] == "complete":
                            # Cache the response
                            full_response = (
                                ""  # You'd need to collect this during streaming
                            )
                            cache_data = {
                                "content": full_response,
                                "sources": chunk.get("sources", []),
                                "cached": True,
                            }
                            await cache_service.cache_rag_response(
                                cache_key, json.dumps(cache_data)
                            )
                        yield chunk
                    return

            # Fallback to general knowledge
            yield {"type": "thinking", "message": "Generating general response..."}
            async for chunk in self.generate_general_knowledge_answer_stream(query):
                yield chunk

        except Exception as e:
            yield {"type": "error", "message": str(e)}

    async def generate_general_knowledge_answer_stream(self, query: str):
        """Generate streaming answer using general knowledge"""
        try:
            yield {"type": "thinking", "message": "Generating response..."}

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on provided context if available, otherwise provide general knowledge responses.",
                },
                {"role": "user", "content": f"Question: {query}"},
            ]

            stream = await self.client.chat.completions.create(
                model="o3-mini",
                messages=messages,
                stream=True,
                max_completion_tokens=2000,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {"type": "chunk", "content": chunk.choices[0].delta.content}

            yield {
                "type": "complete",
                "sources": [],
                "search_method": "general_knowledge",
            }

        except Exception as e:
            yield {"type": "error", "message": str(e)}

    async def generate_context_answer_stream(
        self, query: str, relevant_docs: List[Document], user_id: str
    ):
        """Generate streaming answer using user's document context"""
        try:
            yield {"type": "thinking", "message": "Processing your documents..."}

            context_parts = []
            sources = []

            for doc in relevant_docs:
                doc_type = doc.metadata.get("type", "text")
                source = doc.metadata.get("source", "unknown")

                if doc_type == "image":
                    context_parts.append(f"[Image from {source}]: {doc.page_content}")
                else:
                    context_parts.append(f"[From {source}]: {doc.page_content}")

                if source not in sources:
                    sources.append(source)

            context = "\n\n".join(context_parts)

            if len(context) > self.hybrid_config["max_context_length"]:
                context = context[: self.hybrid_config["max_context_length"]] + "..."

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on the user's uploaded documents. Be precise and cite information appropriately.",
                },
                {
                    "role": "user",
                    "content": f"Context from user's documents:\n{context}\n\nQuestion: {query}\n\nAnswer based on the context above.",
                },
            ]

            stream = await self.client.chat.completions.create(
                model="o3-mini",
                messages=messages,
                stream=True,
                max_completion_tokens=2000,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {"type": "chunk", "content": chunk.choices[0].delta.content}

            yield {
                "type": "complete",
                "sources": sources[:3],
                "search_method": "user_documents",
            }

        except Exception as e:
            yield {"type": "error", "message": str(e)}

    async def hybrid_search(
        self, query: str, user_id: str, topk: int
    ) -> List[Document]:
        """User-specific hybrid search combining semantic + keyword"""
        if user_id not in self.user_documents or not self.user_documents[user_id]:
            return []

        # Expand query for better results
        if self.hybrid_config["enable_query_expansion"]:
            expanded_query = await self.expand_query(query)
            queries = [query, expanded_query] if expanded_query != query else [query]
        else:
            queries = [query]

        all_results = []
        for q in queries:
            semantic_results = await self.semantic_search(q, user_id, topk)
            keyword_results = await self.keyword_search(q, user_id, topk)
            combined = self.combine_results(semantic_results, keyword_results)
            all_results.extend(combined)

        unique_results = self.deduplicate_results(all_results)
        return unique_results[:topk]

    async def semantic_search(
        self, query: str, user_id: str, topk: int
    ) -> List[Document]:
        """User-specific semantic search using FAISS"""
        if user_id not in self.user_faiss_indexes or user_id not in self.user_documents:
            return []

        query_embedding = await self.embeddings.aembed_query(query)
        query_vector = np.array([query_embedding]).astype("float32")
        faiss.normalize_L2(query_vector)

        user_docs = self.user_documents[user_id]
        scores, indices = self.user_faiss_indexes[user_id].search(
            query_vector, min(topk, len(user_docs))
        )

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(user_docs):
                doc = user_docs[idx].copy()
                doc.metadata["semantic_score"] = float(score)
                results.append(doc)

        return results

    async def keyword_search(
        self, query: str, user_id: str, topk: int
    ) -> List[Document]:
        """User-specific keyword search using BM25"""
        if user_id not in self.user_bm25_indexes or user_id not in self.user_documents:
            return []

        query_tokens = query.lower().split()
        scores = self.user_bm25_indexes[user_id].get_scores(query_tokens)
        top_indices = np.argsort(scores)[::-1][:topk]

        results = []
        user_docs = self.user_documents[user_id]
        for idx in top_indices:
            if idx < len(user_docs) and scores[idx] > 0:
                doc = user_docs[idx].copy()
                doc.metadata["keyword_score"] = float(scores[idx])
                results.append(doc)

        return results

    def combine_results(
        self, semantic_results: List[Document], keyword_results: List[Document]
    ) -> List[Document]:
        """Combine semantic and keyword results with weighting"""
        alpha = self.hybrid_config["semantic_weight"]
        score_map = {}

        for doc in semantic_results:
            chunk_id = doc.metadata.get("chunk_id", str(hash(doc.page_content)))
            score_map[chunk_id] = {
                "semantic": doc.metadata.get("semantic_score", 0),
                "keyword": 0,
                "doc": doc,
            }

        for doc in keyword_results:
            chunk_id = doc.metadata.get("chunk_id", str(hash(doc.page_content)))
            if chunk_id not in score_map:
                score_map[chunk_id] = {"semantic": 0, "keyword": 0, "doc": doc}
            score_map[chunk_id]["keyword"] = doc.metadata.get("keyword_score", 0)

        combined_results = []
        max_keyword_score = (
            max([scores["keyword"] for scores in score_map.values()]) or 1.0
        )

        for chunk_id, scores in score_map.items():
            keyword_score = (
                scores["keyword"] / max_keyword_score if max_keyword_score > 0 else 0
            )
            combined_score = alpha * scores["semantic"] + (1 - alpha) * keyword_score
            doc = scores["doc"]
            doc.metadata["combined_score"] = combined_score
            combined_results.append(doc)

        combined_results.sort(
            key=lambda x: x.metadata.get("combined_score", 0), reverse=True
        )
        return combined_results

    async def expand_query(self, query: str) -> str:
        """Expand query with related terms"""
        try:
            expansion_prompt = f"""Expand this search query with 2-3 related terms or synonyms that would help find relevant information:
Original query: {query}
Return the expanded query (original + related terms):"""

            messages = [HumanMessage(content=expansion_prompt)]
            response = await self.text_llm.ainvoke(messages)
            expanded = response.content.strip()

            return expanded if len(expanded) > len(query) else query
        except Exception:
            return query

    def deduplicate_results(self, results: List[Document]) -> List[Document]:
        """Remove duplicate documents based on chunk_id or content hash"""
        seen_ids = set()
        unique_results = []

        for doc in results:
            chunk_id = doc.metadata.get("chunk_id") or str(hash(doc.page_content))
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_results.append(doc)

        unique_results.sort(
            key=lambda x: x.metadata.get("combined_score", 0), reverse=True
        )
        return unique_results

    def get_max_relevance_score(self, results: List[Document]) -> float:
        """Get the maximum relevance score from search results"""
        if not results:
            return 0.0

        max_score = 0.0
        for doc in results:
            semantic_score = doc.metadata.get("semantic_score", 0.0)
            keyword_score = doc.metadata.get("keyword_score", 0.0)
            combined_score = doc.metadata.get("combined_score", 0.0)

            max_score = max(max_score, semantic_score, keyword_score, combined_score)

        return max_score

    # Document processing methods
    async def process_multimodal_document(
        self, filename: str, content: bytes, user_id: str
    ) -> Dict[str, Any]:
        """Process various document types with user-specific storage"""
        try:
            # Validate user_id
            if not user_id or not user_id.strip():
                raise ValueError("user_id is required for document processing")

            self._ensure_user_data(user_id)

            file_ext = Path(filename).suffix.lower()

            # Create user-specific storage directory
            user_storage_path = Path(f"storage/users/{user_id}/documents")
            user_storage_path.mkdir(parents=True, exist_ok=True)

            processing_context = {
                "user_id": user_id,
                "filename": filename,
                "original_filename": (
                    filename.split(f"{user_id}_")[1]
                    if f"{user_id}_" in filename
                    else filename
                ),
                "file_extension": file_ext,
                "timestamp": datetime.now().isoformat(),
                "storage_path": str(user_storage_path),
            }

            if file_ext == ".pdf":
                return await self.process_pdf_advanced(
                    filename, content, user_id, processing_context
                )
            elif file_ext == ".txt":
                return await self.process_text_file(
                    filename, content, user_id, processing_context
                )
            elif file_ext == ".md":
                return await self.process_markdown_file(
                    filename, content, user_id, processing_context
                )
            elif file_ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]:
                return await self.process_image_file(
                    filename, content, user_id, processing_context
                )
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")

        except Exception as e:
            await self.log_user_processing_error(user_id, filename, str(e))
            print(f"Failed to process {filename} for user {user_id}: {e}")
            raise

    async def log_user_processing_error(self, user_id: str, filename: str, error: str):
        """Log processing errors for specific users"""
        try:
            error_log = {
                "user_id": user_id,
                "filename": filename,
                "error": error,
                "timestamp": datetime.now().isoformat(),
                "status": "failed",
            }
            print(f"Logged error for user {user_id}: {error}")
        except Exception as log_error:
            print(f"Failed to log error for user {user_id}: {log_error}")

    async def process_pdf_advanced(
        self, filename: str, content: bytes, user_id: str, context: Dict
    ) -> Dict[str, Any]:
        """Advanced PDF processing with user-specific storage"""
        try:
            # Save file in user directory
            file_path = Path(context["storage_path"]) / filename
            with open(file_path, "wb") as f:
                f.write(content)

            # Extract text using PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            full_text = ""

            for page in pdf_reader.pages:
                full_text += page.extract_text() + "\n"

            # Process text content for this user
            return await self.process_text_content(
                filename, full_text, "pdf", user_id, context
            )

        except Exception as e:
            print(f"PDF processing error for user {user_id}: {e}")
            raise

    async def process_text_file(
        self, filename: str, content: bytes, user_id: str, context: Dict
    ) -> Dict[str, Any]:
        """Process plain text file for specific user"""
        try:
            # Save file in user directory
            file_path = Path(context["storage_path"]) / filename
            with open(file_path, "wb") as f:
                f.write(content)

            text = content.decode("utf-8")
            return await self.process_text_content(
                filename, text, "text", user_id, context
            )
        except Exception as e:
            print(f"Text file processing error for user {user_id}: {e}")
            raise

    async def process_markdown_file(
        self, filename: str, content: bytes, user_id: str, context: Dict
    ) -> Dict[str, Any]:
        """Process markdown file with user-specific handling"""
        try:
            # Save file in user directory
            file_path = Path(context["storage_path"]) / filename
            with open(file_path, "wb") as f:
                f.write(content)

            text = content.decode("utf-8")

            # Try markdown-aware splitting first
            try:
                md_docs = self.md_splitter.split_text(text)
                if md_docs:
                    docs = []
                    for i, doc in enumerate(md_docs):
                        docs.append(
                            Document(
                                page_content=doc.page_content,
                                metadata={
                                    "source": context["original_filename"],
                                    "chunk_id": f"{user_id}_{filename}_md_{i}",
                                    "type": "markdown",
                                    "user_id": user_id,
                                    "timestamp": context["timestamp"],
                                },
                            )
                        )

                    await self.index_user_documents(docs, user_id)
                    return {
                        "user_id": user_id,
                        "filename": context["original_filename"],
                        "chunks_processed": len(docs),
                        "status": "success",
                        "type": "markdown",
                        "file_path": str(file_path),
                    }
            except:
                pass

            # Fallback to regular text processing
            return await self.process_text_content(
                filename, text, "markdown", user_id, context
            )

        except Exception as e:
            print(f"Markdown processing error for user {user_id}: {e}")
            raise

    async def process_image_file(
        self, filename: str, content: bytes, user_id: str, context: Dict
    ) -> Dict[str, Any]:
        """Process image file for specific user using vision model"""
        try:
            # Save file in user images directory
            user_images_path = Path(f"storage/users/{user_id}/images")
            user_images_path.mkdir(parents=True, exist_ok=True)

            file_path = user_images_path / filename
            with open(file_path, "wb") as f:
                f.write(content)

            # Encode image to base64
            base64_image = base64.b64encode(content).decode("utf-8")

            # Use vision model to describe image
            messages = [
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": "Describe this image in detail, including any text, objects, people, and context you can see.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ]
                )
            ]

            response = await self.vision_llm.ainvoke(messages)
            description = response.content.strip()

            # Create document from description
            doc = Document(
                page_content=description,
                metadata={
                    "source": context["original_filename"],
                    "chunk_id": f"{user_id}_{filename}_img_0",
                    "type": "image",
                    "user_id": user_id,
                    "timestamp": context["timestamp"],
                },
            )

            await self.index_user_documents([doc], user_id)

            # Cache the image for this user
            self.user_image_cache[user_id][filename] = base64_image

            return {
                "user_id": user_id,
                "filename": context["original_filename"],
                "chunks_processed": 1,
                "status": "success",
                "type": "image",
                "description": description,
                "file_path": str(file_path),
            }

        except Exception as e:
            print(f"Image processing error for user {user_id}: {e}")
            raise

    async def process_text_content(
        self, filename: str, text: str, doc_type: str, user_id: str, context: Dict
    ) -> Dict[str, Any]:
        """Process text content into user-specific chunks"""
        try:
            # Split into chunks
            chunks = self.text_splitter.split_text(text)

            # Create document objects with user-specific metadata
            docs = []
            for i, chunk in enumerate(chunks):
                docs.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": context["original_filename"],
                            "chunk_id": f"{user_id}_{filename}_{i}",
                            "type": doc_type,
                            "user_id": user_id,
                            "timestamp": context["timestamp"],
                        },
                    )
                )

            # Index documents for this user
            await self.index_user_documents(docs, user_id)

            return {
                "user_id": user_id,
                "filename": context["original_filename"],
                "chunks_processed": len(chunks),
                "status": "success",
                "type": doc_type,
                "file_path": context.get("storage_path", ""),
            }

        except Exception as e:
            print(f"Text content processing error for user {user_id}: {e}")
            raise

    async def index_user_documents(self, docs: List[Document], user_id: str):
        """Index documents in user-specific FAISS and BM25 indexes"""
        if not docs:
            return

        self._ensure_user_data(user_id)

        # Generate embeddings
        texts = [doc.page_content for doc in docs]
        embeddings = await self.embeddings.aembed_documents(texts)

        # Build or update user's FAISS index
        if user_id not in self.user_faiss_indexes:
            dimension = len(embeddings[0])
            self.user_faiss_indexes[user_id] = faiss.IndexFlatIP(dimension)

        embeddings_array = np.array(embeddings).astype("float32")
        faiss.normalize_L2(embeddings_array)
        self.user_faiss_indexes[user_id].add(embeddings_array)

        # Build or update user's BM25 index
        self.user_documents[user_id].extend(docs)
        all_user_texts = [doc.page_content for doc in self.user_documents[user_id]]
        tokenized_docs = [text.lower().split() for text in all_user_texts]
        self.user_bm25_indexes[user_id] = BM25Okapi(tokenized_docs)

        print(
            f"Indexed {len(docs)} chunks for user {user_id}. Total user documents: {len(self.user_documents[user_id])}"
        )

    async def clear_user_documents(self, user_id: str):
        """Clear all documents and indexes for a specific user"""
        if user_id in self.user_documents:
            del self.user_documents[user_id]
        if user_id in self.user_metadata:
            del self.user_metadata[user_id]
        if user_id in self.user_image_cache:
            del self.user_image_cache[user_id]
        if user_id in self.user_faiss_indexes:
            del self.user_faiss_indexes[user_id]
        if user_id in self.user_bm25_indexes:
            del self.user_bm25_indexes[user_id]

        print(f"All documents cleared for user {user_id}")

    async def clear_all_documents(self):
        """Clear all documents for all users"""
        self.user_documents = {}
        self.user_metadata = {}
        self.user_image_cache = {}
        self.user_faiss_indexes = {}
        self.user_bm25_indexes = {}
        print("All documents cleared for all users")

    def get_user_document_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about a user's loaded documents"""
        if user_id not in self.user_documents or not self.user_documents[user_id]:
            return {
                "user_id": user_id,
                "has_documents": False,
                "document_count": 0,
                "total_chunks": 0,
                "sources": [],
            }

        user_docs = self.user_documents[user_id]
        sources = list(set(doc.metadata.get("source", "unknown") for doc in user_docs))

        return {
            "user_id": user_id,
            "has_documents": True,
            "document_count": len(sources),
            "total_chunks": len(user_docs),
            "sources": sources,
        }

    def get_all_users_stats(self) -> Dict[str, Any]:
        """Get statistics for all users"""
        total_users = len(self.user_documents)
        total_documents = sum(len(docs) for docs in self.user_documents.values())

        user_stats = {}
        for user_id in self.user_documents:
            user_stats[user_id] = self.get_user_document_stats(user_id)

        return {
            "total_users": total_users,
            "total_documents": total_documents,
            "user_stats": user_stats,
        }


# Global instance
rag_service = RAGService()
