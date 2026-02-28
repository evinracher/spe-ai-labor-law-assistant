# Colombian Labor Law RAG Backend

Intelligent chatbot with Retrieval-Augmented Generation (RAG) for **Colombian labor law** (*derecho laboral colombiano*) and general question answering capabilities.

The backend implements a LangGraph-based agent workflow with 5 formal tools that orchestrate intent classification, semantic search over 50+ legal documents, grounded answer generation, and answer validation.

---

## Goals

| Property | Value |
|---|---|
| Domain | Colombian labor law (PDF/HTML/TXT corpus) + general knowledge |
| Intent Classification | Automatic routing between RAG and general Q&A |
| RAG Strictness | Answers **only** from retrieved context — never hallucinates |
| Safe response (RAG) | `"No aparece en el contexto."` + empty citations |
| General Q&A | Direct answers for non-labor-law questions |
| Embeddings | Local sentence-transformers (no paid API required) |
| Vector DB | ChromaDB (persistent local directory) |
| LLM providers | Groq (llama-3.1-8b-instant), Gemini, or mock |
| Workflow Engine | LangGraph for agent orchestration |
| Frontend | React app calling `POST /chat` — no auth required |

---

## Project structure

```
rag/
├── app/
│   ├── main.py            # FastAPI app + CORS + startup/shutdown hooks
│   ├── api/
│   │   ├── routes.py      # GET /health, POST /chat
│   │   └── schemas.py     # Pydantic v2 request/response models
│   ├── core/
│   │   └── config.py      # Pydantic Settings (env vars / .env)
│   ├── data/              # Colombian labor law PDF corpus (50+ documents)
│   └── rag/
│       ├── agents.py      # LangGraph workflow with intent classification
│       ├── tools.py       # 5 formal LangChain Tools
│       ├── retriever.py   # Dynamic-k similarity search
│       ├── ingestion.py   # PDF ingestion & text splitting
│       ├── llm.py         # LLM provider implementations
│       ├── prompts.py     # System prompts for classification and Q&A
│       ├── mock.py        # Deterministic mock responder (fallback)
│       └── pipelines/
│           └── run_ingestion.py  # CLI entry point for corpus ingestion
├── db_chroma/         # ChromaDB persistent directory
├── tests/
│   ├── test_api.py        # API smoke tests (FastAPI TestClient)
│   └── test_rag.py        # RAG pipeline tests
├── .env.example
├── .gitignore
├── Makefile               # Development commands
├── pyproject.toml
└── README.md              # ← you are here
```

---

## Local setup

### Prerequisites

- Python 3.11 or newer
- `pip` / `venv` (standard library)

### 1 — Clone and navigate

```bash
# from the repository root
cd rag
```

### 2 — Create and activate a virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows PowerShell
```

### 3 — Install dependencies and git hooks

```bash
make setup
```

This installs all dependencies (`pip install -e ".[dev]"`) **and** activates the pre-commit hooks (ruff linter + formatter) that run automatically on every `git commit`.

> **Manual alternative** (if `make` is not available):
> ```bash
> pip install --upgrade pip
> pip install -e ".[dev]"
> pre-commit install
> ```

### 4 — Configure environment

```bash
cp .env.example .env
# Edit .env if you want to change HOST, PORT, or add API keys.
# The defaults work out-of-the-box with LLM_PROVIDER=mock.
```

### 5 — Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the Python module entry point:

```bash
python -m app.main
```

The interactive API docs are available at <http://localhost:8000/docs> (dev mode only).

---

## Running tests

```bash
pytest -v
```

---

## API reference

### `GET /health`

Liveness probe. Returns `200 OK` when the server is accepting requests.

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

**Expected response:**

```json
{
  "ok": true
}
```

---

### `POST /chat`

Ask the Colombian labor law assistant.

#### Request body

```json
{
  "question": "string (5–2000 chars)",
  "conversation_id": "string | null",
  "max_citations": "integer | null"
}
```

#### Response body

```json
{
  "ok": true,
  "request_id": "uuid-string",
  "answer": "string (Spanish)",
  "citations": [
    {
      "source": "string",
      "page": "integer | null",
      "chunk_id": "string | null",
      "snippet": "string"
    }
  ],
  "trace": {
    "intent": "string | null",
    "top_k": "integer | null",
    "vector_db": "string",
    "llm_provider": "string"
  }
}
```

---

### curl examples

#### Liveness check

```bash
curl -s http://localhost:8000/health
```

#### In-context question (returns citations)

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuántos días de vacaciones tiene derecho un trabajador en Colombia?"
  }' | python3 -m json.tool
```

