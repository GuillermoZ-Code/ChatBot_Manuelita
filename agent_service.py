"""Capa de orquestación del agente con create_react_agent, MemorySaver y HumanInTheLoopMiddleware."""

from __future__ import annotations

from typing import Any, Dict, Optional

from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent

from chat_memory import ChatMemoryService
from dynamic_prompt import dynamic_prompt
from human_in_the_loop import HumanInTheLoopMiddleware
from llm_factory import build_llm
import uuid
from langgraph.checkpoint.memory import MemorySaver
from tools import get_available_tools, set_active_chat_id

ROUTE_PROFILE_CAPTURE = "Captura perfil"
ROUTE_MEMORY = "Memoria"
ROUTE_STRUCTURED = "Dato estructurado"
ROUTE_RAG = "RAG"
ROUTE_HUMAN = "Control humano"

FALLBACK_ANSWER = (
    "No tengo información suficiente en mi base de conocimiento para responder esa pregunta."
)

_human_middleware = HumanInTheLoopMiddleware()


class AgentService:
    def __init__(self, memory_service: ChatMemoryService) -> None:
        self.memory_service = memory_service
        self.tools = get_available_tools()

    def answer_question(
        self,
        prompt: str,
        model_config: Dict[str, str],
        app_settings: Dict[str, Any],
    ) -> Dict[str, Any]:
        recent_history = self.memory_service.get_recent_history_text()
        user_profile = self.memory_service.get_user_profile()

        captured_name = self._extract_name_from_prompt(prompt)
        if captured_name:
            return {
                "answer": f"Mucho gusto, {captured_name}. Lo recordaré para esta conversación.",
                "route": ROUTE_PROFILE_CAPTURE,
                "tool_used": "none",
                "metadata": {"history_used": True, "captured_name": captured_name},
            }

        direct_memory = self._answer_from_memory_if_possible(prompt, user_profile)
        if direct_memory is not None:
            return direct_memory

        return self._run_agent(prompt, model_config, app_settings, recent_history, user_profile)

    def _run_agent(
        self,
        prompt: str,
        model_config: Dict[str, str],
        app_settings: Dict[str, Any],
        recent_history: str,
        user_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        rag_k = int(app_settings.get("rag_k", 4))
        critical_mode = self._is_critical_query(prompt)

        # Inyecta el chat_id activo para que get_conversation_summary acceda al historial correcto.
        set_active_chat_id(self.memory_service.chat_id)

        try:
            llm = build_llm(model_config, app_settings)

            system_prompt = dynamic_prompt(
                history=recent_history,
                user_profile=user_profile,
                extra=(
                    (app_settings.get("system_prompt_extra", "") or "")
                    + f"\nPara retrieve_rag_context usa rag_k={rag_k} cuando necesites contexto documental."
                ),
                critical_mode=critical_mode,
            )

            # MemorySaver por invocación: el historial conversacional lo gestiona
            # ChatMemoryService via dynamic_prompt. Este checkpointer solo mantiene
            # el estado interno del grafo durante los pasos de una misma llamada.
            checkpointer = MemorySaver()

            agent = create_react_agent(
                model=llm,
                tools=self.tools,
                prompt=system_prompt,
                checkpointer=checkpointer,
            )

            # UUID único por invocación — evita que el estado del grafo
            # se acumule entre preguntas distintas del mismo usuario.
            thread_config = {
                "configurable": {
                    "thread_id": str(uuid.uuid4()),
                }
            }

            result = agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "Resuelve la consulta del usuario siguiendo estas reglas:\n"
                                "- Usa get_structured_data para datos operativos fijos como contacto, teléfono, correo, horarios, misión, visión, sedes, NIT.\n"
                                "- Usa retrieve_rag_context para información institucional, histórica o documental.\n"
                                "- Usa request_human_review para solicitudes críticas o que requieran validación humana.\n"
                                "- Usa get_conversation_summary cuando el usuario pida un resumen o quiera saber qué se ha conversado.\n"
                                "- IMPORTANTE: cuando una herramienta devuelva información, ÚSALA para construir tu respuesta. No respondas con el mensaje de insuficiencia si la herramienta devolvió datos.\n"
                                "- Solo responde con el mensaje de insuficiencia si NINGUNA herramienta devolvió información relevante.\n\n"
                                f"Consulta: {prompt}"
                            ),
                        }
                    ]
                },
                config=thread_config,
            )

            raw_result = self._parse_agent_result(result)
            return _human_middleware.process(raw_result)

        except Exception as e:
            return {
                "answer": (
                    "En este momento no pude verificar la información, "
                    "pero puedo ayudarte con otra consulta sobre Manuelita."
                ),
                "route": ROUTE_RAG,
                "tool_used": "agent_error",
                "metadata": {"history_used": True, "error": str(e)},
            }

    def _parse_agent_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        messages = result.get("messages", [])
        route = ROUTE_MEMORY
        tool_used = "none"

        # Detectar qué herramienta se usó revisando todos los mensajes.
        for msg in messages:
            name = getattr(msg, "name", "") or ""
            if name == "get_structured_data":
                route = ROUTE_STRUCTURED
                tool_used = "get_structured_data"
            elif name == "retrieve_rag_context":
                route = ROUTE_RAG
                tool_used = "retrieve_rag_context"
            elif name == "request_human_review":
                route = ROUTE_HUMAN
                tool_used = "request_human_review"

        # Tomar únicamente el último AIMessage — la respuesta sintetizada del LLM.
        answer = FALLBACK_ANSWER
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                text = self._normalize_response_content(msg)
                if text:
                    answer = text
                    break

        return {
            "answer": answer,
            "route": route,
            "tool_used": tool_used,
            "metadata": {"history_used": True},
        }

    def _answer_from_memory_if_possible(
        self,
        prompt: str,
        user_profile: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if self._is_asking_for_name(prompt):
            known_name = user_profile.get("name")
            if known_name:
                return {
                    "answer": f"Te llamas {known_name}.",
                    "route": ROUTE_MEMORY,
                    "tool_used": "none",
                    "metadata": {"history_used": True, "used_profile_name": True},
                }
            return {
                "answer": (
                    "Aún no tengo el gusto de conocer tu nombre. "
                    "Soy Manuel, tu asesor virtual de Manuelita S.A. "
                    "¿Con quién tengo el placer de hablar?"
                ),
                "route": ROUTE_MEMORY,
                "tool_used": "none",
                "metadata": {"history_used": True, "used_profile_name": False},
            }
        return None

    def _is_critical_query(self, prompt: str) -> bool:
        lowered = prompt.lower().strip()
        critical_markers = (
            "modifica", "cambia", "borra", "elimina", "aprueba", "autoriza",
            "radica", "pqrs", "reclamo formal", "escala",
        )
        return any(marker in lowered for marker in critical_markers)

    def _is_asking_for_name(self, prompt: str) -> bool:
        lowered = prompt.lower().strip()
        markers = (
            "como me llamo",
            "cómo me llamo",
            "cual es mi nombre",
            "cuál es mi nombre",
            "recuerdas mi nombre",
        )
        return any(marker in lowered for marker in markers)

    def _extract_name_from_prompt(self, prompt: str) -> Optional[str]:
        lowered = prompt.lower().strip()
        markers = ["me llamo ", "mi nombre es ", "soy "]
        for marker in markers:
            if marker in lowered:
                start = lowered.find(marker)
                extracted = prompt[start + len(marker):].strip()
                if not extracted:
                    return None
                token = extracted.split()[0].strip(".,;:!?\"'()[]{}")
                if not token:
                    return None
                return token[:1].upper() + token[1:].lower()
        return None

    def _normalize_response_content(self, response: Any) -> str:
        content = getattr(response, "content", response)

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and item.get("text"):
                    parts.append(str(item["text"]))
                elif hasattr(item, "text"):
                    parts.append(str(item.text))
            return "\n".join(
                part.strip() for part in parts if part and str(part).strip()
            )

        return str(content).strip() if content else ""
