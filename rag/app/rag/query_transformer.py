"""
app/rag/query_transformer.py
-----------------------------
Adaptive Query Transformation module for the SPE AI Labor Law Assistant.

This module analyzes each incoming user query and dynamically selects the most
appropriate transformation strategy to improve vector retrieval quality:

  - DIRECT       → Query is clear and self-contained; use as-is.
  - HYDE         → Query is vague or short; generate a Hypothetical Document
                   Embedding (HyDE) to guide semantic search.
  - DECOMPOSITION → Query has multiple intents or logical dependencies; split
                    into atomic sub-queries processed independently.

Usage::

    transformer = QueryTransformer(fast_llm=groq_llm, strong_llm=gemini_llm)
    result = transformer.transform("¿Qué pasa si me despiden sin justa causa y no me pagan?")

    # result.strategy       → TransformStrategy.DECOMPOSITION
    # result.effective_queries → ["¿Qué ocurre con el despido sin justa causa?",
    #                             "¿Cuáles son las consecuencias de no pagar la liquidación?"]
    # result.strategy_reason  → "Query contains two independent legal sub-questions..."
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# ====================================================================
# Strategy Enum
# ====================================================================


class TransformStrategy(str, Enum):
    """Available query transformation strategies."""

    DIRECT = "direct"
    HYDE = "hyde"
    DECOMPOSITION = "decomposition"


# ====================================================================
# Internal LLM structured-output model
# ====================================================================


class _QueryAnalysis(BaseModel):
    """Structured output produced by the classification LLM."""

    strategy: Literal["direct", "hyde", "decomposition"] = Field(
        description="The retrieval strategy that best fits this query."
    )
    reason: str = Field(description="One or two sentences explaining why this strategy was chosen.")
    sub_queries: list[str] = Field(
        default_factory=list,
        description=(
            "When strategy is 'decomposition', the list of atomic sub-queries in Spanish. "
            "Empty for 'direct' and 'hyde'."
        ),
    )


# ====================================================================
# Public result model
# ====================================================================


class QueryTransformResult(BaseModel):
    """Full traceability record for a single query transformation."""

    original_query: str = Field(description="The original user query, unmodified.")
    strategy: TransformStrategy = Field(description="The transformation strategy that was applied.")
    strategy_reason: str = Field(description="Brief explanation of why the strategy was selected.")
    effective_queries: list[str] = Field(
        description=(
            "The actual queries used for vector retrieval. "
            "One item for DIRECT/HyDE; multiple items for DECOMPOSITION."
        )
    )
    hypothetical_document: str | None = Field(
        default=None,
        description="The hypothetical document generated when strategy is HyDE; None otherwise.",
    )


# ====================================================================
# Prompts
# ====================================================================

_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a retrieval strategy expert for a Colombian Labor Law RAG system.

Your task: classify the user's query into exactly one retrieval strategy.

STRATEGIES:
- "direct": The query is clear, specific, and self-contained. Use it as-is for vector search.
  → Good examples: "¿Cuántos días de vacaciones tiene un empleado?", "Artículo 64 del CST", "¿Qué es la prima de servicios?"

- "hyde": The query is very short (fewer than 5 meaningful words), vague, ambiguous, or lacks
  enough context for a meaningful embedding search.
  → Good examples: "vacaciones", "despido", "qué dice la ley", "contrato"

- "decomposition": The query contains TWO OR MORE distinct searchable sub-questions, logical
  conditions ("si... entonces..."), comparisons ("diferencia entre X e Y"), or multi-step
  reasoning that cannot be resolved with a single vector search.
  → Good examples:
    "¿Qué pasa si me despiden sin justa causa y además no me pagan la liquidación?"
    "Compara el contrato a término fijo con el indefinido y explica cuándo aplica cada uno."
    "¿Cuáles son mis derechos si estoy en período de prueba y me accidento en el trabajo?"

RULES:
- Prefer "direct" when the query is already specific and semantically rich.
- Use "hyde" only for genuinely short or underspecified queries.
- Use "decomposition" only when you can identify AT LEAST 2 distinct sub-questions.
- When strategy is "decomposition", provide Spanish sub-queries in sub_queries[], each fully
  self-contained and independently searchable.
- Always answer in valid JSON matching the requested schema.
""",
        ),
        ("user", "Query: {question}"),
    ]
)

