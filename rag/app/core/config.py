"""
app/core/config.py
------------------
Application settings loaded from environment variables / .env file.
Uses Pydantic Settings v2 for type-safe configuration.

TODO (future milestones):
  - Add validation that CHROMA_DIR and DATA_DIR are absolute or resolvable paths.
  - Add secret rotation strategy for API keys in prod.
  - Add ALLOWED_ORIGINS for CORS when deploying publicly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta absoluta al directorio rag/ donde está el .env
_RAG_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _RAG_DIR / ".env"


class Settings(BaseSettings):
    """All runtime configuration for the Colombian Labor Law RAG backend."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ server
    HOST: str = Field(default="0.0.0.0", description="Bind host for uvicorn")
    PORT: int = Field(default=8000, description="Bind port for uvicorn")
    ENV: Literal["dev", "prod"] = Field(
        default="dev", description="Runtime environment"
    )

    # -------------------------------------------------------------------- data
    DATA_DIR: Path = Field(
        default=Path("./data"),
        description="Directory containing source corpus files (PDF/HTML/TXT).",
    )

    # ---------------------------------------------------------------- vector db
    VECTOR_DB: str = Field(
        default="chroma",
        description="Vector database backend. Currently only 'chroma' is planned.",
    )
    CHROMA_DIR: Path = Field(
        default=Path("./storage/chroma"),
        description="Persistent directory for ChromaDB.",
    )

    # -------------------------------------------------------------------- LLM
    LLM_PROVIDER: Literal["gemini", "groq", "local", "mock"] = Field(
        default="mock",
        description=(
            "LLM provider to use for answer generation. "
            "Use 'mock' for development without API keys."
        ),
    )
    GOOGLE_API_KEY: str | None = Field(
        default=None,
        description="Google Gemini API key. Required when LLM_PROVIDER='gemini'.",
    )
    GROQ_API_KEY: str | None = Field(
        default=None,
        description="Groq API key. Required when LLM_PROVIDER='groq'.",
    )

    # ------------------------------------------------------------- embeddings
    EMBEDDINGS_PROVIDER: str = Field(
        default="local",
        description="Embeddings backend. 'local' uses sentence-transformers.",
    )
    EMBEDDINGS_MODEL: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        description=(
            "Model name for sentence-transformers embeddings. "
            "Must support Spanish text."
        ),
    )

    # ----------------------------------------------------------------- derived
    @model_validator(mode="after")
    def _warn_missing_keys(self) -> "Settings":
        """Emit a warning (not raise) if LLM_PROVIDER requires a key that is absent."""
        if self.LLM_PROVIDER == "gemini" and not self.GOOGLE_API_KEY:
            print(
                "[WARNING] LLM_PROVIDER=gemini but GOOGLE_API_KEY is not set. "
                "The LLM step will fail at runtime."
            )
        if self.LLM_PROVIDER == "groq" and not self.GROQ_API_KEY:
            print(
                "[WARNING] LLM_PROVIDER=groq but GROQ_API_KEY is not set. "
                "The LLM step will fail at runtime."
            )
        return self


# Module-level singleton — import this instead of instantiating Settings directly.
settings = Settings()
