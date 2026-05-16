"""Capa de orquestación del agente conversacional con tools."""

from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from chat_memory import ChatMemoryService
from llm_factory import build_llm
from settings import SYSTEM_PROMPT_TEMPLATE
from structured_tool import get_structured_answer, load_structured_data
from tools import get_structured_data, retrieve_rag_context

ROUTE_MEMORY = "Memoria"
ROUTE_RAG = "RAG"
ROUTE_STRUCTURED = "Dato estructurado"


class AgentService:
    """Resuelve preguntas del usuario combinando memoria, dato estructurado o RAG."""

    def __init__(self, memory_service: ChatMemoryService) -> None:
        self.memory_service = memory_service
        self.structured_data = load_structured_data()

    def answer_question(
        self,
        prompt: str,
        model_config: Dict[str, str],
        app_settings: Dict[str, Any],
    ) -> Dict[str, Any]:
        recent_history = self.memory_service.get_recent_history_text()
        user_profile = self.memory_service.get_user_profile()
        route = self._choose_route(prompt, recent_history, user_profile)

        if route == ROUTE_MEMORY:
            llm = build_llm(model_config, app_settings)
            messages = self._build_memory_messages(prompt, recent_history, user_profile, app_settings)
            response = llm.invoke(messages)
            return {"answer": response.content, "route": ROUTE_MEMORY, "tool_used": "none", "metadata": {"history_used": True}}

        if route == ROUTE_STRUCTURED:
            answer = get_structured_answer(prompt, self.structured_data)
            final_answer = answer or "No tengo información suficiente en mi base de conocimiento para responder esa pregunta."
            return {"answer": final_answer, "route": ROUTE_STRUCTURED, "tool_used": get_structured_data.name, "metadata": {"history_used": False}}

        context = retrieve_rag_context.invoke({"query": prompt, "rag_k": int(app_settings["rag_k"])})
        llm = build_llm(model_config, app_settings)
        messages = self._build_rag_messages(prompt, recent_history, user_profile, context, app_settings)
        response = llm.invoke(messages)
        return {"answer": response.content, "route": ROUTE_RAG, "tool_used": retrieve_rag_context.name, "metadata": {"history_used": True, "retrieved_context": context}}

    def _choose_route(self, prompt: str, recent_history: str, user_profile: Dict[str, Any]) -> str:
        lowered = prompt.lower().strip()
        personal_markers = (
            "me llamo", "mi nombre es", "soy ", "recuerdas mi nombre",
            "como me llamo", "cuál es tu nombre", "cual es tu nombre",
            "como te llamas", "quién eres", "quien eres",
        )
        if any(marker in lowered for marker in personal_markers):
            return ROUTE_MEMORY

        if any(keyword in lowered for keyword in ("yo ", "mi ", "mis ")) and user_profile:
            return ROUTE_MEMORY

        if self._looks_like_company_question(lowered):
            return ROUTE_RAG

        structured_answer = get_structured_answer(prompt, self.structured_data)
        if structured_answer:
            return ROUTE_STRUCTURED

        return ROUTE_RAG

    def _looks_like_company_question(self, lowered: str) -> bool:
        company_markers = (
            "manuelita", "grupo", "empresa", "compañía", "compania",
            "misión", "mision", "productos", "historia", "sostenibilidad",
            "sedes", "contacto", "horario", "trabajar", "trayectoria", "presencia",
        )
        return any(marker in lowered for marker in company_markers)

    def _build_memory_messages(self, prompt, history, user_profile, app_settings):
        extra = app_settings.get("system_prompt_extra", "") or "Sin instrucciones extra."
        profile_text = self._format_profile(user_profile)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            history=f"{history}\n\nPerfil persistente del usuario:\n{profile_text}",
            extra=extra,
        )
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Responde usando el perfil persistente y el historial conversacional para esta consulta del usuario:\n{prompt}"),
        ]

    def _build_rag_messages(self, prompt, history, user_profile, context, app_settings):
        extra = app_settings.get("system_prompt_extra", "") or "Sin instrucciones extra."
        profile_text = self._format_profile(user_profile)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            history=f"{history}\n\nPerfil persistente del usuario:\n{profile_text}",
            extra=extra,
        )
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Contexto recuperado:\n{context}\n\nPregunta del usuario:\n{prompt}\n\nResponde solamente con base en el contexto, el historial y el perfil persistente si aplica."),
        ]

    def _format_profile(self, profile: Dict[str, Any]) -> str:
        if not profile:
            return "Sin perfil persistente guardado."
        return "\n".join(f"- {key}: {value}" for key, value in profile.items())