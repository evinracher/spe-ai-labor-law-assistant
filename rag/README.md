# Colombian Labor Law RAG Backend

FastAPI backend powering an AI assistant specialized in **Colombian labor law** (*derecho laboral colombiano*). It combines Retrieval-Augmented Generation (RAG), a LangGraph multi-node agent workflow, adaptive query transformation, and a self-critique reflection loop to deliver grounded, citation-backed answers in Spanish.

---

## Goals

| Property | Value |
|---|---|
| Domain | Colombian labor law corpus + general knowledge |
| Intent Classification | 5-category automatic routing |
| Retrieval | Dual: ChromaDB vector search + GraphDB SPARQL |
| Query Transformation | Adaptive: DIRECT / HyDE / DECOMPOSITION |
| Dynamic-K Selection | Groq selects 1–10 chunks per query at runtime |
| Retrieval Strategy | MMR (Maximal Marginal Relevance) for diversity |
| Self-Critique | Reflection loop — up to 3 retry attempts |
| Fallback | Gemini built-in Google Search grounding |
| Embeddings | `gemini-embedding-001` (ingestion + retrieval) |
| Vector DB | ChromaDB (persistent local directory) |
| LLM providers | Gemini (`gemini-2.5-flash`) + Groq (`llama-3.1-8b-instant`) |
| Workflow Engine | LangGraph StateGraph with `InMemorySaver` checkpointer |
| Frontend | React app calling `POST /chat` — no auth required |

---

## Project structure

```
rag/
├── app/
│   ├── main.py                    # FastAPI app + CORS + startup/shutdown hooks
│   ├── api/
│   │   ├── routes.py              # GET /health, POST /chat
│   │   └── schemas.py             # Pydantic v2 request/response models
│   ├── core/
│   │   └── config.py              # Pydantic Settings (env vars / .env)
│   ├── db/
│   │   ├── chroma.py              # ChromaDB client wrapper
│   │   └── graphdb.py             # SPARQLWrapper connector for GraphDB
│   └── rag/
│       ├── agents.py              # LangGraph StateGraph — all nodes + routing logic
│       ├── tools.py               # 10 @tool-decorated functions (least-privilege sets)
│       ├── retriever.py           # Dynamic-K selection + MMR retrieval from ChromaDB
│       ├── query_transformer.py   # Adaptive query transformation (DIRECT/HyDE/DECOMPOSITION)
│       ├── ingestion.py           # PDF loading, cleaning, semantic chunking, embedding
│       ├── llm.py                 # LLM provider factory
│       ├── prompts.py             # System prompts for all nodes
│       ├── metrics.py             # LLM-as-judge evaluation (Precision@k, MRR, nDCG, Faithfulness)
│       ├── graph_retriever.py     # SPARQL query generation and execution
│       └── pipelines/
│           ├── run_ingestion.py       # Full corpus ingestion (SemanticChunker)
│           └── run_ingestion_test.py  # Test corpus ingestion (fast, no API calls)
├── storage/                       # ChromaDB persistent directory (created at runtime)
├── tests/
│   ├── test_api.py                # Endpoint smoke tests (FastAPI TestClient)
│   ├── test_rag.py                # RAG pipeline integration tests
│   └── test_kg.py                 # Knowledge graph / SPARQL integration tests
├── .env.example
├── .gitignore
├── Makefile                       # All development commands
├── pyproject.toml
└── README.md                      # ← you are here
```

---

---

## How It Works

### Agent Graph

Every request flows through a LangGraph `StateGraph` compiled with an `InMemorySaver` checkpointer (multi-turn memory per `thread_id`):

