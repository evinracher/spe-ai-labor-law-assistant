# Knowledge Graph RAG Integration

## Overview

This document describes the Knowledge Graph (KG) retrieval layer added to the existing RAG pipeline. The system now combines **vector-based semantic retrieval** (ChromaDB) with **structured knowledge retrieval** (GraphDB via SPARQL) to produce grounded answers that leverage both unstructured legal documents and structured ontological data.

## Architecture

```
User Question
     │
     ▼
┌─────────────┐
│ classifier  │  (intent detection)
└─────┬───────┘
      │
      ▼
┌─────────────┐    ┌──────────────┐    ┌──────────────────┐
│  rag_node   │───▶│ Vector Store │    │   GraphDB        │
│ (retrieval) │    │  (ChromaDB)  │    │ (SPARQL/Ontology)│
└─────┬───────┘    └──────────────┘    └──────────────────┘
      │                   │                      │
      │     contexto_legal (combined)            │
      ▼◀─────────────────────────────────────────┘
┌─────────────────┐
│ specialist node │  (domain_search / summarize / compare / draft)
│  + KG tool      │  (can invoke query_knowledge_graph on demand)
└─────┬───────────┘
      ▼
┌─────────────┐
│  validate   │  (self-critique)
└─────────────┘
```

### Dual retrieval in `rag_node`

The `rag_node` now performs **two** retrieval passes:

1. **Vector retrieval** – unchanged adaptive query transformation + ChromaDB search.
2. **Graph retrieval** – the user question is translated to SPARQL (via LLM or predefined templates), executed against GraphDB, and the results are formatted as structured context.

Both context blocks are concatenated and passed downstream as `contexto_legal`.

### Agent-level KG access

Each specialist agent (domain_search, summarize, compare) also has access to the `query_knowledge_graph` tool, so it can issue **on-demand** SPARQL queries when the pre-fetched context is insufficient. The agent decides autonomously when to use vector tools vs. the KG tool.

## Files Added

| File | Purpose |
|------|---------|
| `app/db/graphdb.py` | GraphDB SPARQL connector — singleton `SPARQLWrapper`, `execute_sparql()` helper |
| `app/rag/graph_retriever.py` | KG retrieval layer — SPARQL generation (LLM + templates), query execution, result formatting |

## Files Modified

| File | Changes |
|------|---------|
| `app/core/config.py` | Added `GRAPHDB_URL`, `GRAPHDB_REPOSITORY`, `GRAPHDB_ENABLED` settings |
| `app/rag/tools.py` | Added `query_knowledge_graph` tool; included in `TOOLS_LIST` and `TOOLS_DICT` |
| `app/rag/agents.py` | Added `contexto_grafo` to `GraphState`; graph retrieval in `rag_node`; KG tool in all specialist tool sets; graph context in specialist node prompts |
| `app/rag/prompts.py` | Updated `DOMAIN_SEARCH_PROMPT`, `SUMMARIZE_PROMPT`, `COMPARE_PROMPT` to document KG availability |
| `app/main.py` | Added GraphDB connectivity check at startup |
| `pyproject.toml` | Added `SPARQLWrapper>=2.0.0` and `rdflib>=7.0.0` dependencies |
| `.env.example` | Added `GRAPHDB_URL`, `GRAPHDB_REPOSITORY`, `GRAPHDB_ENABLED` variables |

## Configuration

Add to your `.env`:

```env
GRAPHDB_URL=http://localhost:7200
GRAPHDB_REPOSITORY=labor-law
GRAPHDB_ENABLED=true
```

Set `GRAPHDB_ENABLED=false` to disable KG retrieval and fall back to vector-only mode.

## How Graph Retrieval Is Triggered

1. **Automatically** in `rag_node`: every legal-intent query triggers a SPARQL query alongside vector retrieval. If the question maps to a predefined template (e.g., "lista todos los empleados"), the template is used directly without an LLM call. Otherwise, the LLM generates a SPARQL query from the ontology schema.

2. **On-demand** by specialist agents: the `query_knowledge_graph` tool is available to `domain_search_agent`, `summarize_agent`, and `compare_agent`. They can call it when they need structured data (employees, contracts, salaries, benefits) that the vector store cannot provide.

3. **Graceful degradation**: if GraphDB is unreachable or the query fails, the system falls back to vector-only retrieval without errors.

## Ontology

The ontology (`ontology/labor-law-ontology.ttl`) must be loaded into the GraphDB repository. It models:

- **Personas**: Empleado, Empleador, Contratista, Contratante
- **Contratos**: ContratoLaboral, ContratoPrestacionServicios
- **Propiedades**: salarios, puestos, departamentos, jornadas laborales, beneficios
- **Relaciones**: empleaA, tieneContrato, ocupaPuesto, perteneceADepartamento, etc.
