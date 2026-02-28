# AI Labor Law Assistant

An intelligent chatbot powered by Retrieval-Augmented Generation (RAG) that provides guidance and answers questions about Colombian labor law, as well as general questions.

## 📋 Overview

This project implements a conversational AI assistant specialized in Colombian labor legislation. Using RAG technology and intelligent intent classification, the chatbot can:
- **Answer labor law questions**: Retrieves relevant legal information from a curated knowledge base and generates accurate, contextual responses about labor rights, employment regulations, and legal procedures in Colombia.
- **Answer general questions**: Handles general queries outside the labor law domain using a general-purpose language model.

## ✨ Features

- 💬 Interactive chat interface for labor law queries and general questions
- 🧠 Intelligent intent classification (labor law vs. general questions)
- 🔍 RAG-based retrieval of relevant legal documents and articles for labor law queries
- 🌐 General question answering capabilities using state-of-the-art language models
- 📚 Knowledge base of Colombian labor legislation
- 🎯 Contextual responses with legal references and citations
- 💾 Conversation history management across sessions
- 🔄 Real-time chat interface with modern UI components

## 🏗️ Architecture

The system consists of:
- **Intent Classifier**: Uses LangGraph to classify user questions as labor law queries or general questions
- **RAG Pipeline**: For labor law queries, retrieves relevant context from the knowledge base before generating responses
- **General Q&A**: Handles general questions using a general-purpose language model
- **Vector Database**: Stores embeddings of Colombian labor law documents (ChromaDB)
- **LLM Integration**: Generates natural language responses using Groq/Gemini APIs
- **Chat Interface**: Modern React-based UI with TypeScript and Vite
- **Conversation Memory**: In-memory conversation history with persistent conversation IDs

## 🛠️ Tech Stack

### Backend
- **LLM**: Groq (llama-3.1-8b-instant), with support for Google Gemini
- **Framework**: LangGraph 0.2.0+ for AI agent workflows
- **Vector Database**: ChromaDB (persistent local storage)
- **Backend**: FastAPI with Uvicorn
- **Programming Language**: Python 3.11+
- **Embeddings**: TODO: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **Additional Libraries**: Pydantic, LangChain, httpx

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Components**: Radix UI, Material-UI (MUI)
- **Styling**: Tailwind CSS, Emotion
- **State Management**: React useState and localStorage for conversation persistence

## 📚 Data Sources

<!-- TODO: Specify the Colombian labor law sources used -->
- Colombian Labor Code (Código Sustantivo del Trabajo)
- TODO: Add specific legal databases and documents
- TODO: Specify data collection and processing methods

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or newer
- Node.js 18+ and npm
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd spe-ai-labor-law-assistant
```

### Backend Setup

```bash
# Navigate to the RAG backend directory
cd rag

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies and pre-commit hooks
make setup

# Or manually:
# pip install --upgrade pip
# pip install -e ".[dev]"
# pre-commit install
```

### Frontend Setup

```bash
# Navigate to the chat UI directory
cd chat-ui

# Install dependencies
npm install
```

### Configuration

#### Backend Configuration

Create a `.env` file in the `rag/` directory:

```env
# Server settings
HOST=0.0.0.0
PORT=8000
ENV=dev

# LLM Provider (mock, groq, gemini, or local)
LLM_PROVIDER=groq

# API Keys (required for non-mock providers)
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Vector Database
VECTOR_DB=chroma
CHROMA_DIR=./storage/chroma

# Embeddings
EMBEDDINGS_PROVIDER=local
EMBEDDINGS_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Data directory
DATA_DIR=./data
```

#### Frontend Configuration

Create a `.env` file in the `chat-ui/` directory:

```env
# Backend API URL
VITE_API_URL=http://localhost:8000
```

### Running the Application

#### Start the Backend

```bash
# From the rag/ directory
cd rag
source .venv/bin/activate  # If not already activated

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the Python module entry point:
# python -m app.main
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

#### Start the Frontend

```bash
# From the chat-ui/ directory
cd chat-ui

# Run the development server
npm run dev
```

The chat interface will be available at `http://localhost:5173` (or the port shown in terminal)

## 📖 Usage

### Using the Chat Interface

1. Open your browser and navigate to `http://localhost:5173`
2. Type your question in the chat input field
3. The assistant will:
   - Classify your question as either a labor law query or general question
   - For labor law questions: retrieve relevant legal documents and provide answers with citations
   - For general questions: provide direct answers using the language model
4. Your conversation history is preserved across sessions using a persistent conversation ID

### Using the API Directly

#### Health Check

```bash
curl -s http://localhost:8000/health
```

#### Ask a Labor Law Question

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuántos días de vacaciones tiene derecho un trabajador en Colombia?"
  }' | python3 -m json.tool
```

#### Ask a General Question

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la inteligencia artificial?"
  }' | python3 -m json.tool
```

## 🧪 Testing

### Backend Tests

```bash
# From the rag/ directory
cd rag
source .venv/bin/activate

# Run tests
pytest -v

# Run tests with coverage
pytest -v --cov=app
```

### Frontend Development

```bash
# From the chat-ui/ directory
cd chat-ui

# Build for production
npm run build
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development practices and contribution guidelines.

## 📄 License

<!-- TODO: Specify license -->
TODO: Add license information (e.g., MIT, Apache 2.0, GPL-3.0)

## 🗺️ Roadmap

### Completed ✅
- [x] Backend API with FastAPI
- [x] Intent classification (labor law vs. general questions)
- [x] General question answering capability
- [x] Conversation history management with LangGraph
- [x] React chat interface with modern UI components
- [x] Integration with Groq and Gemini LLM providers
- [x] Mock RAG for development

### In Progress 🚧
- [ ] Document ingestion pipeline for Colombian labor law corpus
- [ ] Vector database integration with ChromaDB
- [ ] Sentence-transformers embeddings implementation
- [ ] Full RAG pipeline with actual document retrieval
- [ ] Citation and reference system with source documents

### Planned 📋
- [ ] Multi-language support (Spanish/English interface)
- [ ] Enhanced conversation context management
- [ ] Document upload and custom corpus management
- [ ] Advanced search filters and query refinement
- [ ] Performance monitoring and analytics

## 📧 Contact

<!-- TODO: Add contact information -->
TODO: Add maintainer contact information

## ⚠️ Disclaimer

This chatbot is an educational/assistive tool and should not be considered as professional legal advice. For specific legal matters, please consult with a qualified legal professional.

## 🙏 Acknowledgments

<!-- TODO: Add acknowledgments -->
- TODO: Credit data sources, libraries, and contributors