```
START
  │
  ▼
classifier_node   ← Gemini, Pydantic structured output → 5-category intent
  │
  ├── domainSearch / summarize / compare / draftDocument → rag_node
  └── generalSearch ─────────────────────────────────────────────────────┐
                                                                         │
rag_node  ← adaptive query transformation + dual retrieval               │
  │         (ChromaDB MMR + GraphDB SPARQL)                              │
  ├── domainSearch   → domain_search_node  (ReAct, 6 tools)              │
  ├── summarize      → summarize_node      (ReAct, 4 tools)              │
  ├── compare        → compare_node        (ReAct, 4 tools)              │
  └── draftDocument  → draft_document_node (ReAct, 1 tool)               │
                                                                         │
All specialist nodes → validate_node  ◄─────────────────────────────────┘
                            │
               ┌────────────┼──────────────────────────┐
               │            │                          │
         [is_valid]  [retry < 3, legal]   [retry ≥ 3 or general]
               │            │                          │
              END         rag_node              fallback_node
                        (retry loop)        (Gemini Google Search)
                                                       │
                                                      END
```

### LLMs

| Model | Provider | Role |
|---|---|---|
| `GOOGLE_GEMINI_MODEL` (default: `gemini-2.5-flash-lite`) | Google Gemini | Classification, generation, SPARQL generation, self-critique, fallback |
| `llama-3.1-8b-instant` | Groq | Dynamic-K selection, query transformation analysis, general Q&A |
| `gemini-embedding-001` | Google | Semantic chunking (ingestion) + vector retrieval |

### Query Transformation

Before vector retrieval, `query_transformer.py` uses Groq to select one of three strategies:

| Strategy | When Used | What Happens |
|---|---|---|
| **DIRECT** | Query is clear and specific | Used as-is for retrieval |
| **HyDE** | Query is vague or too short (e.g. `"vacaciones"`) | Gemini generates a hypothetical answer document; its embedding is used for retrieval — dramatically improves match quality |
| **DECOMPOSITION** | Query has 2+ independent sub-questions | Split into atomic sub-queries; each retrieved independently; results deduplicated |

### Retrieval

`retriever.py` uses **dynamic-K selection**: Groq reads the query and decides how many chunks (1–10) are needed to answer it. Retrieval uses **MMR** (Maximal Marginal Relevance) — re-ranks the candidate pool so returned chunks are both *relevant* and *diverse*, avoiding near-duplicate passages.

### The 10 Tools (Least-Privilege Model)

Each specialist node receives only the tools relevant to its task:

| Tool | Node Access | Description |
|---|---|---|
| `list_laws_by_topic` | domain, summarize, compare | Semantic similarity search grouped by source document |
| `search_by_law_number` | domain, compare | Metadata filter by law identifier (e.g. `"Ley 789"`, `"CST"`) |
| `get_article_text` | domain, summarize, compare | Fetches exact article text via semantic search + regex |
| `get_document_metadata` | summarize | Returns chunk/page metadata without loading content |
| `find_related_jurisprudence` | domain | Semantic search filtered for legal judgment terminology |
| `verify_citation_exists` | validate | Confirms a cited law + article exists in ChromaDB |
| `check_law_vigency` | validate | Looks up `LAW_VIGENCY_DB` for major Colombian laws |
| `query_knowledge_graph` | domain, summarize, compare | Translates question to SPARQL via LLM; executes against GraphDB (supplementary structured data from the OWL ontology) |
| `evaluar_riesgo_laboral` | domain | Scores a scenario against known labor abuse patterns |
| `generar_documento_legal` | draft | Generates formatted petitions and contract drafts |

### Self-Critique Loop

`validate_node` evaluates every specialist answer on three independent dimensions:

1. **`addresses_question`** — Does the answer cover all aspects of the question?
2. **`is_complete`** — Is it sufficiently detailed?
3. **`is_grounded`** — Does it cite legal articles, laws, or KG data from the retrieved context?

`is_valid = True` only if **all three** pass. On failure the system retries (up to `MAX_ATTEMPTS = 3`), augmenting the query with the critique hint to fetch better context. After three failures, `fallback_node` activates Gemini's built-in Google Search grounding.

### Ingestion Pipeline

