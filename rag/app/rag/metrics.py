"""
app/rag/metrics.py
------------------
Evaluation metrics for the RAG pipeline.

Retrieval metrics (Precision@k, MRR, nDCG@k) are computed using an LLM as a judge
to determine the relevance of each retrieved chunk, since no labeled ground-truth
annotation set exists for this corpus.

  - Precision@k  : fraction of the k retrieved chunks judged relevant.
  - MRR          : 1 / rank of the first relevant chunk (0 if none relevant).
  - nDCG@k       : normalized Discounted Cumulative Gain using graded LLM scores.
  - Recall@k     : TODO — requires knowing the total number of relevant documents in
                   the full corpus for each query. Cannot be computed without manual
                   relevance annotations over the entire vector store. Implement when
                   a labeled evaluation set is available.

Generation metrics (Relevance, Faithfulness) are also judged by the LLM:

  - Relevance    : does the answer address the user's question? (0.0-1.0)
  - Faithfulness : are all answer claims supported by the retrieved context? (0.0-1.0)

Both metric groups reuse the LLM already instantiated in agents.py (passed as a
parameter to avoid circular imports).
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.api.schemas import (
    ChunkJudgment,
    GenerationJudgment,
    GenerationMetrics,
    RetrievalMetrics,
)

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


# ============================================================= internal judge schemas


class _SingleChunkJudgment(BaseModel):
    chunk_index: int = Field(description="0-based index of the evaluated chunk.")
    relevant: bool = Field(description="True if the chunk is useful to answer the query.")
    relevance_score: float = Field(
        description="Graded relevance: 0.0 (not relevant) to 1.0 (highly relevant).",
        ge=0.0,
        le=1.0,
    )
    justification: str = Field(description="One sentence explaining the judgment.")


class _BulkChunkJudgmentOutput(BaseModel):
    judgments: list[_SingleChunkJudgment] = Field(
        description="One judgment per chunk, in the same order as the input chunks."
    )


class _JudgeScoreOutput(BaseModel):
    score: float = Field(
        description="Quality score from 0.0 (worst) to 1.0 (best).", ge=0.0, le=1.0
    )
    justification: str = Field(description="One sentence explaining the score.")


# ============================================================= prompt templates

_CHUNK_RELEVANCE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a legal retrieval evaluator. "
            "Determine whether each retrieved chunk helps answer the user's query. "
            "A chunk is relevant if it contains information directly useful to answer the query. "
            "Return exactly one judgment per chunk, in index order.",
        ),
        (
            "user",
            "Query: {query}\n\n"
            "Chunks to evaluate:\n{chunks_text}\n\n"
            "Return one judgment per chunk.",
        ),
    ]
)

_RELEVANCE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are evaluating whether a generated answer addresses the user's question. "
            "Score relevance from 0.0 (does not address the question at all) to 1.0 "
            "(fully and directly addresses all aspects of the question). "
            "Provide a one-sentence justification.",
        ),
        (
            "user",
            "Question: {question}\n\nAnswer: {answer}",
        ),
    ]
)

_FAITHFULNESS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are evaluating whether a generated answer is faithful to the retrieved context. "
            "Faithful means every factual claim in the answer is directly supported by the context. "
            "Score faithfulness from 0.0 (answer contains unsupported claims) to 1.0 "
            "(all claims are grounded in the context). "
            "Provide a one-sentence justification.",
        ),
        (
            "user",
            "Context:\n{context}\n\nAnswer: {answer}",
        ),
    ]
)


# ============================================================= helpers


def _ndcg(relevance_scores: list[float]) -> float:
    """Compute nDCG@k for an ordered list of graded relevance scores."""
    if not relevance_scores:
        return 0.0
    dcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(relevance_scores))
    ideal = sorted(relevance_scores, reverse=True)
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal))
    return (dcg / idcg) if idcg > 0 else 0.0


# ============================================================= public functions


def compute_retrieval_metrics(
    query: str,
    retrieved_snippets: list[tuple[str, str]],
    llm: BaseChatModel,
) -> RetrievalMetrics:
    """
    Compute Precision@k, MRR, and nDCG@k for the retrieved chunks.

    Uses the LLM as a judge to determine per-chunk relevance since no external
    ground-truth annotation set is available for this corpus.

    Args:
        query: The original user query.
        retrieved_snippets: Ordered list of (chunk_id, text) in retrieval order.
        llm: LLM instance used as relevance judge.

    Returns:
        RetrievalMetrics with all computed metric values and per-chunk judgments.
    """
    k = len(retrieved_snippets)
    if k == 0:
        return RetrievalMetrics(precision_at_k=0.0, mrr=0.0, ndcg_at_k=0.0, k=0, chunk_judgments=[])

    chunks_text = "\n\n".join(
        f"[{i}] {snippet[:400]}" for i, (_, snippet) in enumerate(retrieved_snippets)
    )

    try:
        chain = _CHUNK_RELEVANCE_PROMPT | llm.with_structured_output(_BulkChunkJudgmentOutput)
        result: _BulkChunkJudgmentOutput = chain.invoke(
            {"query": query, "chunks_text": chunks_text}
        )
        raw_judgments = {j.chunk_index: j for j in result.judgments}
    except Exception as exc:
        logger.warning("Chunk relevance judge failed: %s", exc)
        raw_judgments = {
            i: _SingleChunkJudgment(
                chunk_index=i,
                relevant=False,
                relevance_score=0.0,
                justification="Judge unavailable.",
            )
            for i in range(k)
        }

    chunk_judgments: list[ChunkJudgment] = []
    relevance_scores: list[float] = []
    first_relevant_rank: int | None = None

    for i, (chunk_id, _) in enumerate(retrieved_snippets):
        j = raw_judgments.get(i)
        rel = j.relevant if j else False
        score = j.relevance_score if j else 0.0
        justif = j.justification if j else "Judge unavailable."

        chunk_judgments.append(
            ChunkJudgment(
                chunk_id=chunk_id, relevant=rel, relevance_score=score, justification=justif
            )
        )
        relevance_scores.append(score)

        if rel and first_relevant_rank is None:
            first_relevant_rank = i + 1  # 1-indexed rank

    precision = sum(1 for cj in chunk_judgments if cj.relevant) / k
    mrr = (1.0 / first_relevant_rank) if first_relevant_rank is not None else 0.0
    ndcg = _ndcg(relevance_scores)

    return RetrievalMetrics(
        precision_at_k=round(precision, 4),
        mrr=round(mrr, 4),
        ndcg_at_k=round(ndcg, 4),
        k=k,
        chunk_judgments=chunk_judgments,
    )


def compute_generation_metrics(
    question: str,
    answer: str,
    context: str,
    llm: BaseChatModel,
) -> GenerationMetrics:
    """
    Compute Relevance and Faithfulness scores for the generated answer via LLM-as-a-judge.

    Args:
        question: The original user query.
        answer: The generated answer string.
        context: The retrieved context string (used for faithfulness judgment).
        llm: LLM instance used as judge.

    Returns:
        GenerationMetrics with Relevance and Faithfulness scores and justifications.
    """
    judge_chain = llm.with_structured_output(_JudgeScoreOutput)

    def _judge(prompt: ChatPromptTemplate, variables: dict) -> GenerationJudgment:
        try:
            out: _JudgeScoreOutput = (prompt | judge_chain).invoke(variables)
            return GenerationJudgment(score=round(out.score, 4), justification=out.justification)
        except Exception as exc:
            logger.warning("Generation judge failed: %s", exc)
            return GenerationJudgment(score=0.0, justification="Judge unavailable.")

    relevance = _judge(_RELEVANCE_PROMPT, {"question": question, "answer": answer[:3000]})
    faithfulness = _judge(
        _FAITHFULNESS_PROMPT, {"context": context[:3000], "answer": answer[:3000]}
    )

    return GenerationMetrics(relevance=relevance, faithfulness=faithfulness)
