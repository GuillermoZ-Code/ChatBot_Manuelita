"""Puente WhatsApp <-> agente HTTP."""

from __future__ import annotations

import os
import threading

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn

from agent import ask
import whatsapp

load_dotenv()

app = FastAPI(title="Puente WhatsApp <-> Agente")


class SendBody(BaseModel):
    to: str = Field(..., min_length=3, description="Número destino")
    message: str = Field(..., min_length=1, description="Mensaje a enviar")


class ChatBody(BaseModel):
    numero: str = Field(..., min_length=3, description="Número o id de sesión a simular")
    message: str = Field(..., min_length=1, description="Mensaje a enviar al agente")


def handle_message(chat_jid, text, client) -> None:
    numero = str(chat_jid.User).strip()
    print(f"📥 {numero}: {text}")

    reply = ask(numero, text)

    client.send_message(chat_jid, reply)
    print(f"📤 {numero}: {reply}")


wa_client = whatsapp.create_whatsapp(handle_message)


def _run_whatsapp() -> None:
    wa_client.connect()


def start_whatsapp_bridge() -> None:
    threading.Thread(target=_run_whatsapp, daemon=True).start()


start_whatsapp_bridge()


@app.get("/status")
def status():
    return {
        "ok": True,
        "whatsappConnected": whatsapp.is_connected(),
        "agentUrlConfigured": bool(os.getenv("AGENT_URL", "http://localhost:8000/chat")),
    }


@app.post("/send")
def send(body: SendBody):
    if not whatsapp.is_connected():
        return {"ok": False, "error": "WhatsApp aún no está conectado."}

    whatsapp.send(body.to.strip(), body.message)
    return {"ok": True, "to": body.to.strip()}


@app.post("/chat")
def chat(body: ChatBody):
    reply = ask(body.numero.strip(), body.message)
    return {
        "ok": True,
        "numero": body.numero.strip(),
        "reply": reply,
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "3000"))
    print(f"🚀 Puente WhatsApp en http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)