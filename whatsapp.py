"""whatsapp.py
Capa de conexión a WhatsApp usando neonize (binding de whatsmeow).
Corre 100% local, muestra un QR en la terminal la primera vez y guarda la sesión.
"""

import os
from neonize.client import NewClient
from neonize.events import ConnectedEv, DisconnectedEv, MessageEv
from neonize.utils import build_jid

_client = None
_connected = {"value": False}
REPLY_IN_GROUPS = os.getenv("REPLY_IN_GROUPS", "false").lower() == "true"


def _extract_text(message) -> str:
    """Saca el texto del mensaje, ya sea simple o 'extendido' (con cita/formato)."""
    if message.conversation:
        return message.conversation
    if message.extendedTextMessage and message.extendedTextMessage.text:
        return message.extendedTextMessage.text
    return ""


def create_whatsapp(on_message):
    """Crea el cliente de WhatsApp y registra los manejadores.
    on_message(chat_jid, text, client) se llama con cada mensaje entrante."""
    global _client
    client = NewClient(os.getenv("WA_SESSION_DB", "./neonize.db"))
    _client = client

    @client.event(ConnectedEv)
    def _on_connected(c, e):
        _connected["value"] = True
        print("✅ WhatsApp conectado y listo.")

    @client.event(DisconnectedEv)
    def _on_disconnected(c, e):
        _connected["value"] = False
        print("⚠️  WhatsApp desconectado.")

    @client.event(MessageEv)
    def _on_message(c, e):
        try:
            src = e.Info.MessageSource
            if src.IsFromMe:
                return
            if src.IsGroup and not REPLY_IN_GROUPS:
                return
            text = _extract_text(e.Message)
            if not text:
                return  # ignora audios/imágenes/etc. sin texto
            on_message(src.Chat, text, c)
        except Exception as err:
            print("Error procesando mensaje entrante:", err)

    return client


def is_connected() -> bool:
    return _connected["value"]


def send(to: str, text: str):
    """Envía un mensaje. 'to' puede ser un número (ej. '573001112233')."""
    if _client is None:
        raise RuntimeError("Cliente de WhatsApp no inicializado.")
    jid = build_jid(str(to))
    _client.send_message(jid, text)
