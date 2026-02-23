"""
app/api/routes.py
-----------------
FastAPI router registering all public endpoints.

Current endpoints
-----------------
GET  /health  →  liveness probe
POST /chat    →  RAG chatbot (mock implementation for milestone 1)

Future endpoints (TODOs)
------------------------
TODO (milestone 2): POST /ingest  →  trigger corpus ingestion pipeline from DATA_DIR.
TODO (milestone 4): GET  /chat/{conversation_id}/history  →  conversation turns.
TODO (milestone 5): DELETE /chat/{conversation_id}  →  clear conversation memory.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from app.api.schemas import ChatRequest, ChatResponse
from app.core.config import settings
from app.rag.agents import ask_chat
from app.rag.mock import mock_rag_answer

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------ /health


@router.get(
    "/health",
    summary="Liveness probe",
    description="Returns `{ok: true}` when the server is up and accepting requests.",
    tags=["ops"],
)
async def health() -> dict[str, bool]:
    """Simple liveness check. No database or LLM connectivity is verified here.

    TODO (milestone 3): extend to a readiness check that verifies ChromaDB is
    reachable and at least one collection exists.
    """
    return {"ok": True}


# -------------------------------------------------------------------- /chat


@router.post(
    "/chat",
    summary="Ask the Colombian labor law assistant",
    description=(
        "Accepts a question in Spanish and returns an answer grounded in the "
        "local corpus of Colombian labor law documents, together with source "
        "citations and an execution trace.\n\n"
        "**Milestone 1 (current):** returns a deterministic mock response. "
        "Real retrieval and LLM generation are not yet implemented."
    ),
    response_model=ChatResponse,
    response_model_exclude_none=False,
    tags=["chat"],
)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    """
    Main chat endpoint.

    Routing logic (grows with milestones):
    - LLM_PROVIDER == "mock"  →  mock_rag_answer (current)
    - LLM_PROVIDER == "gemini" →  TODO: real_rag_answer with Gemini
    - LLM_PROVIDER == "groq"  →  TODO: real_rag_answer with Groq
    - LLM_PROVIDER == "local" →  TODO: real_rag_answer with local Ollama/llama.cpp

    TODO (milestone 3): replace the mock branch with a real LangGraph invocation:
        from app.rag.pipeline import rag_graph
        result = await rag_graph.ainvoke(
            {"question": body.question, "conversation_id": body.conversation_id,
             "max_citations": body.max_citations or settings.DEFAULT_TOP_K},
            config={"configurable": {"thread_id": body.conversation_id}},
        )
        return result
    """
    logger.debug(
        "POST /chat | provider=%s | q_len=%d",
        settings.LLM_PROVIDER,
        len(body.question),
    )

    if settings.LLM_PROVIDER == "mock":
        return mock_rag_answer(question=body.question, settings=settings)

    return ask_chat(question=body.question, settings=settings)
