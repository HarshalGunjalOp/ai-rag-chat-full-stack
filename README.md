# 🚀 AI RAG Chat Application

*A production-ready, full-stack Retrieval-Augmented Generation (RAG) chat application built with modern AI technologies*

This is the deployment link: [Link to the website](https://www.harshalgunjal.in/) <br>
I have deployed this application using an AWS EC2 instance and nginx for reverse proxy.

[![GitHub stars](https://img.shields.io/github/stars/HarshalGunjalOp/ai-rag-chat-full-stack?style=social)](https://github.com/username/ai-rag-chat)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

## 🎯 **Project Overview**

This intelligent chat application leverages cutting-edge **Retrieval-Augmented Generation (RAG)** technology to provide accurate, context-aware responses by combining the power of Large Language Models with real-time document retrieval. Used redis for caching and it gives near instant cached responses. Deployed it on a AWS EC2 instance.

### ✨ **Key Highlights**

- 🧠 **Advanced RAG Pipeline**: Sophisticated retrieval-augmented generation with vector similarity search
- ⚡ **Real-time Streaming**: Async real-time streaming responses with sub-second latency
- 🎨 **Modern UI/UX**: Modern and cool looking UI with dark mode and accessibility features
- 🎹 **Keyboard Shortcuts**: Ctrl+I for new chat and Ctrl+b to collapse sidebar
- 🚀 **Superfast Redis Caching**: Implemented aggresive redis caching with 1hr of TTL.
- 📜 **Multiple Document Types Supported**: I have implemented support for text files, pdf files, markdown files as well all Multiple image types as well.


### **Swagger Docs**

If you want to test out the backend API endpoints, then you can use the swagger docs provided on this link: [Swagger Docs](https://www.harshalgunjal.in/docs)

---

## 🏛️ **Architecture & Technology Stack**

### **Frontend**
- **Framework**: ReactJs with react-router-dom
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS

### **Backend**
- **API Framework**: FastAPI with async/await support
- **Language**: Python 3.11+ with type hints
- **Caching**: Redis for session management and query caching

### **AI & Machine Learning**
- **LLM Integration**: OpenAI GPT o3-mini model
- **Embeddings**: OpenAI text-embedding
- **Framework**: LangChain for RAG orchestration
- **Document Processing**: PyPDF2, python-docx for multi-format support

### **Data & Infrastructure**
- **Database**: PostgreSQL with pgvector extension
- **Message Queue**: Redis for async processing

---

## 🚀 **Quick Start**

### **Prerequisites**
- Node.js 18+ and npm/yarn
- Python 3.11+
- OpenAI API key (or alternative LLM provider)

### **1. Clone the Repository**
```bash
git clone https://github.com/HarshalGunjalOp/ai-rag-chat-full-stack.git
cd ai-rag-chat-full-stack
```

### **2. Environment Setup**
```bash
# Copy environment template for both frontend and backend and add your api keys
cp .env.example .env
```


### **4. Development Setup**
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
