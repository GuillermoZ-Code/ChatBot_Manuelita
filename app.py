"""Panel de control operativo — Asistente Virtual Manuelita S.A.

Ejecutar con:
    uv run streamlit run app.py
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

import streamlit as st

import process_manager as pm
from db import initialize_database, list_messages, load_all_settings, save_setting
from env_utils import load_environment
from llm_factory import get_model_catalog
from settings import APP_ICON, APP_TITLE
from ui_components import (
    CUSTOM_CSS,
    HEADER_HTML,
    SIDEBAR_BRAND_HTML,
    log_lines_html,
    msg_bubble_html,
    status_bar_html,
)

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Panel Operativo — Manuelita S.A.",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

MAX_MESSAGES_FEED = 120       # mensajes máximos en el feed de conversaciones


# ── Estado de sesión ──────────────────────────────────────────────────────────

def init_state() -> None:
    defaults = {
        "model_catalog":      {},
        "last_refresh":       0.0,
        "monitor_running":    False,
        "selected_session":   None,   # número filtrado en monitoreo
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Helpers ───────────────────────────────────────────────────────────────────

def _service_info() -> Dict[str, Dict]:
    """Devuelve estado enriquecido de cada servicio para la status bar."""
    result = {}
    for key, cfg in pm.SERVICES.items():
        result[key] = {
            "label":        cfg["label"],
            "port":         cfg["port"],
            "status":       pm.get_status(key),
            "pid":          pm.get_pid(key),
            "wa_connected": pm.whatsapp_connected() if key == "bridge" else False,
        }
    return result


def _all_messages() -> List[Dict[str, Any]]:
    """Lee todos los mensajes de todas las sesiones ordenados por id."""
    from db import get_connection
    with get_connection() as conn:
        import json
        rows = conn.execute(
            """
            SELECT m.id, m.chat_id, m.role, m.content,
                   m.route_used, m.model_used, m.tool_used,
                   m.created_at, m.metadata_json
            FROM messages m
            ORDER BY m.id DESC
            LIMIT ?
            """,
            (MAX_MESSAGES_FEED,),
        ).fetchall()
    msgs = []
    for row in rows:
        item = dict(row)
        import json
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        msgs.append(item)
    return list(reversed(msgs))


def _sessions() -> List[str]:
    """Lista de session_ids únicos presentes en la DB."""
    from db import get_connection
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT json_extract(metadata_json, '$.session_id') as sid
            FROM messages
            WHERE json_extract(metadata_json, '$.session_id') IS NOT NULL
            ORDER BY sid
            """
        ).fetchall()
    return [r["sid"] for r in rows if r["sid"]]


