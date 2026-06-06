"""Checkpointer SQLite para el agente LangGraph.

Usa SqliteSaver de LangGraph como equivalente local de PostgresSaver.
La conexión se abre una sola vez al inicio del proceso y se reutiliza
en todas las invocaciones del agente.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from settings import DATA_DIR

CHECKPOINT_DB_PATH = str(DATA_DIR / "agent_checkpoints.sqlite3")

# Conexión persistente abierta una vez al importar el módulo.
# SqliteSaver requiere una conexión activa, no un context manager.
Path(CHECKPOINT_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
_conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
_checkpointer = SqliteSaver(_conn)


def get_checkpointer() -> SqliteSaver:
    """Devuelve el SqliteSaver singleton del proceso.

    SqliteSaver es el equivalente local de PostgresSaver; ambos implementan
    BaseCheckpointSaver de LangGraph y persisten el estado del grafo por
    thread_id (número de teléfono / sesión).
    """
    return _checkpointer
