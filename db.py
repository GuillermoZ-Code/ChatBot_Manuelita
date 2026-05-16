"""Persistencia SQLite para conversaciones, mensajes, perfil de usuario y configuración."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

from settings import DB_PATH, DEFAULT_SETTINGS


def utc_now() -> str:
    """Retorna la marca de tiempo UTC en formato ISO."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Abre una conexión SQLite con row factory habilitado."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    """Crea las tablas necesarias si aún no existen."""
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_archived INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                route_used TEXT,
                model_used TEXT,
                tool_used TEXT,
                created_at TEXT NOT NULL,
                metadata_json TEXT,
                FOREIGN KEY(chat_id) REFERENCES chats(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_profile (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

    for key, value in DEFAULT_SETTINGS.items():
        save_setting(key, value, overwrite=False)


def create_chat(title: str = "Nuevo chat") -> int:
    """Crea un nuevo chat persistente y retorna su identificador."""
    now = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO chats (title, created_at, updated_at)
            VALUES (?, ?, ?)
            """,
            (title, now, now),
        )
        return int(cursor.lastrowid)


def list_chats() -> List[Dict[str, Any]]:
    """Lista los chats disponibles ordenados por actualización descendente."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM chats
            WHERE is_archived = 0
            ORDER BY datetime(updated_at) DESC, id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_chat(chat_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un chat por identificador."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, title, created_at, updated_at FROM chats WHERE id = ?",
            (chat_id,),
        ).fetchone()
    return dict(row) if row else None


def rename_chat(chat_id: int, new_title: str) -> None:
    """Actualiza el título de una conversación existente."""
    with get_connection() as connection:
        connection.execute(
            "UPDATE chats SET title = ?, updated_at = ? WHERE id = ?",
            (new_title.strip(), utc_now(), chat_id),
        )


def delete_chat(chat_id: int) -> None:
    """Elimina un chat y todos sus mensajes asociados."""
    with get_connection() as connection:
        connection.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        connection.execute("DELETE FROM chats WHERE id = ?", (chat_id,))


def clear_all_data() -> None:
    """Borra conversaciones, perfil de usuario y configuración."""
    with get_connection() as connection:
        connection.execute("DELETE FROM messages")
        connection.execute("DELETE FROM chats")
        connection.execute("DELETE FROM user_profile")
        connection.execute("DELETE FROM app_settings")

    for key, value in DEFAULT_SETTINGS.items():
        save_setting(key, value, overwrite=False)


def add_message(
    chat_id: int,
    role: str,
    content: str,
    route_used: str = "",
    model_used: str = "",
    tool_used: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """Guarda un mensaje dentro de una conversación."""
    created_at = utc_now()
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO messages (
                chat_id, role, content, route_used, model_used, tool_used,
                created_at, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                role,
                content,
                route_used,
                model_used,
                tool_used,
                created_at,
                metadata_json,
            ),
        )
        connection.execute(
            "UPDATE chats SET updated_at = ? WHERE id = ?",
            (created_at, chat_id),
        )
        return int(cursor.lastrowid)


def list_messages(chat_id: int) -> List[Dict[str, Any]]:
    """Lista mensajes de una conversación en orden cronológico."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, chat_id, role, content, route_used, model_used,
                   tool_used, created_at, metadata_json
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (chat_id,),
        ).fetchall()

    messages: List[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        messages.append(item)
    return messages


def save_setting(key: str, value: Any, overwrite: bool = True) -> None:
    """Guarda un ajuste de aplicación como JSON."""
    payload = json.dumps(value, ensure_ascii=False)
    now = utc_now()
    with get_connection() as connection:
        exists = connection.execute(
            "SELECT 1 FROM app_settings WHERE key = ?",
            (key,),
        ).fetchone()
        if exists and not overwrite:
            return
        connection.execute(
            """
            INSERT INTO app_settings (key, value_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value_json = excluded.value_json, updated_at = excluded.updated_at
            """,
            (key, payload, now),
        )


def get_setting(key: str, default: Any = None) -> Any:
    """Recupera un ajuste persistido o retorna el valor por defecto."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT value_json FROM app_settings WHERE key = ?",
            (key,),
        ).fetchone()
    if not row:
        return default
    return json.loads(row["value_json"])


def load_all_settings() -> Dict[str, Any]:
    """Carga todos los ajustes persistidos."""
    with get_connection() as connection:
        rows = connection.execute("SELECT key, value_json FROM app_settings").fetchall()
    settings = DEFAULT_SETTINGS.copy()
    for row in rows:
        settings[row["key"]] = json.loads(row["value_json"])
    return settings


def save_user_fact(key: str, value: Any) -> None:
    """Guarda un hecho persistente del usuario."""
    now = utc_now()
    payload = json.dumps(value, ensure_ascii=False)
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO user_profile (key, value_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value_json = excluded.value_json, updated_at = excluded.updated_at
            """,
            (key, payload, now),
        )


def get_user_fact(key: str, default: Any = None) -> Any:
    """Recupera un hecho persistente del usuario."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT value_json FROM user_profile WHERE key = ?",
            (key,),
        ).fetchone()
    if not row:
        return default
    return json.loads(row["value_json"])


def load_user_profile() -> Dict[str, Any]:
    """Carga todo el perfil persistente del usuario."""
    with get_connection() as connection:
        rows = connection.execute("SELECT key, value_json FROM user_profile").fetchall()
    profile: Dict[str, Any] = {}
    for row in rows:
        profile[row["key"]] = json.loads(row["value_json"])
    return profile