_HYDE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Eres un experto en derecho laboral colombiano con acceso a todo el corpus normativo.

El usuario ha realizado una búsqueda vaga o muy corta. Tu tarea es generar un fragmento de
documento hipotético (2-3 párrafos) que represente el tipo de contenido que probablemente
respondería su consulta dentro del Código Sustantivo del Trabajo o la normatividad laboral
colombiana relevante.

Escribe en español usando terminología jurídica precisa. NO menciones que este texto es
hipotético; escríbelo como si fuera un fragmento real de un documento legal colombiano.""",
        ),
        ("user", "Consulta del usuario: {question}"),
    ]
)


# ====================================================================
# QueryTransformer
# ====================================================================


class QueryTransformer:
    """
    Analyzes a natural language query and applies the best transformation
    strategy (DIRECT, HyDE, or DECOMPOSITION) prior to vector retrieval.

    Args:
        fast_llm:   A LangChain chat model used for classification (e.g., Groq Llama).
                    Must support `with_structured_output`.
        strong_llm: A LangChain chat model used for HyDE document generation (e.g., Gemini).

    Example::

        transformer = QueryTransformer(fast_llm=groq_llm, strong_llm=gemini_llm)
        result = transformer.transform("liquidación")
        # → strategy=HYDE, effective_queries=[<hypothetical document>]
    """

    _RED = "\033[91m"
    _RESET = "\033[0m"

    def __init__(self, fast_llm, strong_llm) -> None:
        self._analysis_chain = _ANALYSIS_PROMPT | fast_llm.with_structured_output(_QueryAnalysis)
        self._hyde_chain = _HYDE_PROMPT | strong_llm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transform(self, question: str) -> QueryTransformResult:
        """
        Analyze *question* and return a :class:`QueryTransformResult` with the
        selected strategy and the list of effective queries to use for retrieval.
        """
        print(f"{self._RED}[QueryTransformer] Analyzing: {question[:80]}...{self._RESET}")

        analysis: _QueryAnalysis = self._analysis_chain.invoke({"question": question})
        strategy = TransformStrategy(analysis.strategy)

        print(
            f"{self._RED}[QueryTransformer] Strategy={strategy.value} | "
            f"Reason={analysis.reason[:80]}{self._RESET}"
        )

        if strategy == TransformStrategy.DIRECT:
            return self._direct(question, analysis.reason)

        if strategy == TransformStrategy.HYDE:
            return self._hyde(question, analysis.reason)

        # DECOMPOSITION
        return self._decompose(question, analysis.reason, analysis.sub_queries)

    # ------------------------------------------------------------------
    # Private strategy builders
    # ------------------------------------------------------------------

    def _direct(self, question: str, reason: str) -> QueryTransformResult:
        return QueryTransformResult(
            original_query=question,
            strategy=TransformStrategy.DIRECT,
            strategy_reason=reason,
            effective_queries=[question],
        )

    def _hyde(self, question: str, reason: str) -> QueryTransformResult:
        """Generate a hypothetical document and use it as the retrieval query."""
        response = self._hyde_chain.invoke({"question": question})
        raw = response.content if hasattr(response, "content") else str(response)

        # Gemini sometimes returns a list of content blocks
        if isinstance(raw, list):
            raw = " ".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in raw)

        hypo_doc: str = raw.strip()
        print(
            f"{self._RED}[QueryTransformer] HyDE document generated "
            f"({len(hypo_doc)} chars){self._RESET}"
        )

        return QueryTransformResult(
            original_query=question,
            strategy=TransformStrategy.HYDE,
            strategy_reason=reason,
            effective_queries=[hypo_doc],
            hypothetical_document=hypo_doc,
        )

    def _decompose(
        self, question: str, reason: str, sub_queries: list[str]
    ) -> QueryTransformResult:
        """Use the LLM-provided sub-queries, falling back to the original if none."""
        effective = sub_queries if sub_queries else [question]

        print(
            f"{self._RED}[QueryTransformer] Decomposed into "
            f"{len(effective)} sub-queries{self._RESET}"
        )
        for i, sq in enumerate(effective, 1):
            print(f"{self._RED}  [{i}] {sq}{self._RESET}")

        return QueryTransformResult(
            original_query=question,
            strategy=TransformStrategy.DECOMPOSITION,
            strategy_reason=reason,
            effective_queries=effective,
        )
