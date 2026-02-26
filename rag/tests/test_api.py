"""
tests/test_api.py
-----------------
Smoke tests for milestone 1 endpoints using FastAPI's TestClient.

Run with:
    pytest -v
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ================================================================= /health


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


# ================================================================== /chat


def test_chat_in_context_returns_citations() -> None:
    payload = {"question": "¿Cuántos días de vacaciones tiene un trabajador?"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["answer"]) > 10
    assert len(data["citations"]) >= 2
    assert data["trace"]["vector_db"] is not None


def test_chat_out_of_context_returns_empty_citations() -> None:
    payload = {"question": "¿Cuál es la distancia al planeta Marte?"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["answer"] == "No aparece en el contexto."
    assert data["citations"] == []


def test_chat_empty_question_returns_422() -> None:
    """Empty string should fail Pydantic min_length validation."""
    payload = {"question": ""}
    response = client.post("/chat", json=payload)
    assert response.status_code == 422


def test_chat_too_short_question_returns_422() -> None:
    """A 3-char question is below min_length=5."""
    payload = {"question": "hoy"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 422


def test_chat_deterministic_same_question() -> None:
    """Same question must always return the same answer (deterministic mock)."""
    question = "¿Cuál es el auxilio de cesantías en Colombia?"
    payload = {"question": question}
    r1 = client.post("/chat", json=payload).json()
    r2 = client.post("/chat", json=payload).json()
    # request_id is a fresh UUID each time — exclude it from comparison
    assert r1["answer"] == r2["answer"]
    assert r1["citations"] == r2["citations"]
    assert r1["trace"]["intent"] == r2["trace"]["intent"]


def test_chat_optional_fields_accepted() -> None:
    payload = {
        "question": "¿Qué dice el Código Sustantivo del Trabajo sobre jornada laboral?",
        "conversation_id": "test-conv-001",
        "max_citations": 3,
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    assert response.json()["ok"] is True


# TODO (milestone 2): add tests for the real retrieval pipeline once implemented.
# TODO (milestone 3): add LangGraph workflow integration tests.
