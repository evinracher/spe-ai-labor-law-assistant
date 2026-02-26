from __future__ import annotations

from langchain_core.tools import tool

MAX_CITATIONS: int = 5

# ---------------------------------------------------------------------------
# Mock citations tool
# In a future milestone this will perform an actual vector-store similarity
# search and return real document chunks.
# ---------------------------------------------------------------------------

_MOCK_CITATION_POOL: list[dict] = [
    {
        "source": "Código Sustantivo del Trabajo (CST)",
        "page": 57,
        "chunk_id": "cst-art-57",
        "snippet": "El empleador está obligado a suministrar al trabajador los útiles, materiales e instrumentos necesarios para la realización de las labores.",
    },
    {
        "source": "Ley 50 de 1990",
        "page": 12,
        "chunk_id": "ley50-art-22",
        "snippet": "El trabajador tiene derecho a quince (15) días hábiles consecutivos de vacaciones remuneradas por cada año de servicios.",
    },
    {
        "source": "Decreto 1072 de 2015 — Decreto Único Reglamentario del Sector Trabajo",
        "page": 34,
        "chunk_id": "d1072-art-2.2.1",
        "snippet": "Las relaciones laborales deben fundamentarse en el respeto a la dignidad del trabajador y en los principios de igualdad y no discriminación.",
    },
    {
        "source": "Ley 100 de 1993 — Sistema de Seguridad Social Integral",
        "page": 8,
        "chunk_id": "ley100-art-15",
        "snippet": "Son afiliados al Sistema General de Pensiones, en forma obligatoria, todas las personas vinculadas mediante contrato de trabajo.",
    },
    {
        "source": "Código Sustantivo del Trabajo (CST)",
        "page": 140,
        "chunk_id": "cst-art-140",
        "snippet": "Durante la vigencia del contrato el trabajador tiene derecho a un descanso remunerado en los días que la ley señale como de fiesta.",
    },
    {
        "source": "Ley 789 de 2002",
        "page": 5,
        "chunk_id": "ley789-art-5",
        "snippet": "El auxilio de transporte se reconocerá a los trabajadores cuya remuneración mensual no exceda de dos salarios mínimos legales vigentes.",
    },
    {
        "source": "Constitución Política de Colombia — Art. 53",
        "page": None,
        "chunk_id": "cp-art-53",
        "snippet": "El Congreso expedirá el estatuto del trabajo. La ley correspondiente tendrá en cuenta por lo menos los principios de igualdad de oportunidades para los trabajadores.",
    },
]


@tool
def generate_mock_citations(question: str, max_citations: int = MAX_CITATIONS) -> list[dict]:
    """Generate mock citations from the Colombian labor law corpus for a given question.

    Returns up to `max_citations` citation records, each containing the source document
    name, page number, internal chunk identifier, and a verbatim text snippet.
    In future milestones this tool will perform a real vector-store similarity search.
    """
    import hashlib
    import random

    # Deterministic shuffle based on the question so the same question always
    # returns the same citations (useful for testing).
    seed = int(hashlib.md5(question.encode()).hexdigest(), 16) % (2**32)
    pool = _MOCK_CITATION_POOL.copy()
    random.Random(seed).shuffle(pool)
    return pool[:max_citations]


__all__ = ["MAX_CITATIONS", "generate_mock_citations"]
