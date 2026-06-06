"""Puerta HTTP para el agente Manuelita, consumida por el puente de WhatsApp."""

from __future__ import annotations

import os
import traceback

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

from fastapi import FastAPI, HTTPException
import uvicorn

from agent_service import AgentService
from chat_memory import ChatMemoryService
from db import get_setting, initialize_database, load_all_settings, save_setting
from env_utils import load_environment
from langsmith_config import configure_langsmith
from llm_factory import get_model_catalog
from schemas import ChatRequest, ChatResponse
from sqlite_checkpointer import get_checkpointer

load_environment()
configure_langsmith()
initialize_database()

# Inicializa el checkpointer al arranque para crear las tablas de LangGraph si no existen.
_checkpointer = get_checkpointer()

app = FastAPI(title="API del agente Manuelita")
_model_catalog = get_model_catalog()


def _chat_id_for(numero: str) -> int:
    key = f"wa_chat::{numero}"
    chat_id = get_setting(key)
    if chat_id is None:
        chat_id = ChatMemoryService.create_new_chat()
        save_setting(key, chat_id)
    return int(chat_id)


def _pick_model(app_settings):
    label = app_settings.get("default_model")
    if label not in _model_catalog:
        label = next(iter(_model_catalog))
    return _model_catalog[label]


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    try:
        numero = body.numero.strip()
        if not numero:
            raise HTTPException(status_code=400, detail="El campo 'numero' es obligatorio.")

        app_settings = load_all_settings()
        model_config = _pick_model(app_settings)

        chat_id = _chat_id_for(numero)
        memory = ChatMemoryService(chat_id=chat_id, session_id=numero)
        agent = AgentService(memory)

        print(f"[agent_api] numero={numero} chat_id={chat_id} message={body.message!r}")

        memory.append_user_message(body.message, model_used=model_config["model"])
        result = agent.answer_question(body.message, model_config, app_settings)
        memory.append_assistant_message(
            content=result["answer"],
            route_used=result["route"],
            model_used=model_config["model"],
            tool_used=result["tool_used"],
            metadata=result["metadata"],
        )

        return ChatResponse(
            response=result["answer"],
            numero=numero,
            chat_id=chat_id,
            route=result["route"],
            tool_used=result["tool_used"],
            metadata=result["metadata"],
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        return ChatResponse(
            response=f"[ERROR del agente] {type(e).__name__}: {e}",
            numero=body.numero,
            route="error",
            tool_used="none",
            metadata={},
        )


@app.get("/status")
def status():
    return {"ok": True, "modelos": list(_model_catalog.keys())}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
