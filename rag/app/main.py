"""
app/main.py
-----------
Application factory and entry point for the Colombian Labor Law RAG backend.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Or via the helper script in pyproject.toml:
    python -m app.main
"""

from __future__ import annotations

import logging
import os
import sys

from app.core.config import settings

# Set LangChain environment variables before importing any LangChain modules
os.environ['LANGCHAIN_TRACING_V2'] = settings.LANGCHAIN_TRACING_V2
os.environ['LANGCHAIN_ENDPOINT'] = settings.LANGCHAIN_ENDPOINT
os.environ['LANGCHAIN_API_KEY'] = settings.LANGCHAIN_API_KEY
os.environ['LANGCHAIN_PROJECT'] = settings.LANGCHAIN_PROJECT

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.chroma import get_chroma_client

# ---------------------------------------------------------------------------
# Logging — basic config (replace with structlog/loguru in production)
# ---------------------------------------------------------------------------
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if settings.ENV == "dev" else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

# Enable debug logging for LangSmith and LangChain to capture trace errors
logging.getLogger('langsmith').setLevel(logging.DEBUG)
logging.getLogger('langchain').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Colombian Labor Law RAG Assistant",
    description=(
        "Strict Retrieval-Augmented Generation chatbot for Colombian labor law. "
        "Answers are generated **only** from an approved local corpus. "
        "If the requested information is not in the corpus, the system replies: "
        "'No aparece en el contexto.' — never hallucinates.\n\n"
        "**Status:** Milestone 1 — Mock API only. "
        "Ingestion, retrieval and LLM integration are pending."
    ),
    version="0.1.0",
    docs_url="/docs" if settings.ENV == "dev" else None,
    redoc_url="/redoc" if settings.ENV == "dev" else None,
    openapi_url="/openapi.json" if settings.ENV == "dev" else None,
)


# ---------------------------------------------------------------------------
# CORS — permissive for local development.
# TODO (milestone 5): tighten allowed origins for any networked deployment.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "dev" else [],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(router, prefix="")

# TODO (milestone 2): register ingestion router
# from app.api.ingest_routes import ingest_router
# app.include_router(ingest_router, prefix="/ingest")


# ---------------------------------------------------------------------------
# Startup / shutdown events
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def on_startup() -> None:  # (async is intentional)
    logger.info(
        "Starting Colombian Labor Law RAG backend | env=%s | provider=%s | vector_db=%s",
        settings.ENV,
        settings.LLM_PROVIDER,
        settings.VECTOR_DB,
    )
    logger.info("CHROMA_DIR=%s | DATA_DIR=%s", settings.CHROMA_DIR, settings.DATA_DIR)

    chroma_client = get_chroma_client()
    collection = chroma_client.get_or_create_collection(name="labor_law")

    app.state.chroma_client = chroma_client
    app.state.collection = collection

    logger.info("ChromaDB ready | collection=%s | docs=%d", collection.name, collection.count())
    # TODO (milestone 3): warm up sentence-transformers model on startup.


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Shutting down Colombian Labor Law RAG backend.")
    # TODO (milestone 2): flush any pending ChromaDB writes.


# ---------------------------------------------------------------------------
# Dev convenience runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENV == "dev"),
        log_level="debug" if settings.ENV == "dev" else "info",
    )
