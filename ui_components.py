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
    padding: 24px 28px;
    box-shadow: 0 14px 32px rgba(47,111,35,0.18);
    margin-bottom: 20px;
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
    font-size: 1.65rem;
    font-weight: 800;
}

.main-header p {
    margin: 7px 0 0 0;
    opacity: 0.96;
    font-size: 0.98rem;
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

[data-testid="stChatInput"] {
    border-top: 1px solid var(--m-border);
}

[data-testid="stChatInput"] textarea {
    background: white;
    border-radius: 14px;
}

[data-testid="stTabs"] button {
    color: var(--m-muted);
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--m-orange);
    border-bottom-color: var(--m-orange);
}

.stChatMessage {
    background: rgba(255,255,255,0.72);
    border: 1px solid rgba(216,223,209,0.9);
    border-radius: 18px;
    padding: 8px 2px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
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

HEADER_HTML = r"""<div class="main-header">
<h1>🍃 Asistente Virtual — Manuelita S.A.</h1>
<p>Cultivamos cosas buenas que generan progreso y bienestar · Desde 1864</p>
</div>"""

SIDEBAR_BRAND_HTML = r"""<div class="brand-strip">
<div class="brand-logo"></div>
<div>
  <div class="brand-name">Manuelita</div>
  <div style="color:#6c756d;font-size:.86rem;">Asistente corporativo</div>
</div>
</div>"""

EMPTY_STATE_HTML = """
<div style="padding: 1.5rem; color: #6a7469;">
    Escribe una pregunta sobre Manuelita S.A. para empezar.
</div>
"""