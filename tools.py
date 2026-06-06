"""Herramientas estructuradas del agente Manuelita."""

from __future__ import annotations

from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from db import list_messages
from rag_client import query_rag_context
from structured_tool import get_structured_answer, load_structured_data

# chat_id activo inyectado por AgentService antes de cada invocación.
# Permite que get_conversation_summary acceda al historial correcto sin
# necesidad de pasar el chat_id como argumento visible al LLM.
_active_chat_id: Optional[int] = None


def set_active_chat_id(chat_id: int) -> None:
    global _active_chat_id
    _active_chat_id = chat_id


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class StructuredDataArgs(BaseModel):
    query: str = Field(
        ...,
        description="Consulta sobre datos fijos operativos como teléfono, correo, horarios, dirección, sedes, PQRS o NIT.",
    )


class RagArgs(BaseModel):
    query: str = Field(
        ...,
        description="Consulta institucional, histórica, corporativa o documental sobre Manuelita.",
    )
    rag_k: int = Field(
        default=3,
        ge=1,
        le=8,
        description="Número de fragmentos a recuperar desde la base documental.",
    )


class HumanReviewArgs(BaseModel):
    reason: str = Field(
        ...,
        description="Motivo por el que se requiere revisión humana.",
    )


class ConversationSummaryArgs(BaseModel):
    instruction: str = Field(
        default="resumen",
        description=(
            "Tipo de resumen solicitado: 'resumen' para síntesis general, "
            "'temas' para listar los temas tratados, "
            "'conteo' para contar cuántas preguntas se hicieron."
        ),
    )


# ---------------------------------------------------------------------------
# Funciones internas
# ---------------------------------------------------------------------------

def _get_structured_data(query: str) -> str:
    data = load_structured_data()
    answer = get_structured_answer(query, data)
    if not answer:
        return "No se encontró información estructurada para esa consulta."
    return answer


def _retrieve_rag_context(query: str, rag_k: int = 3) -> str:
    return query_rag_context(query, k=rag_k)


def _request_human_review(reason: str) -> str:
    return f"HUMAN_REVIEW_REQUIRED::{reason}"


def _get_conversation_summary(instruction: str = "resumen") -> str:
    """Lee el historial completo de la sesión desde la DB y lo formatea."""
    if _active_chat_id is None:
        return "No hay una sesión activa para resumir."

    messages = list_messages(_active_chat_id)
    if not messages:
        return "No hay mensajes registrados en esta sesión."

    user_messages = [m for m in messages if m["role"] == "user"]
    assistant_messages = [m for m in messages if m["role"] == "assistant"]

    instruction_lower = instruction.lower().strip()

    # --- Conteo ---
    if "conteo" in instruction_lower or "cuánto" in instruction_lower or "cuantas" in instruction_lower:
        return (
            f"En esta conversación se han registrado {len(user_messages)} pregunta(s) "
            f"del usuario y {len(assistant_messages)} respuesta(s) del asistente."
        )

    # --- Lista de temas ---
    if "tema" in instruction_lower:
        lines = ["Temas abordados en la conversación:"]
        for i, msg in enumerate(user_messages, start=1):
            preview = msg["content"][:120].strip()
            if len(msg["content"]) > 120:
                preview += "..."
            lines.append(f"{i}. {preview}")
        return "\n".join(lines)

    # --- Resumen completo (default) ---
    lines = [
        f"Resumen de la conversación ({len(user_messages)} pregunta(s) registrada(s)):",
        "",
    ]
    for i, msg in enumerate(messages, start=1):
        role = "Usuario" if msg["role"] == "user" else "Manuel"
        # Truncar respuestas largas del asistente para que el resumen sea conciso
        content = msg["content"]
        if msg["role"] == "assistant" and len(content) > 200:
            content = content[:200].strip() + "..."
        lines.append(f"{i}. {role}: {content}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# StructuredTools registradas
# ---------------------------------------------------------------------------

get_structured_data = StructuredTool.from_function(
    func=_get_structured_data,
    name="get_structured_data",
    description="Recupera datos estructurados fijos como contacto, horarios, sedes, misión, visión o NIT.",
    args_schema=StructuredDataArgs,
)

retrieve_rag_context = StructuredTool.from_function(
    func=_retrieve_rag_context,
    name="retrieve_rag_context",
    description="Recupera contexto documental sobre Manuelita desde la base vectorial.",
    args_schema=RagArgs,
)

request_human_review = StructuredTool.from_function(
    func=_request_human_review,
    name="request_human_review",
    description="Solicita revisión humana para una consulta crítica o ambigua.",
    args_schema=HumanReviewArgs,
)

get_conversation_summary = StructuredTool.from_function(
    func=_get_conversation_summary,
    name="get_conversation_summary",
    description=(
        "Recupera y resume el historial completo de la conversación actual. "
        "Úsala cuando el usuario pregunte cuánto ha preguntado, qué temas se han tratado, "
        "pida un resumen de la sesión, o quiera saber qué se ha conversado hasta ahora."
    ),
    args_schema=ConversationSummaryArgs,
)


def get_available_tools():
    return [
        get_structured_data,
        retrieve_rag_context,
        request_human_review,
        get_conversation_summary,
    ]
