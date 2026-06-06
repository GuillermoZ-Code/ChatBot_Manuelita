"""agent.py
Conecta el puente de WhatsApp con TU agente (un endpoint HTTP/REST).

Envía, además del mensaje, el NÚMERO de quien escribe, para que tu agente
pueda guardar y recuperar el historial de conversación por persona.

Contrato que envía el puente (ajústalo a lo que espere tu agente):
  POST {AGENT_URL}
  body: {"message": "<texto>", "numero": "573103716572", "sessionId": "573103716572"}
"""

import os
import requests

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8000/chat")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")  # opcional (Bearer)
TIMEOUT = float(os.getenv("AGENT_TIMEOUT_MS", "180000")) / 1000.0

FALLBACK = "Intenta de nuevo en un momento."


def ask(numero: str, user_text: str) -> str:
    """numero = teléfono de quien escribe (ej. '573103716572').
    Tu agente debe usarlo como clave del historial de conversación."""
    headers = {"Content-Type": "application/json"}
    if AGENT_API_KEY:
        headers["Authorization"] = f"Bearer {AGENT_API_KEY}"

    # 👇 AJUSTA los nombres de los campos a lo que reciba TU agente.
    payload = {
        "message": user_text,
        "numero": numero,      # número del remitente -> para el historial
        "sessionId": numero,   # alias común; deja solo el que use tu agente
    }

    try:
        resp = requests.post(AGENT_URL, json=payload, headers=headers, timeout=TIMEOUT)

        try:
            data = resp.json()
        except ValueError:
            return resp.text.strip() or FALLBACK

        if isinstance(data, str):
            return data.strip() or FALLBACK

        if isinstance(data, dict):
            # 👇 AJUSTA si tu campo de respuesta tiene otro nombre.
            for key in ("response", "reply", "message", "content", "text", "output"):
                if data.get(key):
                    return str(data[key]).strip()
            if data.get("error"):
                return f"⚠️ {data['error']}"

        return FALLBACK

    except requests.Timeout:
        return f"El agente está tardando demasiado. {FALLBACK}"
    except requests.RequestException:
        return f"No pude contactar al agente en este momento. {FALLBACK}"


def reset(numero=None) -> None:
    """Si tu agente expone un endpoint para borrar el historial, impleméntalo aquí."""
    return
