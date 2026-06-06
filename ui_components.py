"""Componentes visuales de la interfaz."""

CUSTOM_CSS = r"""<style>
:root {
    --m-green: #4b8f2f;
    --m-green-dark: #2f6f23;
    --m-green-soft: #eef4e6;
    --m-yellow: #ffd200;
    --m-orange: #ea6a1f;
    --m-olive: #a1ad1b;
    --m-bg: #f7f7f2;
    --m-surface: #ffffff;
    --m-border: #d8dfd1;
    --m-text: #3e4b3f;
    --m-muted: #6c756d;
}

html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

.stApp {
    background: linear-gradient(180deg, #fcfcf8 0%, #f3f6ee 100%);
    color: var(--m-text);
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f7f7f2 0%, #f1f3eb 100%);
    border-right: 1px solid var(--m-border);
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}

.brand-strip {
    display: flex;
    align-items: center;
    gap: 12px;
    background: var(--m-surface);
    border: 1px solid var(--m-border);
    border-radius: 18px;
    padding: 12px 14px;
    box-shadow: 0 8px 20px rgba(47,111,35,0.08);
    margin-bottom: 18px;
}

.brand-logo {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: conic-gradient(from 210deg, #f2a51a 0 26%, #4fa33b 26% 60%, #ffd200 60% 84%, #ea6a1f 84% 100%);
    box-shadow: inset 0 0 0 2px rgba(255,255,255,0.5);
}

.brand-name {
    font-weight: 800;
    font-size: 1.12rem;
    color: var(--m-green-dark);
    line-height: 1;
}

.main-header {
    position: relative;
    overflow: hidden;
    background: linear-gradient(90deg, var(--m-green-dark), var(--m-green) 55%, #5e9a32 100%);
    color: white;
    border-radius: 22px;
    padding: 20px 28px;
    box-shadow: 0 14px 32px rgba(47,111,35,0.18);
    margin-bottom: 16px;
}

.main-header::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(120deg, rgba(255,255,255,0.08), rgba(255,255,255,0));
    pointer-events: none;
}

.main-header h1 {
    margin: 0;
    font-size: 1.45rem;
    font-weight: 800;
}

.main-header p {
    margin: 5px 0 0 0;
    opacity: 0.92;
    font-size: 0.88rem;
}

/* ── Status bar ─────────────────────────────────────────────────────────── */
.status-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    flex-wrap: wrap;
}

.status-card {
    flex: 1;
    min-width: 160px;
    background: var(--m-surface);
    border: 1px solid var(--m-border);
    border-radius: 16px;
    padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    display: flex;
    align-items: center;
    gap: 12px;
}

.status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
}

.status-dot.online   { background: #27AE60; box-shadow: 0 0 0 3px rgba(39,174,96,0.2); }
.status-dot.starting { background: #F39C12; box-shadow: 0 0 0 3px rgba(243,156,18,0.2); animation: pulse 1s infinite; }
.status-dot.error    { background: #E74C3C; box-shadow: 0 0 0 3px rgba(231,76,60,0.2); }
.status-dot.stopped  { background: #BDC3C7; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}

.status-label { font-size: 0.82rem; color: var(--m-muted); }
.status-name  { font-size: 0.96rem; font-weight: 700; color: var(--m-text); }
.status-pid   { font-size: 0.75rem; color: var(--m-muted); font-family: monospace; }

/* ── Service cards ──────────────────────────────────────────────────────── */
.service-card {
    background: var(--m-surface);
    border: 1px solid var(--m-border);
    border-radius: 18px;
    padding: 20px 22px;
    margin-bottom: 16px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}

.service-card h3 {
    margin: 0 0 4px 0;
    font-size: 1.05rem;
    color: var(--m-green-dark);
}

.service-card .meta {
    font-size: 0.80rem;
    color: var(--m-muted);
    margin-bottom: 14px;
}

/* ── Log viewer ─────────────────────────────────────────────────────────── */
.log-box {
    background: #1C2833;
    border-radius: 14px;
    padding: 14px 16px;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem;
    line-height: 1.55;
    color: #A9DFBF;
    max-height: 260px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
}

.log-box .log-error  { color: #F1948A; }
.log-box .log-warn   { color: #F9CA24; }
.log-box .log-info   { color: #A9DFBF; }
.log-box .log-system { color: #85C1E9; }

/* ── QR block ───────────────────────────────────────────────────────────── */
.qr-container {
    background: #FDFEFE;
    border: 2px dashed var(--m-green);
    border-radius: 18px;
    padding: 22px;
    text-align: center;
    margin-top: 12px;
}

.qr-container h4 {
    margin: 0 0 12px 0;
    color: var(--m-green-dark);
    font-size: 1rem;
}

.qr-container pre {
    display: inline-block;
    font-family: 'Courier New', monospace;
    font-size: 0.65rem;
    line-height: 1.1;
    text-align: left;
    background: white;
    padding: 12px;
    border-radius: 10px;
    border: 1px solid var(--m-border);
}

/* ── Conversation feed ──────────────────────────────────────────────────── */
.conv-feed {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-height: 620px;
    overflow-y: auto;
    padding-right: 4px;
}

.msg-bubble {
    border-radius: 16px;
    padding: 12px 16px;
    max-width: 88%;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.msg-user {
    background: #EAF4E0;
    border: 1px solid #C8E6B0;
    align-self: flex-start;
    border-bottom-left-radius: 4px;
}

.msg-agent {
    background: var(--m-surface);
    border: 1px solid var(--m-border);
    align-self: flex-end;
    border-bottom-right-radius: 4px;
}

.msg-meta {
    font-size: 0.72rem;
    color: var(--m-muted);
    margin-bottom: 4px;
}

.msg-content {
    font-size: 0.90rem;
    color: var(--m-text);
    line-height: 1.5;
}

.msg-badge {
    display: inline-block;
    font-size: 0.68rem;
    padding: 2px 8px;
    border-radius: 999px;
    margin-top: 6px;
    font-weight: 600;
}

.badge-rag      { background: #D5F5E3; color: #1E8449; }
.badge-struct   { background: #D6EAF8; color: #1A5276; }
.badge-memory   { background: #FEF9E7; color: #B7770D; }
.badge-human    { background: #FDEDEC; color: #C0392B; }
.badge-error    { background: #FDEDEC; color: #C0392B; }
.badge-agent    { background: #EEF4E6; color: #2f6f23; }

/* ── Session pill ───────────────────────────────────────────────────────── */
.session-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #EAF0FB;
    border: 1px solid #AED6F1;
    border-radius: 999px;
    padding: 4px 12px;
    font-size: 0.78rem;
    color: #1A5276;
    font-weight: 600;
    margin-bottom: 6px;
}

/* ── Buttons ────────────────────────────────────────────────────────────── */
.stButton > button {
    border-radius: 14px;
    border: 1px solid var(--m-border);
    background: var(--m-surface);
    color: var(--m-text);
    box-shadow: 0 2px 6px rgba(0,0,0,0.03);
}

.stButton > button:hover {
    border-color: var(--m-green);
    color: var(--m-green-dark);
    background: #fafdf6;
}

[data-testid="stTabs"] button {
    color: var(--m-muted);
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--m-orange);
    border-bottom-color: var(--m-orange);
}

.route-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #eef4e6;
    color: var(--m-green-dark);
    border: 1px solid #d4e2c7;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    margin-bottom: 8px;
}

.sidebar-section {
    background: rgba(255,255,255,0.75);
    border: 1px solid var(--m-border);
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 16px;
}

.sidebar-section h3 {
    margin: 0 0 12px 0;
    color: var(--m-green-dark);
    font-size: 1rem;
}
</style>"""