```
PDF files
   │
   ▼
PyPDFLoader → raw text per page
   │
   ▼
limpiar_texto() → removes SUIN-Juriscol artifacts, URLs, control chars, duplicate whitespace
   │
   ▼
SemanticChunker (gemini-embedding-001, percentile-85 threshold)
   │             preserves legal article boundaries better than fixed-size splits
   │
   ▼
Metadata tagging → chunk_id, doc_id (source file), page number
   │
   ▼
Chroma.from_documents() → embeds each chunk (task_type=RETRIEVAL_DOCUMENT)
   │
   ▼
ChromaDB (persisted to CHROMA_DIR)
```

---

## Local setup

### Prerequisites

- Python 3.11 or newer
- `pip` / `venv` (standard library)
- Google Gemini API key (for embeddings and Gemini LLM)
- Groq API key (for Llama LLM)
- GraphDB running at `localhost:7200` *(optional — only needed for KG queries)*

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
# Edit .env with your API keys and paths.
```

Minimum required `.env`:

```env
# LLM providers
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key

# Server
HOST=0.0.0.0
PORT=8000
ENV=dev

# Vector DB
VECTOR_DB=chroma
CHROMA_DIR=./db_chroma

# Embeddings (local fallback for dev, not used in production flow)
EMBEDDINGS_PROVIDER=local
EMBEDDINGS_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### 5 — Run the ingestion pipeline

Both modes require `GOOGLE_API_KEY` set in `.env`.

#### 5a — Full corpus (production)

Processes all PDFs in `app/data/` using **SemanticChunker**. Writes to `./db_chroma`. Use for the full Colombian labor law corpus.

```bash
make ingest
# or: python -m app.rag.pipelines.run_ingestion
```

#### 5b — Test corpus (fast, no API chunking)

Processes only PDFs in `app/data/test/` using `RecursiveCharacterTextSplitter` — no API calls for chunking. Completes in seconds. Writes to `./db_chroma_test`.

```bash
make ingest-test
# or: python -m app.rag.pipelines.run_ingestion_test
```

After test ingestion, point the server to the test index:

```ini
# .env
CHROMA_DIR=./db_chroma_test
```

### 6 — Start the server

```bash
make serve
# or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000`
- Interactive docs (dev only): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

---

## Running Tests

```bash
# Full test suite
make test
# or: pytest -v

# Knowledge graph / SPARQL / ontology tests only (requires GraphDB running)
make test-kg
# or: pytest tests/test_kg.py -v

# With coverage
pytest -v --cov=app
```

### Test coverage

| File | What is tested |
|---|---|
| `tests/test_api.py` | Endpoint smoke tests: `GET /health`, `POST /chat` validation, error handling |
| `tests/test_rag.py` | RAG pipeline integration: retrieval, query transformation, context injection |
| `tests/test_kg.py` | Knowledge graph integration (detailed below) |

### `test_kg.py` — Knowledge Graph & Ontology Tests

Covers the full KG stack in three layers:

**`TestGraphDBConnector`** — SPARQL connector unit tests (all mocked, no live GraphDB required):
- Singleton creation and reuse of `SPARQLWrapper` endpoint
- Credential injection when `GRAPHDB_USERNAME` / `GRAPHDB_PASSWORD` are set
- `execute_sparql` correctly parses JSON bindings into plain `list[dict]`
- `execute_sparql` returns `[]` and logs gracefully on connection errors

**`TestGraphRetriever`** — SPARQL generation, template selection, and result formatting:
- `format_graph_results` returns `""` for empty results
- Formatted output contains `CONTEXTO ESTRUCTURADO DEL KNOWLEDGE GRAPH` header with rows numbered
- Ontology namespace URIs (e.g. `http://example.org/contratos#Empleado`) are stripped to `:Empleado`
- `_select_template` matches `"all_employees"`, `"all_contracts"`, `"all_employers"`, `"ontology_classes"` by keyword, returns `None` for unmatched queries
- `generate_sparql` uses a pre-built template (no LLM call) when a keyword match is found
- `generate_sparql` calls the LLM for open-ended questions and strips markdown fences from the response
- `generate_sparql` returns `None` when the LLM responds with `"NO_SPARQL"` (non-SPARQL question)
- `query_graph` returns `source="graphdb_disabled"` when `GRAPHDB_ENABLED=false`
- End-to-end `query_graph` pipeline: template → `execute_sparql` → `format_graph_results` → structured result

