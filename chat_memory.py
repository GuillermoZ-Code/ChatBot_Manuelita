"""Servicios de memoria conversacional persistente."""

from __future__ import annotations

from typing import Any, Dict, List

from db import (
    add_message,
    create_chat,
    get_chat,
    get_user_fact,
    list_messages,
    load_user_profile,
    rename_chat,
    save_user_fact,
)
from settings import DEFAULT_CHAT_TITLE_LIMIT, DEFAULT_HISTORY_TURNS


class ChatMemoryService:
    """Gestiona una conversación persistida en SQLite y perfil por sesión."""

    def __init__(self, chat_id: int, session_id: str) -> None:
        self.chat_id = int(chat_id)
        self.session_id = str(session_id).strip()

    @staticmethod
    def create_new_chat() -> int:
        return create_chat("Nuevo chat")

    def get_messages(self) -> List[Dict[str, Any]]:
        return list_messages(self.chat_id)

    def get_user_profile(self) -> Dict[str, Any]:
        return load_user_profile(self.session_id)

    def get_user_fact(self, key: str, default: Any = None) -> Any:
        return get_user_fact(self.session_id, key, default)

    def save_user_fact(self, key: str, value: Any) -> None:
        save_user_fact(self.session_id, key, value)

    def append_user_message(self, content: str, model_used: str = "") -> None:
        add_message(
            chat_id=self.chat_id,
            role="user",
            content=content,
            model_used=model_used,
            metadata={"source": "chat", "session_id": self.session_id},
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
        final_metadata = dict(metadata or {})
        final_metadata["session_id"] = self.session_id

        add_message(
            chat_id=self.chat_id,
            role="assistant",
            content=content,
            route_used=route_used,
            model_used=model_used,
            tool_used=tool_used,
            metadata=final_metadata,
        )

    def get_recent_history_text(self, limit: int = DEFAULT_HISTORY_TURNS) -> str:
        messages = self.get_messages()[-limit:]
        if not messages:
            return "Sin historial previo."

        lines = []
        for item in messages:
            role = "Usuario" if item["role"] == "user" else "Asistente"
            lines.append(f"{role}: {item['content']}")
        return "\n".join(lines)

    def _ensure_title_from_first_message(self, first_message: str) -> None:
        chat = get_chat(self.chat_id)
        if not chat or chat["title"] != "Nuevo chat":
            return

        title = " ".join(first_message.strip().split())
        if not title:
            return

        title = title[:DEFAULT_CHAT_TITLE_LIMIT].rstrip()
        rename_chat(self.chat_id, title)

    def _extract_user_facts(self, content: str) -> None:
        lowered = content.lower().strip()
        markers = ["me llamo ", "mi nombre es ", "soy "]

        for marker in markers:
            if marker in lowered:
                start = lowered.find(marker)
                extracted = content[start + len(marker):].strip()
                if not extracted:
                    return

                token = extracted.split()[0].strip(".,;:!?\"'()[]{}")
                if token:
                    normalized = token[:1].upper() + token[1:].lower()
                    self.save_user_fact("name", normalized)
                    return