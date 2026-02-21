"""
app/rag/mock.py
---------------
Deterministic mock RAG responder for development / demo purposes.

This module simulates the full RAG pipeline without any real retrieval or LLM calls.
Responses are deterministic: the same question always produces the same answer,
which is important for frontend integration testing and demo reproducibility.

Replace the body of `mock_rag_answer` (and wire `real_rag_answer`) once the
real pipeline is implemented.

TODO (milestone 2 — ingestion):
  - Load corpus files from settings.DATA_DIR (PDF via pypdf, HTML via BeautifulSoup,
    TXT directly).
  - Clean/normalize text: strip headers/footers, fix encoding, normalize whitespace.
  - Split into overlapping chunks (e.g. 512 tokens, 64-token overlap).
  - Compute local embeddings with sentence-transformers (settings.EMBEDDINGS_MODEL).
  - Persist chunks + metadata to ChromaDB at settings.CHROMA_DIR.

TODO (milestone 3 — retrieval):
  - On each query: embed the question with the same local model.
  - Run similarity search (top_k) against ChromaDB collection.
  - Optional: apply cross-encoder reranker (e.g. cross-encoder/ms-marco-MiniLM-L-6-v2).
  - Build Citation objects from returned metadata (source, page, chunk_id, snippet).

TODO (milestone 4 — LangGraph workflow):
  - Node 1 "classify_intent": classify question into predefined labor-law categories
    (vacaciones, salario, despido, contrato, seguridad_social, licencias, etc.).
  - Node 2 "retrieve": run similarity search with dynamic top_k based on intent.
  - Node 3 "generate": call LLM (Gemini/Groq/local) with strict prompt:
        "Responde ÚNICAMENTE con base en los fragmentos proporcionados. Si la
         información no está en los fragmentos, responde exactamente:
         'No aparece en el contexto.' y no añadas nada más."
  - Node 4 "critic": evaluate if answer is grounded; re-retrieve if not confident.
  - Node 5 "finalize": assemble ChatResponse with answer + citations + trace.

TODO (milestone 5 — LLM integration):
  - Implement GeminiClient wrapping google-generativeai SDK.
  - Implement GroqClient wrapping groq SDK.
  - Implement LocalClient (e.g. Ollama or llama-cpp-python).
  - Route to the right client via settings.LLM_PROVIDER.

TODO (milestone 6 — conversation memory):
  - Persist conversation turns keyed by conversation_id.
  - Inject recent turns as context into the LLM prompt.
  - Use LangGraph checkpointing for stateful graph runs.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from app.api.schemas import Citation, ChatResponse, Trace

if TYPE_CHECKING:
    from app.core.config import Settings

# ---------------------------------------------------------------------------
# Keywords that signal the question is clearly outside the labor-law domain.
# The match is case-insensitive and checks for whole-word presence.
# ---------------------------------------------------------------------------
_OUT_OF_CONTEXT_KEYWORDS: frozenset[str] = frozenset(
    {
        # astronomy / science
        "astronomía", "astronomia", "planeta", "galaxia", "nebulosa", "cometa",
        "telescopio", "universo", "agujero negro",
        # cooking
        "receta", "cocina", "ingrediente", "hornear", "freír", "freir",
        "postre", "sopa", "ensalada", "gastronomía", "gastronomia",
        # sports / entertainment
        "fútbol", "futbol", "béisbol", "beisbol", "baloncesto", "tenis",
        "mundial", "gol", "estadio", "jugador de fútbol",
        # geography / travel (unrelated)
        "turismo", "montañismo", "senderismo", "buceo",
        # pop culture
        "película", "pelicula", "serie", "videojuego", "anime", "manga",
        # medicine (outside occupational accidents scope)
        "cirugía", "cirugia", "oncología", "oncologia", "cardiología",
    }
)

# ---------------------------------------------------------------------------
# Realistic mock corpus entries — used to build deterministic citations.
# ---------------------------------------------------------------------------
_MOCK_SOURCES: list[dict] = [
    {
        "source": "CST_codigo_sustantivo_trabajo.pdf",
        "page": 47,
        "chunk_id": "cst-047-001",
        "snippet": (
            "Artículo 186: Todo trabajador que hubiere prestado sus servicios "
            "durante un año tiene derecho a quince (15) días hábiles consecutivos "
            "de vacaciones remuneradas."
        ),
    },
    {
        "source": "CST_codigo_sustantivo_trabajo.pdf",
        "page": 51,
        "chunk_id": "cst-051-003",
        "snippet": (
            "Artículo 189: Durante el período de vacaciones el trabajador recibirá "
            "el salario ordinario que esté devengando el día que comience a disfrutar "
            "de ellas."
        ),
    },
    {
        "source": "ley_789_2002_reforma_laboral.pdf",
        "page": 3,
        "chunk_id": "ley789-003-002",
        "snippet": (
            "Artículo 28 — Jornada laboral: La duración máxima de la jornada "
            "ordinaria de trabajo es de ocho (8) horas al día y cuarenta y ocho "
            "(48) horas a la semana."
        ),
    },
    {
        "source": "ley_1468_2011_licencia_maternidad.html",
        "page": None,
        "chunk_id": "ley1468-mat-001",
        "snippet": (
            "La licencia de maternidad será de dieciocho (18) semanas. "
            "La trabajadora deberá disfrutar forzosamente al menos una semana "
            "antes del parto, salvo que un médico certifique lo contrario."
        ),
    },
    {
        "source": "decreto_1072_2015_reglamento_trabajo.pdf",
        "page": 112,
        "chunk_id": "dec1072-112-005",
        "snippet": (
            "El empleador está obligado a afiliar a sus trabajadores al sistema "
            "de seguridad social integral desde el primer día de vinculación, "
            "cubriendo salud, pensión y riesgos laborales."
        ),
    },
    {
        "source": "CST_codigo_sustantivo_trabajo.pdf",
        "page": 78,
        "chunk_id": "cst-078-002",
        "snippet": (
            "Artículo 249: El trabajador que al momento de su retiro haya laborado "
            "un mínimo de un año tiene derecho a que el empleador le pague un mes "
            "de salario por cada año de servicios como auxilio de cesantías."
        ),
    },
    {
        "source": "ley_100_1993_seguridad_social.pdf",
        "page": 22,
        "chunk_id": "ley100-022-001",
        "snippet": (
            "El sistema general de pensiones tiene como objeto garantizar a la "
            "población el amparo contra las contingencias derivadas de la vejez, "
            "la invalidez y la muerte, mediante el reconocimiento de las pensiones "
            "y prestaciones."
        ),
    },
    {
        "source": "CST_codigo_sustantivo_trabajo.pdf",
        "page": 33,
        "chunk_id": "cst-033-007",
        "snippet": (
            "Artículo 64: En todo contrato de trabajo va envuelta la condición "
            "resolutoria por incumplimiento de lo pactado, con indemnización de "
            "perjuicios a cargo de la parte responsable."
        ),
    },
]

# ---------------------------------------------------------------------------
# Mock answer templates (Spanish) — selected deterministically by hash.
# ---------------------------------------------------------------------------
_ANSWER_TEMPLATES: list[str] = [
    # 0 — vacaciones / descanso
    (
        "Según el Código Sustantivo del Trabajo colombiano, todo trabajador que "
        "haya prestado sus servicios durante un año continuo tiene derecho a quince "
        "(15) días hábiles consecutivos de vacaciones remuneradas (artículo 186 CST).\n\n"
        "Durante el período vacacional, el empleador debe pagar el salario ordinario "
        "que el trabajador esté devengando al momento en que comience a disfrutar de "
        "sus vacaciones (artículo 189 CST).\n\n"
        "Es importante destacar que:\n"
        "- Las vacaciones no son compensables en dinero, salvo en casos excepcionales "
        "previstos por la ley.\n"
        "- El empleador puede determinar la época de vacaciones, pero debe dar aviso "
        "al trabajador con al menos quince (15) días de anticipación.\n"
        "- Las vacaciones pueden acumularse hasta por dos períodos consecutivos, "
        "previa solicitud escrita del trabajador."
    ),
    # 1 — jornada / horas extras
    (
        "La jornada laboral máxima en Colombia es de ocho (8) horas diarias y "
        "cuarenta y ocho (48) horas semanales, de acuerdo con el artículo 161 del "
        "Código Sustantivo del Trabajo y la Ley 789 de 2002.\n\n"
        "Las horas trabajadas por fuera de esta jornada ordinaria se denominan "
        "horas extra y deben ser remuneradas con un recargo sobre el valor de la "
        "hora ordinaria:\n"
        "- Hora extra diurna: recargo del 25 % sobre el valor hora ordinaria.\n"
        "- Hora extra nocturna: recargo del 75 % sobre el valor hora ordinaria.\n"
        "- Hora nocturna ordinaria (entre las 9 p.m. y las 6 a.m.): recargo del "
        "35 %.\n\n"
        "Ningún trabajador puede laborar más de dos (2) horas extra por día ni más "
        "de doce (12) horas extra a la semana, salvo autorización expresa del "
        "Ministerio del Trabajo."
    ),
    # 2 — cesantías / prestaciones sociales
    (
        "Las cesantías constituyen una prestación social de carácter obligatorio en "
        "Colombia, regulada por los artículos 249 y siguientes del Código Sustantivo "
        "del Trabajo.\n\n"
        "El valor equivale a un (1) mes de salario por cada año de servicios "
        "continuos, y proporcional por fracción de año. Las cesantías deben ser "
        "consignadas en un fondo administrador a más tardar el 14 de febrero de "
        "cada año.\n\n"
        "Prestaciones sociales adicionales que debe reconocer el empleador:\n"
        "- Prima de servicios: un mes de salario pagadero en dos cuotas (junio y "
        "diciembre).\n"
        "- Intereses sobre cesantías: 12 % anual sobre el saldo acumulado.\n"
        "- Dotación: para trabajadores que devenguen hasta dos salarios mínimos."
    ),
    # 3 — seguridad social / afiliación
    (
        "El sistema de seguridad social integral en Colombia está regulado "
        "principalmente por la Ley 100 de 1993 y el Decreto 1072 de 2015 "
        "(Decreto Único Reglamentario del Sector Trabajo).\n\n"
        "El empleador está obligado a afiliar a sus trabajadores a los tres "
        "subsistemas desde el primer día de trabajo:\n"
        "1. Salud (EPS): el aporte total es del 12,5 % del salario; el empleador "
        "paga 8,5 % y el trabajador 4 %.\n"
        "2. Pensión (AFP): aporte total del 16 %; empleador 12 % y trabajador 4 %.\n"
        "3. Riesgos Laborales (ARL): el aporte lo asume íntegramente el empleador; "
        "varía entre 0,348 % y 8,7 % según la clase de riesgo de la actividad.\n\n"
        "El incumplimiento de la obligación de afiliación genera responsabilidad "
        "directa del empleador por las prestaciones asistenciales y económicas que "
        "correspondan al trabajador."
    ),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def mock_rag_answer(question: str, settings: "Settings") -> ChatResponse:
    """
    Generate a deterministic mock ChatResponse for development and demo purposes.

    The function:
    1. Checks whether the question is outside the labor-law domain.
    2. If out-of-context → returns the safe "No aparece en el contexto." response.
    3. Otherwise → selects an answer template and citations deterministically
       based on a SHA-256 hash of the (lowercased, stripped) question.

    Args:
        question:  User question string (already validated by Pydantic).
        settings:  Application settings (used for trace metadata).

    Returns:
        A fully populated ChatResponse (ok=True, no real retrieval performed).
    """
    import uuid

    request_id = str(uuid.uuid4())
    q_normalized = question.lower().strip()

    # ------------------------------------------------------------------
    # Step 1 — out-of-context check
    # ------------------------------------------------------------------
    if _is_out_of_context(q_normalized):
        return ChatResponse(
            ok=True,
            request_id=request_id,
            answer="No aparece en el contexto.",
            citations=[],
            trace=Trace(
                intent=None,
                top_k=0,
                vector_db=settings.VECTOR_DB,
                llm_provider=settings.LLM_PROVIDER,
            ),
        )

    # ------------------------------------------------------------------
    # Step 2 — deterministic selection via hash
    # ------------------------------------------------------------------
    digest = int(hashlib.sha256(q_normalized.encode()).hexdigest(), 16)

    # Pick answer template
    answer_text = _ANSWER_TEMPLATES[digest % len(_ANSWER_TEMPLATES)]

    # Pick 2–4 citations (distinct, order shuffled deterministically)
    num_citations = 2 + (digest % 3)  # 2, 3, or 4
    # Use different bit slices of the hash to pick source indices
    indices: list[int] = []
    shift = 0
    while len(indices) < num_citations:
        idx = (digest >> shift) % len(_MOCK_SOURCES)
        if idx not in indices:
            indices.append(idx)
        shift += 4  # advance 4 bits each attempt

    citations = [Citation(**_MOCK_SOURCES[i]) for i in indices]

    # Simulated trace
    top_k = num_citations
    intent_options = [
        "vacaciones_y_descanso",
        "jornada_y_horas_extra",
        "cesantias_y_prestaciones",
        "seguridad_social",
        "contrato_de_trabajo",
        "salario_minimo",
        "despido_e_indemnizacion",
        "licencias",
    ]
    intent = intent_options[digest % len(intent_options)]

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_out_of_context(q_normalized: str) -> bool:
    """Return True if the question clearly falls outside the labor-law domain."""
    for keyword in _OUT_OF_CONTEXT_KEYWORDS:
        if keyword in q_normalized:
            return True
    return False