**`TestKnowledgeGraphTool`** — `query_knowledge_graph` LangChain `@tool`:
- Returns `source="graphdb_disabled"` and `total_results=0` when `GRAPHDB_ENABLED=false`
- Correctly delegates to `query_graph` and surfaces structured results
- Catches any exception from `query_graph` and returns a safe error dict instead of raising

---

## Linting and Formatting

```bash
make lint      # ruff check
make format    # ruff format
```

Pre-commit hooks run both automatically on every `git commit`.

---

## API Reference

### `GET /health`

Liveness probe. Returns `200 OK` when the server is up.

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

```json
{ "ok": true }
```

---

### `POST /chat`

Ask the Colombian labor law assistant.

#### Request body

```json
{
  "question": "string (max 2000 chars, required)",
  "conversation_id": "string | null",
  "max_citations": "integer (1–20) | null"
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
    "intent": "domainSearch | summarize | compare | draftDocument | generalSearch | null",
    "top_k": "integer | null",
    "vector_db": "string",
    "llm_provider": "string",
    "query_transform": {
      "strategy": "direct | hyde | decomposition",
      "reason": "string",
      "effective_queries": ["string"]
    }
  }
}
```

#### curl examples

```bash
# Liveness
curl -s http://localhost:8000/health

# Labor law question (triggers RAG + ReAct + self-critique)
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué pasa si me despiden sin justa causa?"}' \
  | python3 -m json.tool

# Vacation rights (expect citations from CST)
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuántos días de vacaciones tiene un trabajador en Colombia?"}' \
  | python3 -m json.tool

# General question (routes to generalSearch, no citations)
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué es la inteligencia artificial?"}' \
  | python3 -m json.tool

# Multi-turn conversation (pass conversation_id to retain context)
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Y si tengo contrato a término fijo?", "conversation_id": "session-abc"}' \
  | python3 -m json.tool

# Validation error (question too short → 422)
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "hola"}' | python3 -m json.tool
```

---

## Environment Variables

### Server

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind host for uvicorn |
| `PORT` | `8000` | Bind port for uvicorn |
| `ENV` | `dev` | Runtime environment (`dev` or `prod`) |

### Corpus & Vector DB

| Variable | Default | Description |
|---|---|---|
| `DATA_DIR` | `./data` | Directory containing source corpus files (PDF/HTML/TXT) for ingestion |
| `VECTOR_DB` | `chroma` | Vector database backend (only `chroma` supported) |
| `CHROMA_DIR` | `./db_chroma` | ChromaDB persistent directory. Use `./db_chroma_test` for the lightweight test index |

### LLM

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `mock` | `mock` / `gemini` / `groq` / `local` |
| `GOOGLE_API_KEY` | *(empty)* | Google API key. Required for `LLM_PROVIDER=gemini` and for embeddings (`gemini-embedding-001`) |
| `GOOGLE_GEMINI_MODEL` | `gemini-2.5-flash-lite` | Gemini model used by all Gemini nodes. Options: `gemini-2.5-flash-lite`, `gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-2.5-pro` |
| `GROQ_API_KEY` | *(empty)* | Groq API key. Required for `LLM_PROVIDER=groq` (dynamic-K selection, query transformation, general Q&A) |

### Embeddings

