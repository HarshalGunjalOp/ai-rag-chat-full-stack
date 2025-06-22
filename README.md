# 🚀 AI RAG Chat Application

*A production-ready, full-stack Retrieval-Augmented Generation (RAG) chat application built with modern AI technologies*

[![GitHub stars](https://img.shields.io/github/stars/HarshalGunjalOp/ai-rag-chat-full-stack?style=social)](https://github.com/username/ai-rag-chat)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

## 🎯 **Project Overview**

This intelligent chat application leverages cutting-edge **Retrieval-Augmented Generation (RAG)** technology to provide accurate, context-aware responses by combining the power of Large Language Models with real-time document retrieval. Built with a modern full-stack architecture, it demonstrates enterprise-grade scalability, security, and performance optimization.

### ✨ **Key Highlights**

- 🧠 **Advanced RAG Pipeline**: Sophisticated retrieval-augmented generation with vector similarity search
- ⚡ **Real-time Streaming**: WebSocket-based streaming responses with sub-second latency
- 🏗️ **Production Architecture**: Microservices design with containerized deployment
- 🔐 **Enterprise Security**: JWT authentication, rate limiting, and data encryption
- 📊 **Intelligent Analytics**: Real-time monitoring with performance metrics and usage insights
- 🌐 **Scalable Infrastructure**: Auto-scaling capabilities with load balancing
- 🎨 **Modern UI/UX**: Responsive design with dark mode and accessibility features

---

## 🏛️ **Architecture & Technology Stack**

### **Frontend**
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand with persistence
- **Real-time**: WebSocket integration for streaming

### **Backend**
- **API Framework**: FastAPI with async/await support
- **Language**: Python 3.11+ with type hints
- **Authentication**: JWT with refresh token rotation
- **Caching**: Redis for session management and query caching

### **AI & Machine Learning**
- **LLM Integration**: OpenAI GPT-4, Anthropic Claude, or local models
- **Vector Database**: Pinecone/Weaviate for semantic search
- **Embeddings**: OpenAI text-embedding-ada-002
- **Framework**: LangChain for RAG orchestration
- **Document Processing**: PyPDF2, python-docx for multi-format support

### **Data & Infrastructure**
- **Database**: PostgreSQL with pgvector extension
- **Message Queue**: Redis/RabbitMQ for async processing
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes for production deployment
- **Monitoring**: Prometheus + Grafana for observability

---

## 🚀 **Quick Start**

### **Prerequisites**
- Node.js 18+ and npm/yarn
- Python 3.11+
- Docker and Docker Compose
- OpenAI API key (or alternative LLM provider)

### **1. Clone the Repository**
```bash
git clone https://github.com/HarshalGunjalOp/ai-rag-chat-full-stack.git
cd ai-rag-chat
```

### **2. Environment Setup**
```bash
# Copy environment template for both frontend and backend and add your api keys
cp .env.example .env
```

### **3. Start with Docker (Recommended)**
```bash
# Build and start all services
docker-compose up --build

# Access the application
open http://localhost:3000
```

### **4. Manual Setup (Development)**
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

---

## 📋 **Core Features**

### 🤖 **Intelligent Conversational AI**
- **Context-Aware Responses**: Maintains conversation history and context
- **Multi-Document RAG**: Retrieves information from multiple document sources
- **Source Attribution**: Citations and references for all generated content
- **Adaptive Learning**: Learns from user interactions to improve responses

### 📄 **Document Management**
- **Multi-Format Support**: PDF, DOCX, TXT, Markdown processing
- **Intelligent Chunking**: Semantic text splitting with overlap optimization
- **Batch Upload**: Concurrent processing of multiple documents
- **Version Control**: Document versioning with change tracking

### 🔍 **Advanced Search & Retrieval**
- **Semantic Search**: Vector similarity search with configurable thresholds
- **Hybrid Retrieval**: Combines dense and sparse retrieval methods
- **Query Expansion**: Automatic query enhancement for better results
- **Relevance Scoring**: Advanced ranking algorithms for result prioritization

### 📊 **Analytics & Monitoring**
- **Usage Metrics**: Query volume, response times, user engagement
- **Performance Monitoring**: System health, API latency, error rates
- **Cost Tracking**: Token usage and API cost optimization
- **A/B Testing**: Experimental features with performance comparison

---

## 🛠️ **Development**

### **Project Structure**
```
ai-rag-chat-full-stack/
├── frontend/                 # Next.js application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Application pages
│   │   ├── hooks/          # Custom React hooks
│   │   └── utils/          # Utility functions
│   └── package.json
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core functionality
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   └── requirements.txt
└── README.md
```

### **Code Formatting**
```bash
# Python formatting
black . && isort . && flake8

# TypeScript formatting
npx prettier --write .
```

## 📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**⭐ If you find this project helpful, please give it a star on GitHub!**

*Built with ❤️ by Harshal - [My Linkedin](https://linkedin.com/in/harshalgunjal)*