HEADER_HTML = """<div class="main-header">
<h1>🍃 Panel de Control — Asistente Virtual Manuelita S.A.</h1>
<p>Consola de operación · Cultivamos cosas buenas que generan progreso y bienestar · Desde 1864</p>
</div>"""

SIDEBAR_BRAND_HTML = """<div class="brand-strip">
<div class="brand-logo"></div>
<div>
  <div class="brand-name">Manuelita</div>
  <div style="color:#6c756d;font-size:.86rem;">Panel operativo</div>
</div>
</div>"""

EMPTY_STATE_HTML = """
<div style="padding: 1.5rem; color: #6a7469; text-align:center;">
    Sin conversaciones registradas aún.
</div>
"""


def status_bar_html(services: dict) -> str:
    """Genera la barra de estado superior con las tarjetas de cada servicio."""
    cards = []
    for key, info in services.items():
        st    = info["status"]
        label = {"online": "En línea", "starting": "Iniciando...",
                 "error": "Error", "stopped": "Detenido"}.get(st, st)
        pid_txt = f"PID {info['pid']}" if info.get("pid") else ""
        port_txt = f":{info['port']}"
        cards.append(f"""
        <div class="status-card">
            <div class="status-dot {st}"></div>
            <div>
                <div class="status-name">{info['label']}</div>
                <div class="status-label">{label} {port_txt}</div>
                <div class="status-pid">{pid_txt}</div>
            </div>
        </div>""")

    wa_dot   = "online" if services.get("bridge", {}).get("wa_connected") else "stopped"
    wa_label = "WhatsApp conectado" if wa_dot == "online" else "WhatsApp desconectado"
    cards.append(f"""
    <div class="status-card">
        <div class="status-dot {wa_dot}"></div>
        <div>
            <div class="status-name">WhatsApp</div>
            <div class="status-label">{wa_label}</div>
        </div>
    </div>""")

    return f'<div class="status-bar">{"".join(cards)}</div>'


