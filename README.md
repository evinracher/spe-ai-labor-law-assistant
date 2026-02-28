# AI Labor Law Assistant

An intelligent chatbot powered by Retrieval-Augmented Generation (RAG) that provides guidance and answers questions about Colombian labor law, as well as general questions.

## 📋 Overview

This project implements a conversational AI assistant specialized in Colombian labor legislation. Using RAG technology and a LangGraph-based agent workflow with 5 formal tools, the chatbot can:
- **Answer labor law questions**: Retrieves relevant legal information from a curated knowledge base (50+ PDFs) and generates accurate, contextual responses about labor rights, employment regulations, and legal procedures in Colombia.
- **Answer general questions**: Handles general queries outside the labor law domain using a general-purpose language model.
- **Provide full traceability**: Shows which legal fragments were retrieved and how the answer was constructed.

## ✨ Features

- 💬 Interactive chat interface for labor law queries and general questions
- 🧠 Intelligent intent classification (labor law vs. general questions) via LangGraph
- 🔍 RAG-based retrieval of relevant legal documents from 50+ Colombian legislation PDFs
- 🌐 General question answering using Groq and Gemini LLM providers
- 📚 Knowledge base covering the Código Sustantivo del Trabajo, Decreto 1072, Ley 100, and more
- 🎯 Contextual responses with legal citations panel and source snippets
- 🔎 Workflow trace panel showing retrieval steps and tool execution
- 💾 Conversation history management across sessions

## 🏗️ Architecture

The system consists of:
- **LangGraph Agent Workflow**: Orchestrates 5 formal tools — intent classification, semantic search, document reading, grounded answer generation, and answer validation.
- **RAG Pipeline**: For labor law queries, retrieves relevant context from ChromaDB before generating responses with citations.
- **General Q&A**: Handles general questions using a direct LLM call.
- **Vector Database**: ChromaDB with HuggingFace sentence-transformer embeddings of 50+ legal documents.
- **LLM Integration**: Groq (llama-3.1-8b-instant) for retrieval tasks; Google Gemini for answer generation.
- **Chat Interface**: Modern React-based UI with citations panel and workflow trace panel.
- **Conversation Memory**: In-memory conversation history with persistent conversation IDs.

## 🛠️ Tech Stack

### Backend
- **LLM (Retrieval)**: Groq — llama-3.1-8b-instant
- **LLM (Generation)**: Google Gemini
- **Framework**: LangGraph 0.2.0+ for AI agent workflows
- **Vector Database**: ChromaDB (persistent local storage)
- **Backend**: FastAPI with Uvicorn
- **Language**: Python 3.11+
- **Embeddings**: HuggingFace sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`)
- **Additional Libraries**: Pydantic v2, LangChain, LangChain-Community

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Components**: Radix UI, Material-UI (MUI)
- **Styling**: Tailwind CSS, Emotion
- **State Management**: React useState and localStorage for conversation persistence

## 📚 Data Sources

The knowledge base includes 50+ official Colombian labor law documents, among them:

- Código Sustantivo del Trabajo (Decreto 2158 de 1948)
- Decreto 1072 de 2015 — Decreto Único Reglamentario del Sector Trabajo
- Decreto 780 de 2016 — Sector Salud y Protección Social
- Decreto 1833 de 2016 — Sistema General de Pensiones
- Ley 100 de 1993 — Sistema de Seguridad Social Integral
- Ley 1010 de 2006 — Acoso Laboral
- Ley 2101 de 2021, Ley 2114 de 2021, Ley 2191 de 2022, Ley 2365 de 2024, and more
- Multiple circulares and resoluciones from the Ministerio del Trabajo

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or newer
- Node.js 18+ and npm
- Git
- A Groq API key ([console.groq.com](https://console.groq.com/))
- A Google AI API key ([aistudio.google.com](https://aistudio.google.com/))

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd spe-ai-labor-law-assistant
```

### Backend Setup

```bash
cd rag

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies and pre-commit hooks
make setup
```

### Frontend Setup

```bash
cd chat-ui
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

# LLM Provider (mock, groq, gemini)
LLM_PROVIDER=groq

# API Keys
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Vector Database
VECTOR_DB=chroma
CHROMA_DIR=./db_chroma

# Embeddings
EMBEDDINGS_PROVIDER=local
EMBEDDINGS_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Data directory
DATA_DIR=./app/data
```

#### Frontend Configuration

Create a `.env` file in the `chat-ui/` directory:

```env
VITE_API_URL=http://localhost:8000
```

### Ingesting Documents

Before first use, populate the vector database:

```bash
cd rag
source .venv/bin/activate
python -m app.rag.pipelines.run_ingestion
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

## ⚠️ Disclaimer

This chatbot is an educational/assistive tool and should not be considered as professional legal advice. For specific legal matters, please consult with a qualified legal professional.

## 🙏 Acknowledgments

- Colombian labor law documents sourced from official government publications and the Ministerio del Trabajo.
- Built with [LangChain](https://www.langchain.com/), [LangGraph](https://www.langchain.com/langgraph), [ChromaDB](https://www.trychroma.com/), [FastAPI](https://fastapi.tiangolo.com/), and [React](https://react.dev/).
- Embeddings provided by [sentence-transformers](https://www.sbert.net/).