**Expected (mock):** answer with 2–4 paragraphs and 2–4 citations from the CST and related laws.

#### Out-of-context question (returns empty citations)

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuántos planetas tiene el sistema solar?"
  }' | python3 -m json.tool
```

**Expected (mock):**

```json
{
  "ok": true,
  "request_id": "...",
  "answer": "No aparece en el contexto.",
  "citations": [],
  "trace": { "intent": null, "top_k": 0, "vector_db": "chroma", "llm_provider": "mock" }
}
```

#### Validation error (question too short)

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "hoy"}' | python3 -m json.tool
```

**Expected:** `422 Unprocessable Entity` with a descriptive validation error.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind host |
| `PORT` | `8000` | Bind port |
| `ENV` | `dev` | Runtime environment (`dev` or `prod`) |
| `DATA_DIR` | `./app/data` | Corpus source files directory |
| `VECTOR_DB` | `chroma` | Vector database backend |
| `CHROMA_DIR` | `./db_chroma` | ChromaDB persistent directory |
| `LLM_PROVIDER` | `groq` | `groq` (default) / `gemini` / `local` / `mock` |
| `GOOGLE_API_KEY` | *(empty)* | Required for `LLM_PROVIDER=gemini` |
| `GROQ_API_KEY` | *(empty)* | Required for `LLM_PROVIDER=groq` (**required for default setup**) |
| `EMBEDDINGS_PROVIDER` | `local` | Embeddings backend |
| `EMBEDDINGS_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Multilingual model |

**Note**: The default configuration uses Groq's llama-3.1-8b-instant model. You must provide a `GROQ_API_KEY` for the chatbot to function. Get your API key at https://console.groq.com/

---

## Implemented Features

1. **LangGraph Agent Workflow** (`app/rag/agents.py`)
   - Intent classification node using Tool 1 (`classify_intent` via Gemini)
   - RAG node for labor law queries: semantic search → grounded generation → answer validation
   - General search node for non-labor-law questions with direct LLM responses
   - In-memory conversation history (`InMemorySaver`) with persistent conversation IDs
   - Conditional routing based on intent classification

2. **5 Formal LangChain Tools** (`app/rag/tools.py`)
   - `classify_intent` — Classifies user intent using Gemini (`domainSearch` / `summarize` / `compare` / `generalSearch`)
   - `semantic_search` — Dynamic-k similarity search over ChromaDB; uses Groq to determine retrieval depth (1–10 fragments)
   - `read_document` — Full document access by source metadata for citation verification
   - `generate_grounded_answer` — Grounded answer generation with citations using Gemini
   - `validate_answer` — Quality assessment and hallucination detection

3. **LLM Integration** (`app/rag/llm.py`)
   - Groq client (llama-3.1-8b-instant) — used for dynamic-k retrieval decisions
   - Gemini client — used for intent classification and grounded answer generation

4. **Corpus Ingestion Pipeline** (`app/rag/ingestion.py`, `app/rag/pipelines/run_ingestion.py`)
   - Loads 50+ PDF documents from `app/data/`
   - Cleans and normalizes extracted text (removes noise, normalizes whitespace)
   - Splits documents into overlapping chunks (1000 tokens, 150 overlap) with legal-aware separators (`ARTÍCULO`, `PARÁGRAFO`, `CAPÍTULO`, etc.)
   - Embeds chunks with `paraphrase-multilingual-MiniLM-L12-v2` and persists to ChromaDB

5. **RAG Retriever** (`app/rag/retriever.py`)
   - Dynamic-k retrieval: Groq determines how many fragments to retrieve per query (1–10)
   - Formats retrieved documents with source, page, and snippet for citation

6. **API Endpoints**
   - `GET /health`: Health check
   - `POST /chat`: Chat endpoint with intent-aware routing, citations, and execution trace
   - Full request/response validation with Pydantic v2

7. **Conversation Management**
   - Persistent conversation threads using LangGraph `InMemorySaver`
   - Conversation ID-based message history
   - Automatic context retention across multiple questions in a session
    - Add request rate limiting and response caching
