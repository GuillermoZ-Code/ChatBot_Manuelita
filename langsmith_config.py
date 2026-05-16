"""Configuración de LangSmith para trazabilidad del proyecto."""

from __future__ import annotations

import os


def configure_langsmith() -> None:
    """Activa LangSmith si las variables de entorno están presentes."""
    api_key = os.getenv("LANGSMITH_API_KEY")
    tracing = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    project = os.getenv("LANGSMITH_PROJECT", "taller_1_manuelita")

    if not api_key:
        return

    os.environ["LANGSMITH_TRACING"] = "true" if tracing else "false"
    os.environ["LANGSMITH_PROJECT"] = project
    os.environ.setdefault("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")