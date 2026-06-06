"""Cliente HTTP entre el puente de WhatsApp y la API del agente."""

from __future__ import annotations

import os

import requests

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8000/chat")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")
TIMEOUT = float(os.getenv("AGENT_TIMEOUT_MS", "180000")) / 1000.0

FALLBACK = "Intenta de nuevo en un momento."


def ask(numero: str, user_text: str) -> str:
    headers = {"Content-Type": "application/json"}
    if AGENT_API_KEY:
        headers["Authorization"] = f"Bearer {AGENT_API_KEY}"

    payload = {
        "message": user_text,
        "numero": str(numero).strip(),
    }

    try:
        resp = requests.post(AGENT_URL, json=payload, headers=headers, timeout=TIMEOUT)
        raw_text = resp.text.strip()

        try:
            data = resp.json()
        except ValueError:
            return raw_text or FALLBACK

        if isinstance(data, str):
            return data.strip() or FALLBACK

        if isinstance(data, dict):
            for key in ("response", "reply", "message", "content", "text", "output"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

            if data.get("error"):
                return f"⚠️ {data['error']}"

        return raw_text or FALLBACK

    except requests.Timeout:
        return f"El agente está tardando demasiado. {FALLBACK}"
    except requests.RequestException:
        return f"No pude contactar al agente en este momento. {FALLBACK}"