"""Servicios de memoria conversacional persistente."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from db import (
    add_message,
    create_chat,
    get_chat,
    list_messages,
    rename_chat,
    save_user_fact,
    get_user_fact,
    load_user_profile,
)
from settings import DEFAULT_CHAT_TITLE_LIMIT, DEFAULT_HISTORY_TURNS


class ChatMemoryService:
    """Gestiona una conversación persistida en SQLite."""

    def __init__(self, chat_id: int) -> None:
        """Inicializa el servicio con un chat existente."""
        self.chat_id = chat_id

    @staticmethod
    def create_new_chat() -> int:
        """Crea un chat nuevo con título temporal."""
        return create_chat("Nuevo chat")

    def get_messages(self) -> List[Dict[str, Any]]:
        """Retorna los mensajes persistidos del chat."""
        return list_messages(self.chat_id)

    def get_user_profile(self) -> Dict[str, Any]:
        """Retorna el perfil persistente del usuario."""
        return load_user_profile()

    def get_user_fact(self, key: str, default: Any = None) -> Any:
        """Obtiene un dato persistente del usuario."""
        return get_user_fact(key, default)

    def save_user_fact(self, key: str, value: Any) -> None:
        """Guarda un dato persistente del usuario."""
        save_user_fact(key, value)

    def append_user_message(self, content: str, model_used: str = "") -> None:
        """Guarda un mensaje del usuario y actualiza el título si aplica."""
        add_message(
            chat_id=self.chat_id,
            role="user",
            content=content,
            model_used=model_used,
            metadata={"source": "chat"},
        )
        self._extract_user_facts(content)
        self._ensure_title_from_first_message(content)

    def append_assistant_message(
        self,
        content: str,
        route_used: str,
        model_used: str,
        tool_used: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Guarda un mensaje del asistente con metadatos."""
        add_message(
            chat_id=self.chat_id,
            role="assistant",
            content=content,
            route_used=route_used,
            model_used=model_used,
            tool_used=tool_used,
            metadata=metadata,
        )

    def get_recent_history_text(self, limit: int = DEFAULT_HISTORY_TURNS) -> str:
        """Construye un historial corto para el prompt del agente."""
        messages = self.get_messages()[-limit:]
        if not messages:
            return "Sin historial previo."

        lines = []
        for item in messages:
            role = "Usuario" if item["role"] == "user" else "Asistente"
            lines.append(f"{role}: {item['content']}")
        return "".join(lines)

    def _ensure_title_from_first_message(self, first_message: str) -> None:
        """Genera un título automático a partir del primer mensaje útil."""
        chat = get_chat(self.chat_id)
        if not chat:
            return
        if chat["title"] != "Nuevo chat":
            return

        title = first_message.strip().replace("", " ")
        if not title:
            return
        title = title[:DEFAULT_CHAT_TITLE_LIMIT].rstrip()
        rename_chat(self.chat_id, title)

    def _extract_user_facts(self, content: str) -> None:
        """Extrae datos personales simples del usuario para memoria global."""
        lowered = content.lower().strip()
        markers = ["me llamo ", "mi nombre es ", "soy "]
        for marker in markers:
            if marker in lowered:
                raw = content.lower().split(marker, 1)[1].strip()
                name = raw.split()[0].strip().capitalize()
                if name:
                    self.save_user_fact("name", name)
                break
