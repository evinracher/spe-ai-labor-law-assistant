# Colombian Labor Law RAG Backend

Intelligent chatbot with Retrieval-Augmented Generation (RAG) for **Colombian labor law** (*derecho laboral colombiano*) and general question answering capabilities.

> **Current Milestone — Intent Classification & General Q&A**  
> The server implements LangGraph-based intent classification to route questions between:
> - **Labor law queries**: RAG-based retrieval from Colombian labor law corpus (in development)
> - **General questions**: Direct LLM-based question answering (fully functional)
> 
> Vector retrieval and full RAG pipeline are **partially implemented** (see [Current Status](#current-status) and [Next Steps](#next-steps) below).

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
| LLM providers | Groq (default), Gemini, local (Ollama), or mock |
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
│   └── rag/
│       ├── agents.py      # LangGraph workflow with intent classification
│       ├── llm.py         # LLM provider implementations
│       ├── prompts.py     # System prompts for classification and Q&A
│       └── mock.py        # Deterministic mock RAG responder (fallback)
├── storage/               # ChromaDB persistent directory (created at runtime)
├── tests/
│   └── test_api.py        # Smoke tests with FastAPI TestClient
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
    "vector_db": "string"
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
  "trace": { "intent": null, "top_k": 0, "vector_db": "chroma" }
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
| `DATA_DIR` | `./data` | Corpus source files directory |
| `VECTOR_DB` | `chroma` | Vector database backend |
| `CHROMA_DIR` | `./storage/chroma` | ChromaDB persistent directory |
| `LLM_PROVIDER` | `groq` | `groq` (default) / `gemini` / `local` / `mock` |
| `GEMINI_API_KEY` | *(empty)* | Required for `LLM_PROVIDER=gemini` |
| `GROQ_API_KEY` | *(empty)* | Required for `LLM_PROVIDER=groq` (**required for default setup**) |
| `EMBEDDINGS_PROVIDER` | `local` | Embeddings backend |
| `EMBEDDINGS_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Multilingual model |

**Note**: The default configuration uses Groq's llama-3.1-8b-instant model. You must provide a `GROQ_API_KEY` for the chatbot to function. Get your API key at https://console.groq.com/

---

## Current Status

### ✅ Implemented Features

1. **LangGraph Agent Workflow** (`app/rag/agents.py`)
   - Intent classification node: Determines if a question is about labor law or general knowledge
   - RAG node: Handles labor law queries (currently uses mock data, will integrate with vector DB)
   - General search node: Handles general questions with direct LLM responses
   - In-memory conversation history with persistent conversation IDs
   - Conditional routing based on intent classification

2. **LLM Integration** (`app/rag/llm.py`)
   - Groq client (llama-3.1-8b-instant) — fully functional
   - Gemini client — fully functional
   - Configurable via `LLM_PROVIDER` environment variable

3. **Intent Classification**
   - Automatically routes questions to appropriate handler:
     - `domainSearch`: Labor law specific questions → RAG pipeline
     - `summarize`: Summarization requests → RAG pipeline
     - `compare`: Comparison questions → RAG pipeline
     - `generalSearch`: General knowledge questions → Direct LLM

4. **API Endpoints**
   - `GET /health`: Health check
   - `POST /chat`: Chat endpoint with intent-aware routing
   - Full request/response validation with Pydantic v2

5. **Conversation Management**
   - Persistent conversation threads using LangGraph checkpointer
   - Conversation ID-based message history
   - Automatic context retention across multiple questions

### 🚧 In Progress / TODO

---

## Next Steps

The following features are planned for upcoming milestones:

1. **Corpus ingestion pipeline** (`app/rag/ingest.py`)  
   Load PDF (pypdf), HTML (BeautifulSoup), and TXT files from `DATA_DIR`; normalize text; split into overlapping chunks (≈ 512 tokens, 64-token overlap); embed with sentence-transformers; persist to ChromaDB at `CHROMA_DIR`.

2. **ChromaDB client initialization** (`app/core/vector_store.py`)  
   Wrap `chromadb.PersistentClient`; create/load the `labor_law` collection; expose `similarity_search(query, top_k)` returning `List[Citation]`.

3. **Local embeddings service** (`app/rag/embeddings.py`)  
   Load `settings.EMBEDDINGS_MODEL` once at startup (cache in module); expose `embed(text) -> List[float]`. Use sentence-transformers multilingual model.

4. **`POST /ingest` endpoint** (optional)  
   Trigger the ingestion pipeline on demand, or add a CLI script `python -m app.ingest` to populate the vector database.

5. **Full RAG retrieval in `rag_node`** (`app/rag/agents.py`)  
   Replace mock responses with actual vector similarity search. Query ChromaDB, retrieve top-k relevant chunks, format as context for the LLM prompt.

6. **Enhanced strict prompt template** (`app/rag/prompts.py`)  
   Strengthen system prompt: *"Responde ÚNICAMENTE basándote en los fragmentos proporcionados. Si la información no está en los fragmentos, responde exactamente: 'No aparece en el contexto.' sin agregar nada más."*  
   Ensure the RAG node never hallucinates beyond retrieved context.

7. **Citation extraction and formatting**  
   Parse LLM responses to extract source references, page numbers, and snippets. Return properly formatted `Citation` objects in the API response with actual document sources.

8. **Local LLM support** (Ollama integration)  
   Implement `LocalClient` for `LLM_PROVIDER=local` to support offline/local models.

9. **Integration tests for full RAG pipeline** (`tests/test_pipeline.py`)  
   - Test that a labor law question gets citations from the corpus
   - Test that an out-of-domain question triggers general search
   - Test that unavailable information returns `"No aparece en el contexto."`
   - Test conversation history retention

10. **Performance optimization**  
    - Cache embeddings for common queries
    - Implement async vector search
    - Add request rate limiting and response caching
