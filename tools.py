"""Herramientas LangChain expuestas al agente."""

from __future__ import annotations

from typing import Tuple

from langchain.tools import tool

from rag_client import query_rag_context
from structured_tool import get_structured_answer, load_structured_data


@tool("retrieve_rag_context")
def retrieve_rag_context(query: str, rag_k: int = 4) -> str:
    """Recupera contexto documental sobre Manuelita desde la base vectorial."""
    return query_rag_context(query, k=rag_k)


@tool("get_structured_data")
def get_structured_data(query: str) -> str:
    """Recupera datos estructurados fijos como contacto, horarios o sedes."""
    data = load_structured_data()
    answer = get_structured_answer(query, data)
    if not answer:
        return "No se encontró información estructurada para esa consulta."
    return answer


def get_available_tools():
    """Retorna la colección de herramientas registradas para el agente."""
    return [retrieve_rag_context, get_structured_data]
