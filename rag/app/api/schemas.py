"""
app/api/schemas.py
------------------
Pydantic v2 request/response models for the Colombian Labor Law RAG API.
These models define the contract between this backend and the React frontend.

Changing field names here is a BREAKING CHANGE for the frontend — coordinate before
modifying.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# ============================================================== Request models


class ChatRequest(BaseModel):
    """Body for POST /chat."""

    question: str = Field(
        ...,
        max_length=2_000,
        description="User question in Spanish about Colombian labor law.",
        examples=["¿Cuántos días de vacaciones tiene un trabajador en Colombia?"],
    )
    conversation_id: str | None = Field(
        default=None,
        description=(
            "Optional ID to group turns into a conversation. "
            # TODO (milestone 3): wire to LangGraph memory / checkpointing.
            "Currently ignored — conversation memory is not yet implemented."
        ),
    )
    max_citations: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Maximum number of citations to return. Defaults to server setting.",
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "La pregunta no puede estar vacía. "
                "Por favor escribe una pregunta sobre derecho laboral colombiano."
            )
        return v.strip()


# ============================================================= Response models


class Citation(BaseModel):
    """A single retrieved chunk that supports the generated answer."""

    source: str = Field(
        ...,
        description="File name or URL of the source document.",
        examples=["CST_codigo_sustantivo_trabajo.pdf"],
    )
    page: int | None = Field(
        default=None,
        description="Page number within the source document, if applicable.",
    )
    chunk_id: str | None = Field(
        default=None,
        description="Internal chunk identifier in the vector store.",
    )
    snippet: str = Field(
        ...,
        description="Verbatim or near-verbatim text excerpt from the source.",
    )


class Trace(BaseModel):
    """Minimal execution trace for debugging and explainability."""

    intent: str | None = Field(
        default=None,
        description="Classified intent of the question (e.g. 'vacaciones', 'salario').",
        # TODO (milestone 2): populate via LangGraph intent-classification node.
    )
    top_k: int | None = Field(
        default=None,
        description="Number of chunks retrieved from the vector store.",
        # TODO (milestone 2): populate from retrieval step.
    )
    vector_db: str = Field(
        ...,
        description="Vector database backend used for retrieval.",
    )


class ChatResponse(BaseModel):
    """Full response returned by POST /chat."""

    ok: bool = Field(..., description="Whether the request was processed successfully.")
    request_id: str = Field(
        ...,
        description="Unique UUID for this request, useful for tracing logs.",
    )
    answer: str = Field(
        ...,
        description=(
            "Generated answer in Spanish. "
            "If the information is not in the corpus, equals 'No aparece en el contexto.'"
        ),
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description=(
            "Source chunks that support the answer. "
            "Empty when the answer is 'No aparece en el contexto.'."
        ),
    )
    trace: Trace = Field(
        ...,
        description="Execution trace for debugging.",
    )
