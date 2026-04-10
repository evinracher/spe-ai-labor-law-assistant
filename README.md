# AI Labor Law Assistant

An intelligent chatbot powered by Retrieval-Augmented Generation (RAG) that provides guidance and answers questions about Colombian labor law, as well as general questions.

## 📋 Overview

This project implements a conversational AI assistant specialized in Colombian labor legislation, developed for the *Ontology Engineering* course at UNAL. It combines three modern AI paradigms:

- **RAG** (Retrieval-Augmented Generation) — answers grounded in real legal documents via ChromaDB vector search
- **Knowledge Graphs** — structured OWL ontology + GraphDB for relationship-aware SPARQL queries (supplementary)
- **ReAct Agents** (LangGraph) — LLM autonomously decides which tools to call per query

The chatbot can:
- **Answer labor law questions**: Retrieves relevant legal information from a curated knowledge base and generates accurate, contextual responses about labor rights, employment regulations, and legal procedures in Colombia.
- **Answer general questions**: Handles general queries outside the labor law domain using a general-purpose language model.

## 🖼️ Screenshots & Demo

### Chat Interface

![Chat UI – Asistente de Derecho Laboral](examples/chat-ui-1.png)

> The assistant answering a question about fixed-term contracts and just-cause dismissal in Colombian labor law, with structured, citation-ready responses.

### Demo Video

A full walkthrough of the assistant in action is available as a screen recording:

**[▶ Watch demo.mp4](examples/demo.mp4)**

---

## ✨ Features

- 💬 Interactive chat interface for labor law queries and general questions
- 🧠 Intelligent 5-category intent classification via Gemini structured output
- 🔍 Dual retrieval: ChromaDB vector search (MMR) + GraphDB SPARQL for structured data
- 🔀 Adaptive query transformation: DIRECT, HyDE, or DECOMPOSITION strategies
- 🤖 ReAct agents with least-privilege tool sets (10 specialized legal tools)
- ✅ Self-critique reflection loop — up to 3 retry attempts before fallback
- 🌐 Fallback to Gemini Google Search grounding when internal KB is insufficient
- 📚 Knowledge base of Colombian labor legislation (CST, Ley 789, and more)
- 🎯 Contextual responses with legal citations and structured traceability
- 💾 Multi-turn conversation memory via LangGraph `InMemorySaver` checkpointer
- 🔄 Real-time chat interface with modern UI components

## 🏗️ Architecture

The system consists of:
- **Intent Classifier**: Gemini with structured Pydantic output classifies queries into 5 intents: `domainSearch`, `summarize`, `compare`, `draftDocument`, `generalSearch`
- **Multi-node Agent Flow** (LangGraph StateGraph): Routes queries through specialist ReAct nodes and a self-critique validation loop
- **RAG Pipeline**: Adaptive query transformation (HyDE / Decomposition / Direct) + dynamic-K MMR retrieval from ChromaDB
- **Dual Retrieval**: Vector search (ChromaDB) combined with structured SPARQL queries against GraphDB
- **Specialist Nodes**: `domain_search_node` (6 tools), `summarize_node` (4 tools), `compare_node` (4 tools), `draft_document_node` (1 tool)
- **Self-Critique Loop**: `validate_node` checks answers on 3 dimensions; retries up to 3 times with improved hints
- **Fallback Node**: Activates Gemini's built-in Google Search grounding after exhausting retries
- **General Q&A**: Handles off-domain questions via direct Groq/Llama response
- **Vector Database**: Persistent ChromaDB with semantic chunking (percentile-85 threshold)
- **LLM Integration**: Gemini (`gemini-2.5-flash`) for reasoning-heavy tasks; Groq (`llama-3.1-8b-instant`) for fast structured tasks
- **Legal Tools Layer**: 10 tools — law/article lookup, jurisprudence, citation verification, vigency checks, KG queries, risk evaluation, document drafting
- **Chat Interface**: Modern React-based UI with TypeScript and Vite
- **Conversation Memory**: Multi-turn memory via LangGraph `InMemorySaver` checkpointer with persistent `thread_id`

## 🛠️ Tech Stack

### Backend
- **Primary LLM**: Google Gemini (`gemini-2.5-flash`) — classification, generation, SPARQL generation, self-critique
- **Secondary LLM**: Groq (`llama-3.1-8b-instant`) — dynamic-K selection, query transformation, general responses
- **Embeddings**: `gemini-embedding-001` for semantic chunking, ingestion, and retrieval
- **Framework**: LangGraph 0.2.0+ for StateGraph agent orchestration
- **Vector Database**: ChromaDB (persistent local storage) with MMR retrieval
- **Knowledge Graph**: GraphDB (RDF triple store, SPARQL endpoint) + OWL ontology (supplementary)
- **Backend**: FastAPI with Uvicorn
- **Programming Language**: Python 3.11+
- **Additional Libraries**: Pydantic v2, LangChain, langchain-experimental (`SemanticChunker`), SPARQLWrapper, rdflib, pypdf

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Components**: Radix UI, Material-UI (MUI)
- **Styling**: Tailwind CSS, Emotion
- **State Management**: React useState and localStorage for conversation persistence

## 📚 Data Sources

- Colombian Labor Code (Código Sustantivo del Trabajo — CST)
- Ley 789 and other complementary Colombian labor legislation
- Document processing pipeline: PDF extraction → text cleaning → semantic chunking (percentile-85 threshold) → `gemini-embedding-001` embeddings → persistent ChromaDB indexing

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

No license has been specified yet in this repository.

## ✅ Done Features

### Technical Features
- [x] FastAPI backend with `GET /health` and `POST /chat`
- [x] LangGraph StateGraph with multi-node orchestration and 5-category intent classification
- [x] Dual LLM strategy: Gemini (reasoning) + Groq/Llama (fast structured tasks)
- [x] Persistent ChromaDB vector storage with MMR retrieval
- [x] Adaptive query transformation: DIRECT, HyDE, and DECOMPOSITION strategies
- [x] Dynamic-K retrieval selection (1–10 chunks) based on query complexity
- [x] 10 legal tools with least-privilege assignment per agent node
- [x] SPARQL-based knowledge graph retrieval via GraphDB (supplementary structured data)
- [x] Self-critique validation loop with up to 3 retry attempts and improvement hints
- [x] Fallback to Gemini Google Search grounding on validation failure
- [x] PDF ingestion pipeline with cleaning, semantic chunking, and vector indexing
- [x] Request/response validation with Pydantic v2 models and execution trace support

### Architectural Features
- [x] Intent-based routing into 5 flows: `domainSearch`, `summarize`, `compare`, `draftDocument`, `generalSearch`
- [x] Specialist ReAct nodes with tool access scoped by task type
- [x] Reflective agent pattern: `validate_node` evaluates grounding, completeness, and relevance
- [x] Citation-aware answer generation with legal article references
- [x] Multi-turn conversation memory via `InMemorySaver` checkpointer and persistent `thread_id`
- [x] Decoupled frontend/backend architecture (React + FastAPI)

## 📧 Contact

For support, maintenance, or collaboration, use repository Issues and Pull Requests.

## ⚠️ Disclaimer

This chatbot is an educational/assistive tool and should not be considered as professional legal advice. For specific legal matters, please consult with a qualified legal professional.

## 🙏 Acknowledgments

- Colombian labor law public sources used for the legal corpus
- Open-source ecosystem: FastAPI, LangGraph, LangChain, ChromaDB, React, Vite, Radix UI, and Material UI
