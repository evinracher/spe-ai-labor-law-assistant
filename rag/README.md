# Colombian Labor Law RAG Backend

Strict Retrieval-Augmented Generation (RAG) chatbot for **Colombian labor law** (*derecho laboral colombiano*).

> **Milestone 1 — Mock API only.**  
> The server is fully runnable and exposes the final API contract.  
> Document ingestion, vector retrieval, and LLM generation are **not yet implemented** (see TODOs in source files and the [Next milestone checklist](#next-milestone-checklist) below).

---

## Goals

| Property | Value |
|---|---|
| Domain | Colombian labor law (PDF/HTML/TXT corpus) |
| Strictness | Answers **only** from retrieved context — never hallucinates |
| Safe response | `"No aparece en el contexto."` + empty citations |
| Embeddings | Local sentence-transformers (no paid API required) |
| Vector DB | ChromaDB (persistent local directory) |
| LLM providers | Gemini, Groq, local (Ollama), or **mock** (default) |
| Frontend | React app calling `POST /chat` — no auth required |

---

## Project structure

```
backend/
├── app/
│   ├── main.py            # FastAPI app + CORS + startup/shutdown hooks
│   ├── api/
│   │   ├── routes.py      # GET /health, POST /chat
│   │   └── schemas.py     # Pydantic v2 request/response models
│   ├── core/
│   │   └── config.py      # Pydantic Settings (env vars / .env)
│   └── rag/
│       └── mock.py        # Deterministic mock RAG responder
├── storage/               # ChromaDB persistent directory (created at runtime)
├── tests/
│   └── test_api.py        # Smoke tests with FastAPI TestClient
├── .env.example
├── .gitignore
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
| `DATA_DIR` | `./data` | Corpus source files directory |
| `VECTOR_DB` | `chroma` | Vector database backend |
| `CHROMA_DIR` | `./storage/chroma` | ChromaDB persistent directory |
| `LLM_PROVIDER` | `mock` | `mock` / `gemini` / `groq` / `local` |
| `GEMINI_API_KEY` | *(empty)* | Required for `LLM_PROVIDER=gemini` |
| `GROQ_API_KEY` | *(empty)* | Required for `LLM_PROVIDER=groq` |
| `EMBEDDINGS_PROVIDER` | `local` | Embeddings backend |
| `EMBEDDINGS_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Multilingual model |

---

## Next milestone checklist

1. **Corpus ingestion pipeline** (`app/rag/ingest.py`)  
   Load PDF (pypdf), HTML (BeautifulSoup), and TXT files from `DATA_DIR`; normalize text; split into overlapping chunks (≈ 512 tokens, 64-token overlap); embed with sentence-transformers; persist to ChromaDB at `CHROMA_DIR`.

2. **ChromaDB client initialization** (`app/core/vector_store.py`)  
   Wrap `chromadb.PersistentClient`; create/load the `labor_law` collection; expose `similarity_search(query, top_k)` returning `List[Citation]`.

3. **Local embeddings service** (`app/rag/embeddings.py`)  
   Load `settings.EMBEDDINGS_MODEL` once at startup (cache in module); expose `embed(text) -> List[float]`.

4. **`POST /ingest` endpoint**  
   Trigger the ingestion pipeline on demand (or add a CLI script `python -m app.ingest`).

5. **LangGraph RAG workflow** (`app/rag/pipeline.py`)  
   Nodes: `classify_intent → retrieve → generate → critic → finalize`. Wire `mock_rag_answer` as the fallback leaf. Make the graph async-compatible for FastAPI.

6. **LLM provider clients** (`app/rag/llm/`)  
   Implement `GeminiClient`, `GroqClient`, and `LocalClient` (Ollama). Route via `settings.LLM_PROVIDER` in `routes.py`.

7. **Strict prompt template** (`app/rag/prompts.py`)  
   System prompt: *"Responde ÚNICAMENTE basándote en los fragmentos proporcionados. Si la información no está en los fragmentos, responde exactamente: 'No aparece en el contexto.' sin agregar nada más."*

8. **Integration tests for retrieval + generation** (`tests/test_pipeline.py`)  
   Test that a question whose answer IS in the corpus gets ≥ 1 citation; test that an out-of-domain question gets `"No aparece en el contexto."` and `citations == []`.