| Variable | Default | Description |
|---|---|---|
| `EMBEDDINGS_PROVIDER` | `local` | Embeddings backend. `local` uses sentence-transformers as fallback (no API key needed) |
| `EMBEDDINGS_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Multilingual sentence-transformers model used when `EMBEDDINGS_PROVIDER=local` |

### Retrieval

| Variable | Default | Description |
|---|---|---|
| `RETRIEVAL_STRATEGY` | `mmr` | `mmr` (Maximal Marginal Relevance — balances relevance + diversity) or `similarity` (plain cosine) |
| `MMR_FETCH_K` | `10` | Candidate pool size for MMR re-ranking. The retriever fetches this many docs first, then re-ranks. Higher values improve diversity at a small latency cost |
| `MMR_LAMBDA` | `0.5` | MMR diversity weight (0.0 = max diversity, 1.0 = max relevance) |

### Knowledge Graph (GraphDB)

| Variable | Default | Description |
|---|---|---|
| `GRAPHDB_URL` | `http://localhost:7200` | Base URL of the GraphDB instance |
| `GRAPHDB_REPOSITORY` | `labor-law` | Repository name containing the OWL ontology and instances |
| `GRAPHDB_USERNAME` | *(empty)* | GraphDB basic auth username. Leave empty if auth is disabled |
| `GRAPHDB_PASSWORD` | *(empty)* | GraphDB basic auth password. Leave empty if auth is disabled |
| `GRAPHDB_ENABLED` | `true` | Set to `false` to disable KG retrieval and rely only on the vector store |

### Evaluation

| Variable | Default | Description |
|---|---|---|
| `EVAL_ENABLED` | `false` | When `true`, computes retrieval + generation quality metrics (Precision@k, MRR, nDCG@k, Relevance, Faithfulness) via LLM-as-a-judge after each request. Adds extra LLM calls; keep `false` in production |

### LangSmith (observability)

| Variable | Default | Description |
|---|---|---|
| `LANGCHAIN_TRACING_V2` | `false` | Set to `true` to enable LangSmith request tracing |
| `LANGCHAIN_ENDPOINT` | `https://api.smith.langchain.com` | LangSmith API endpoint |
| `LANGCHAIN_API_KEY` | *(empty)* | LangSmith API key |
| `LANGCHAIN_PROJECT` | `AgenticLawyer` | LangSmith project name shown in the dashboard |

---

## Implemented Features

### Core Pipeline
- [x] LangGraph `StateGraph` with 8 nodes and conditional routing
- [x] 5-category intent classification via Gemini with Pydantic structured output
- [x] Adaptive query transformation: DIRECT, HyDE, DECOMPOSITION (Groq)
- [x] Dynamic-K chunk selection (1–10) based on query complexity (Groq)
- [x] MMR retrieval from ChromaDB for relevant, diverse context
- [x] SPARQL-based knowledge graph retrieval via GraphDB (supplementary structured data)
- [x] 4 specialist ReAct nodes with least-privilege tool sets
- [x] Self-critique reflection loop (`validate_node`, up to 3 retries with improvement hints)
- [x] Fallback to Gemini Google Search grounding after failed retries

### Tools & Data Access
- [x] 10 `@tool` functions: law/article lookup, jurisprudence, citation verification, vigency check, KG query, risk assessment, document drafting
- [x] `LAW_VIGENCY_DB` — hardcoded vigency registry for major Colombian laws
- [x] Full PDF ingestion pipeline: PyPDFLoader → `limpiar_texto()` → SemanticChunker → ChromaDB
- [x] Fast test ingestion pipeline (no Gemini API calls, `RecursiveCharacterTextSplitter`)

### API & Infrastructure
- [x] FastAPI backend with `GET /health` and `POST /chat`
- [x] Pydantic v2 request/response validation with execution trace in every response
- [x] Multi-turn conversation memory via `InMemorySaver` checkpointer (`thread_id`)
- [x] LLM-as-judge evaluation metrics: Precision@k, MRR, nDCG@k, Relevance, Faithfulness
- [x] ruff linting + formatting with pre-commit hooks
