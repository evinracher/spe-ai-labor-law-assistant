"""
app/rag/llm.py
---------------
LLM integration module to be used by the RAG.

This module is configurable thought the env variables and support integration with Groq and Gemini LLM provider,
using the langchain implementation. You need to setup your proper API to use it.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from app.api.schemas import ChatResponse, Trace
from app.core.config import settings

if TYPE_CHECKING:
    from app.core.config import Settings


_llm: BaseChatModel | None = None


def get_llm() -> BaseChatModel:
    """Return the LLM singleton for the configured provider, creating it on first call."""
    global _llm
    if _llm is None:
        if settings.LLM_PROVIDER == "groq":
            _llm = ChatGroq(
                model="llama-3.1-8b-instant",
                temperature=0.2,
                api_key=settings.GROQ_API_KEY,
            )
        elif settings.LLM_PROVIDER == "gemini":
            _llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                temperature=0.2,
                google_api_key=settings.GOOGLE_API_KEY,
            )
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER for get_llm(): '{settings.LLM_PROVIDER}'")
    return _llm


def ask_llm(question: str, settings: Settings) -> ChatResponse:
    """
    Generate an LLM response

    Args:
        question:  User question string (already validated by Pydantic).
        settings:  Application settings (used for trace metadata).

    Returns:
        A fully populated ChatResponse (ok=True).
    """
    request_id = str(uuid.uuid4())

    # TODO: handle out of context in RAG level
    response = get_llm().invoke(question)

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
