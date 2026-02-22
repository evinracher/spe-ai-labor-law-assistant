"""
app/rag/llm.py
---------------
LLM integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.api.schemas import Citation, ChatResponse, Trace
from app.core.config import settings

if TYPE_CHECKING:
    from app.core.config import Settings
    
from langchain_groq import ChatGroq
    
LLM_API_KEY = settings.GROQ_API_KEY if settings.LLM_PROVIDER == "groq" else settings.GEMINI_API_KEY

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    api_key=LLM_API_KEY,
)


def ask_llm(question: str, settings: "Settings") -> ChatResponse:
    """
    Generate an LLM response
    
    Args:
        question:  User question string (already validated by Pydantic).
        settings:  Application settings (used for trace metadata).

    Returns:
        A fully populated ChatResponse (ok=True, no real retrieval performed).
    """
    import uuid

    request_id = str(uuid.uuid4())

    # TODO: handle out of context in RAG level
    response = llm.invoke(question)
    
    answer_text = response.content
    citations = []
    intent = ""
    top_k = 4

    return ChatResponse(
        ok=True,
        request_id=request_id,
        answer=answer_text,
        citations=citations,
        trace=Trace(
            intent=intent,
            top_k=top_k,
            vector_db=settings.VECTOR_DB,
            llm_provider=settings.LLM_PROVIDER,
        ),
    )
