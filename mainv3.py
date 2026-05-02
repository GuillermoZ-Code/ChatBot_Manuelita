import streamlit as st
from pathlib import Path
import ollama

# ============================================================
# CONFIGURACIÓN DE PROVEEDORES
# Para agregar Gemini, ChatGPT o Claude:
#   1. pip install litellm
#   2. Descomenta el proveedor deseado abajo
#   3. Agrega tu API key en st.secrets o variable de entorno
# ============================================================

# from litellm import completion as litellm_completion
# import os
# PROVIDERS = {
#     "Ollama (local)": {"type": "ollama"},
#     "GPT-4o": {"type": "litellm", "model": "gpt-4o", "key_env": "OPENAI_API_KEY"},
#     "Gemini Flash": {"type": "litellm", "model": "gemini/gemini-2.0-flash", "key_env": "GEMINI_API_KEY"},
#     "Claude Sonnet": {"type": "litellm", "model": "anthropic/claude-sonnet-4-5", "key_env": "ANTHROPIC_API_KEY"},
# }

# ============================================================
# CONFIG INICIAL
# ============================================================
st.set_page_config(page_title="Comparador de Modelos", layout="wide")
st.title("⚖️ Comparador de Modelos LLM")

# --- Contexto desde /context/*.md ---
def load_context(folder="context"):
    p = Path(folder)
    if not p.exists():
        return ""
    return "\n\n".join(
        f"--- {f.name} ---\n{f.read_text(encoding='utf-8')}"
        for f in sorted(p.glob("*.md"))
    )

# --- Modelos Ollama disponibles ---
@st.cache_data
def get_ollama_models():
    try:
        # Filtra modelos de embedding que no sirven para chat
        EXCLUIR = ("embed", "embedding", "minilm", "nomic")
        return [
            m.model for m in ollama.list().models
            if not any(x in m.model.lower() for x in EXCLUIR)
        ]
    except Exception as e:
        st.error(f"No se pudo conectar con Ollama: {e}")
        return []

# --- Llamada unificada al modelo ---
def chat_with_model(model: str, messages: list) -> str:
    # Aquí puedes extender con litellm para otros proveedores:
    # if model.startswith("gpt") or model.startswith("gemini") or model.startswith("claude"):
    #     resp = litellm_completion(model=model, messages=messages)
    #     return resp.choices[0].message.content
    return ollama.chat(model=model, messages=messages).message.content

context_text = load_context()
models = get_ollama_models()

if not models:
    st.warning("Asegúrate de que Ollama esté corriendo con `ollama serve`.")
    st.stop()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("⚙️ Configuración")

    model_a = st.selectbox("Modelo A", models, index=0, key="model_a")
    model_b = st.selectbox("Modelo B", models, index=min(1, len(models)-1), key="model_b")

    st.divider()

    # Contexto cargado
    st.subheader("📄 Contexto")
    files = list(Path("context").glob("*.md")) if Path("context").exists() else []
    if files:
        for f in files:
            st.markdown(f"✅ `{f.name}`")
    else:
        st.caption("Sin archivos en /context")

    st.divider()

    if st.button("🗑️ Limpiar chat"):
        st.session_state.messages = []
        st.rerun()

# ============================================================
# HISTORIAL
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# Encabezados de columnas
col_a, col_b = st.columns(2)
col_a.markdown(f"### 🅰️ `{model_a}`")
col_b.markdown(f"### 🅱️ `{model_b}`")
st.divider()

# Renderizar historial
for msg in st.session_state.messages:
    col_a, col_b = st.columns(2)
    if msg["role"] == "user":
        col_a.chat_message("user").markdown(msg["content"])
        col_b.chat_message("user").markdown(msg["content"])
    elif msg["role"] == "assistant_a":
        col_a.chat_message("assistant").markdown(msg["content"])
    elif msg["role"] == "assistant_b":
        col_b.chat_message("assistant").markdown(msg["content"])

# ============================================================
# INPUT Y RESPUESTAS
# ============================================================
if prompt := st.chat_input("Escribe tu pregunta para comparar..."):
    # Guardar pregunta del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Mostrar la pregunta en ambas columnas
    col_a, col_b = st.columns(2)
    col_a.chat_message("user").markdown(prompt)
    col_b.chat_message("user").markdown(prompt)

    # Construir historial limpio para enviar (solo user/assistant sin sufijos)
    def build_history(side: str) -> list:
        history = []
        if context_text:
            history.append({
                "role": "system",
                "content": f"Eres un asistente útil. Usa este contexto si es relevante:\n\nCONTEXTO:\n{context_text}"
            })
        for m in st.session_state.messages:
            if m["role"] == "user":
                history.append({"role": "user", "content": m["content"]})
            elif m["role"] == f"assistant_{side}":
                history.append({"role": "assistant", "content": m["content"]})
        return history

    # Respuesta Modelo A
    with col_a:
        with st.chat_message("assistant"):
            with st.spinner(f"Pensando ({model_a})..."):
                answer_a = chat_with_model(model_a, build_history("a"))
                st.markdown(answer_a)

    # Respuesta Modelo B
    with col_b:
        with st.chat_message("assistant"):
            with st.spinner(f"Pensando ({model_b})..."):
                answer_b = chat_with_model(model_b, build_history("b"))
                st.markdown(answer_b)

    # Guardar respuestas
    st.session_state.messages.append({"role": "assistant_a", "content": answer_a})
    st.session_state.messages.append({"role": "assistant_b", "content": answer_b})