# ── Sidebar — configuración ───────────────────────────────────────────────────

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(SIDEBAR_BRAND_HTML, unsafe_allow_html=True)
        st.markdown("---")

        # Catálogo de modelos
        st.markdown("#### 🤖 Modelo LLM")
        if st.button("↺ Recargar modelos", use_container_width=True):
            st.session_state.model_catalog = get_model_catalog()
            st.rerun()

        catalog = st.session_state.model_catalog
        if not catalog:
            st.caption("Sin modelos disponibles. Verifica Ollama o API keys.")
        else:
            st.caption(f"{len(catalog)} modelo(s) disponible(s)")

        st.markdown("---")

        # Parámetros
        st.markdown("#### ⚙️ Parámetros del agente")
        settings = load_all_settings()
        available = list(catalog.keys()) if catalog else []

        default_idx = 0
        if settings.get("default_model") in available:
            default_idx = available.index(settings["default_model"])

        sel_model = st.selectbox(
            "Modelo por defecto",
            available if available else ["(sin modelos)"],
            index=default_idx,
            disabled=not available,
        )
        temperature    = st.slider("Temperatura",         0.0,  1.5,   float(settings["temperature"]),    0.05)
        top_p          = st.slider("Top-p",               0.1,  1.0,   float(settings["top_p"]),          0.05)
        num_predict    = st.slider("Máx. tokens salida",  128,  4096,  int(settings["num_predict"]),      64)
        rag_k          = st.slider("Fragmentos RAG",      1,    8,     int(settings["rag_k"]),             1)
        num_ctx        = st.slider("Ventana contexto",    1024, 32768, int(settings["num_ctx"]),           512)
        repeat_penalty = st.slider("Repeat penalty",      1.0,  2.0,   float(settings["repeat_penalty"]), 0.05)
        char_limit     = st.number_input(
            "Límite caracteres/msg", min_value=50, max_value=10000,
            value=int(settings["question_char_limit"]), step=50,
        )
        extra_prompt   = st.text_area(
            "Instrucciones extra del sistema",
            value=settings.get("system_prompt_extra", ""),
            height=100,
        )

        if st.button("💾 Guardar configuración", use_container_width=True, type="primary"):
            payload = {
                "default_model":      sel_model,
                "temperature":        temperature,
                "top_p":              top_p,
                "num_predict":        num_predict,
                "rag_k":              rag_k,
                "num_ctx":            num_ctx,
                "repeat_penalty":     repeat_penalty,
                "question_char_limit": char_limit,
                "system_prompt_extra": extra_prompt,
            }
            for k, v in payload.items():
                save_setting(k, v)
            st.success("✅ Configuración guardada.")


# ── Tab: Servicios ────────────────────────────────────────────────────────────

