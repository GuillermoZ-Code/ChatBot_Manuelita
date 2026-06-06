"""server.py
Punto de entrada: conecta WhatsApp con tu agente y expone una API REST con FastAPI.
"""

import os
import threading
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from agent import ask, reset
import whatsapp

app = FastAPI(title="Puente WhatsApp <-> Agente")


# Qué hacer con cada mensaje entrante: pasarlo al agente y responder.
def handle_message(chat_jid, text, client):
    numero = chat_jid.User  # número limpio de quien escribe, ej. "573103716572"
    print(f"📥 {numero}: {text}")
    reply = ask(numero, text)  # se envía el número para mantener el historial
    client.send_message(chat_jid, reply)
    print(f"📤 {numero}: {reply}")


wa_client = whatsapp.create_whatsapp(handle_message)


def _run_whatsapp():
    # connect() inicia la conexión y muestra el QR en la terminal la 1ª vez.
    wa_client.connect()


# WhatsApp corre en un hilo aparte; FastAPI se queda en el hilo principal.
threading.Thread(target=_run_whatsapp, daemon=True).start()


# ---- Modelos de los cuerpos JSON ----
class SendBody(BaseModel):
    to: str
    message: str


class ChatBody(BaseModel):
    chatId: str = "api-test"
    message: str


class ResetBody(BaseModel):
    chatId: Optional[str] = None


# ---- Endpoints ----
@app.get("/status")
def status():
    return {"whatsappConnected": whatsapp.is_connected()}


@app.post("/send")
def send(body: SendBody):
    if not whatsapp.is_connected():
        return {"error": "WhatsApp aún no está conectado."}
    whatsapp.send(body.to, body.message)
    return {"ok": True, "to": body.to}


@app.post("/chat")
def chat(body: ChatBody):
    return {"reply": ask(body.chatId, body.message)}


@app.post("/reset")
def reset_endpoint(body: ResetBody):
    reset(body.chatId)
    return {"ok": True}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "3000"))
    print(f"🚀 API REST en http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
