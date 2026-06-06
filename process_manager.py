"""Gestión de subprocesos para agent_api.py y server.py.

Lanza cada proceso con subprocess, captura stdout/stderr en threads
daemon y expone el estado, logs y detección de QR para la UI Streamlit.
"""

from __future__ import annotations

import re
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path
from typing import Deque, Dict, List, Optional

import requests

# ── Configuración ─────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
LOG_MAXLEN = 300          # líneas máximas por buffer
QR_MIN_LINES = 5         # mínimo de líneas para considerar un bloque QR
HEALTH_TIMEOUT = 2.0     # segundos para health check HTTP

SERVICES: Dict[str, Dict] = {
    "agent": {
        "label":   "Agente API",
        "script":  "agent_api.py",
        "port":    8000,
        "url":     "http://localhost:8000/status",
        "color":   "#1E8449",
    },
    "bridge": {
        "label":   "Puente WhatsApp",
        "script":  "server.py",
        "port":    3000,
        "url":     "http://localhost:3000/status",
        "color":   "#2471A3",
    },
}

# ── Estado global de procesos (compartido entre threads) ──────────────────────
_state: Dict[str, Dict] = {
    key: {
        "process":   None,       # subprocess.Popen
        "pid":       None,
        "status":    "stopped",  # stopped | starting | online | error
        "logs":      deque(maxlen=LOG_MAXLEN),
        "qr_block":  None,       # str con el bloque QR detectado
        "lock":      threading.Lock(),
    }
    for key in SERVICES
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_ansi(text: str) -> str:
    """Elimina códigos de escape ANSI (colores de terminal)."""
    return re.sub(r"\x1b\[[0-9;]*[mGKHF]", "", text)


def _is_qr_line(line: str) -> bool:
    """Detecta si una línea forma parte de un bloque QR ASCII."""
    qr_chars = {"█", "▀", "▄", "▌", "▐", "░", "▒", "▓", "■", "□"}
    stripped = line.strip()
    if not stripped:
        return False
    char_count = sum(1 for c in stripped if c in qr_chars)
    return char_count > len(stripped) * 0.3


def _reader_thread(key: str, stream, label: str) -> None:
    """Lee líneas de stdout/stderr y las guarda en el buffer de logs.
    Detecta bloques QR y los guarda por separado.
    """
    state  = _state[key]
    qr_buf: List[str] = []
    in_qr  = False

    try:
        for raw_line in iter(stream.readline, ""):
            line = _strip_ansi(raw_line).rstrip("\n").rstrip("\r")
            if not line and not in_qr:
                continue

            # Detección de QR
            if _is_qr_line(line):
                in_qr = True
                qr_buf.append(line)
            else:
                if in_qr:
                    if len(qr_buf) >= QR_MIN_LINES:
                        with state["lock"]:
                            state["qr_block"] = "\n".join(qr_buf)
                    qr_buf = []
                    in_qr  = False

                if line:
                    entry = f"[{label}] {line}"
                    with state["lock"]:
                        state["logs"].append(entry)
                        # Detectar arranque exitoso
                        up_signals = ("uvicorn running", "application startup complete",
                                      "started server", "connected", "listening")
                        if any(s in line.lower() for s in up_signals):
                            state["status"] = "online"
                        err_signals = ("error", "exception", "traceback", "failed")
                        if any(s in line.lower() for s in err_signals):
                            state["status"] = "error"
    except Exception:
        pass
    finally:
        stream.close()


# ── API pública ───────────────────────────────────────────────────────────────

def start_service(key: str) -> bool:
    """Inicia el servicio indicado. Devuelve True si se lanzó correctamente."""
    cfg   = SERVICES[key]
    state = _state[key]

    with state["lock"]:
        proc = state["process"]
        if proc is not None and proc.poll() is None:
            return True  # ya está corriendo

        state["status"]   = "starting"
        state["qr_block"] = None
        state["logs"].clear()

    script = BASE_DIR / cfg["script"]
    try:
        proc = subprocess.Popen(
            [sys.executable, "-u", str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            cwd=str(BASE_DIR),
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        )
    except Exception as e:
        with state["lock"]:
            state["status"] = "error"
            state["logs"].append(f"[ERROR] No se pudo iniciar {cfg['script']}: {e}")
        return False

    with state["lock"]:
        state["process"] = proc
        state["pid"]     = proc.pid

    # Thread daemon para leer logs
    t = threading.Thread(
        target=_reader_thread,
        args=(key, proc.stdout, cfg["label"]),
        daemon=True,
    )
    t.start()

    return True


def stop_service(key: str) -> None:
    """Detiene el servicio indicado."""
    state = _state[key]
    with state["lock"]:
        proc = state["process"]
        if proc is None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        state["process"] = None
        state["pid"]     = None
        state["status"]  = "stopped"
        state["qr_block"] = None


def restart_service(key: str) -> bool:
    """Detiene y vuelve a iniciar el servicio."""
    stop_service(key)
    return start_service(key)


def get_status(key: str) -> str:
    """Devuelve el estado actual: stopped | starting | online | error."""
    state = _state[key]
    proc  = state["process"]

    if proc is None:
        return "stopped"

    if proc.poll() is not None:
        with state["lock"]:
            state["process"] = None
            state["pid"]     = None
            state["status"]  = "stopped"
        return "stopped"

    # Verificar via HTTP si el proceso dice 'starting'
    if state["status"] == "starting":
        try:
            r = requests.get(SERVICES[key]["url"], timeout=HEALTH_TIMEOUT)
            if r.status_code == 200:
                with state["lock"]:
                    state["status"] = "online"
        except Exception:
            pass

    return state["status"]


def get_pid(key: str) -> Optional[int]:
    return _state[key]["pid"]


def get_logs(key: str) -> List[str]:
    with _state[key]["lock"]:
        return list(_state[key]["logs"])


def get_qr(key: str) -> Optional[str]:
    with _state[key]["lock"]:
        return _state[key]["qr_block"]


def clear_qr(key: str) -> None:
    with _state[key]["lock"]:
        _state[key]["qr_block"] = None


def health_check(key: str) -> bool:
    """Hace un GET al endpoint /status del servicio. Devuelve True si responde OK."""
    try:
        r = requests.get(SERVICES[key]["url"], timeout=HEALTH_TIMEOUT)
        return r.status_code == 200
    except Exception:
        return False


def whatsapp_connected() -> bool:
    """Consulta el estado de conexión de WhatsApp via server.py."""
    try:
        r = requests.get(SERVICES["bridge"]["url"], timeout=HEALTH_TIMEOUT)
        if r.status_code == 200:
            return r.json().get("whatsappConnected", False)
    except Exception:
        pass
    return False