def render_tab_servicios() -> None:
    st.markdown("### Gestión de servicios")

    for key, cfg in pm.SERVICES.items():
        status = pm.get_status(key)
        pid    = pm.get_pid(key)
        qr     = pm.get_qr(key)

        status_emoji = {"online": "🟢", "starting": "🟡", "error": "🔴", "stopped": "⚫"}.get(status, "⚫")
        status_label = {"online": "En línea", "starting": "Iniciando...",
                        "error": "Error", "stopped": "Detenido"}.get(status, status)

        with st.container():
            st.markdown(f"""
            <div class="service-card">
                <h3>{status_emoji} {cfg['label']}</h3>
                <div class="meta">Puerto {cfg['port']} · {status_label}{f' · PID {pid}' if pid else ''}</div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
            with col1:
                if st.button("▶ Iniciar", key=f"start_{key}", use_container_width=True,
                             disabled=(status in ("online", "starting"))):
                    pm.start_service(key)
                    time.sleep(0.5)
                    st.rerun()
            with col2:
                if st.button("⏹ Detener", key=f"stop_{key}", use_container_width=True,
                             disabled=(status == "stopped")):
                    pm.stop_service(key)
                    st.rerun()
            with col3:
                if st.button("↺ Reiniciar", key=f"restart_{key}", use_container_width=True,
                             disabled=(status == "stopped")):
                    pm.restart_service(key)
                    time.sleep(0.5)
                    st.rerun()
            with col4:
                health = pm.health_check(key)
                if health:
                    st.success(f"✅ Respondiendo en localhost:{cfg['port']}")
                elif status != "stopped":
                    st.warning(f"⏳ Sin respuesta en localhost:{cfg['port']}")

            # QR de WhatsApp
            if key == "bridge" and qr:
                st.markdown("""
                <div class="qr-container">
                    <h4>📱 Escanea el código QR con WhatsApp</h4>
                    <p style="color:#6c756d;font-size:0.85rem;margin-bottom:10px;">
                        Abre WhatsApp → Dispositivos vinculados → Vincular dispositivo
                    </p>
                </div>
                """, unsafe_allow_html=True)
                st.code(qr, language=None)
                if st.button("✓ Ya escaneé el QR", key="clear_qr"):
                    pm.clear_qr("bridge")
                    st.rerun()
            elif key == "bridge" and status == "online":
                wa_ok = pm.whatsapp_connected()
                if wa_ok:
                    st.success("📱 WhatsApp conectado")
                else:
                    st.info("📱 WhatsApp aún no conectado — iniciando sesión...")

            # Logs del servicio
            with st.expander(f"📋 Logs recientes — {cfg['label']}", expanded=(status == "error")):
                logs = pm.get_logs(key)
                if logs:
                    st.markdown(log_lines_html(logs), unsafe_allow_html=True)
                else:
                    st.caption("Sin logs aún.")

        st.markdown("---")

    # Arrancar ambos
    st.markdown("#### Arranque rápido")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("▶▶ Iniciar todos los servicios", use_container_width=True, type="primary"):
            pm.start_service("agent")
            time.sleep(1)
            pm.start_service("bridge")
            time.sleep(0.5)
            st.rerun()
    with col_b:
        if st.button("⏹⏹ Detener todos", use_container_width=True):
            pm.stop_service("bridge")
            pm.stop_service("agent")
            st.rerun()


# ── Tab: Conversaciones ───────────────────────────────────────────────────────

def render_tab_conversaciones() -> None:
    st.markdown("### Monitor de conversaciones en tiempo real")

    # Filtro de sesión — fuera del fragment para no resetear al refrescar
    sessions = ["Todas las sesiones"] + _sessions()
    sel = st.selectbox("Filtrar por número / sesión", sessions, key="session_filter")
    st.session_state.selected_session = None if sel == "Todas las sesiones" else sel

    st.markdown("---")

    # Fragment con auto-refresh cada 5 segundos — solo refresca este bloque
    @st.fragment(run_every=5)
    def _feed() -> None:
        msgs = _all_messages()

        if st.session_state.get("selected_session"):
            msgs = [m for m in msgs
                    if m.get("metadata", {}).get("session_id") == st.session_state.selected_session]

        if not msgs:
            st.info("Sin conversaciones registradas aún. Los mensajes aparecerán aquí cuando WhatsApp esté activo.")
            return

        current_session = None
        html_parts = ['<div class="conv-feed">']
        for msg in msgs:
            sid = msg.get("metadata", {}).get("session_id", "desconocido")
            if sid != current_session:
                current_session = sid
                html_parts.append(f'<div class="session-pill">📱 Sesión: {sid}</div>')
            html_parts.append(msg_bubble_html(msg))
        html_parts.append("</div>")
        st.markdown("".join(html_parts), unsafe_allow_html=True)

        st.markdown("---")
        total_users = len([m for m in msgs if m["role"] == "user"])
        total_agent = len([m for m in msgs if m["role"] == "assistant"])
        sessions_count = len(set(
            m.get("metadata", {}).get("session_id", "") for m in msgs
        ))
        routes = [m.get("route_used") for m in msgs if m.get("route_used")]

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Mensajes usuario", total_users)
        mc2.metric("Respuestas agente", total_agent)
        mc3.metric("Sesiones activas", sessions_count)
        mc4.metric("Interacciones totales", total_users + total_agent)

        if routes:
            from collections import Counter
            route_counts = Counter(routes)
            st.markdown("**Distribución de rutas:**")
            cols = st.columns(len(route_counts))
            for i, (route, count) in enumerate(route_counts.most_common()):
                cols[i].metric(route, count)

    _feed()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    load_environment()
    initialize_database()
    init_state()

    # Cargar catálogo una vez por sesión
    if not st.session_state.model_catalog:
        st.session_state.model_catalog = get_model_catalog()

    # CSS global
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Header
    st.markdown(HEADER_HTML, unsafe_allow_html=True)

    # Status bar superior
    svc_info = _service_info()
    st.markdown(status_bar_html(svc_info), unsafe_allow_html=True)

    # Sidebar
    render_sidebar()

    # Tabs principales
    tab_svc, tab_conv = st.tabs([
        "🖥️  Servicios",
        "💬  Conversaciones",
    ])

    with tab_svc:
        render_tab_servicios()

    with tab_conv:
        render_tab_conversaciones()


if __name__ == "__main__":
    main()