def msg_bubble_html(msg: dict) -> str:
    """Genera el HTML de una burbuja de conversación."""
    role    = msg.get("role", "user")
    content = msg.get("content", "").replace("<", "&lt;").replace(">", "&gt;")
    numero  = msg.get("metadata", {}).get("session_id", "—")
    ts      = msg.get("created_at", "")[:16].replace("T", " ")
    route   = msg.get("route_used") or ""
    model   = msg.get("model_used") or ""
    tool    = msg.get("tool_used") or ""

    badge_map = {
        "RAG":            "badge-rag",
        "Dato estructurado": "badge-struct",
        "Memoria":        "badge-memory",
        "Control humano": "badge-human",
        "error":          "badge-error",
    }
    badge_cls = badge_map.get(route, "badge-agent")

    if role == "user":
        return f"""
        <div class="msg-bubble msg-user">
            <div class="msg-meta">📱 {numero} · {ts}</div>
            <div class="msg-content">{content}</div>
        </div>"""
    else:
        badge_html = f'<span class="msg-badge {badge_cls}">{route}</span>' if route else ""
        meta2 = f"{model} · {tool}" if model else ""
        return f"""
        <div class="msg-bubble msg-agent">
            <div class="msg-meta">🤖 Manuel · {ts}</div>
            <div class="msg-content">{content}</div>
            {badge_html}
            <div class="msg-meta" style="margin-top:4px">{meta2}</div>
        </div>"""


def log_lines_html(lines: list) -> str:
    """Formatea líneas de log con coloración por nivel."""
    html_lines = []
    for line in lines[-80:]:
        lo = line.lower()
        if any(w in lo for w in ("error", "exception", "traceback", "failed", "critical")):
            cls = "log-error"
        elif any(w in lo for w in ("warn", "warning")):
            cls = "log-warn"
        elif any(w in lo for w in ("info", "uvicorn", "started", "running", "connected")):
            cls = "log-info"
        else:
            cls = "log-system"
        escaped = line.replace("<", "&lt;").replace(">", "&gt;")
        html_lines.append(f'<span class="{cls}">{escaped}</span>')
    return '<div class="log-box">' + "<br>".join(html_lines) + "</div>"
