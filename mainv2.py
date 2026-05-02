import streamlit as st
import ollama
from pathlib import Path

st.set_page_config(page_title="Chat con Ollama", layout="centered")
st.title("🤖 Chat con Ollama")

# --- Cargar archivos Markdown de la carpeta /context ---
def load_context(folder: str = "context") -> str:
    context_path = Path(folder)
    if not context_path.exists():
        return ""

    texts = []
    for file in sorted(context_path.glob("*.md")):
        content = file.read_text(encoding="utf-8")
        texts.append(f"--- Archivo: {file.name} ---\n{content}")

    return "\n\n".join(texts)

context_text = load_context()

# --- Obtener modelos disponibles ---
@st.cache_data
def get_models():
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

models = get_models()

if not models:
    st.warning("Asegúrate de que Ollama esté corriendo. Ejecuta `ollama serve` en una terminal.")
    st.stop()

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Configuración")
    selected_model = st.selectbox("Modelo", models)

    st.divider()

    # Mostrar archivos cargados
    st.subheader("📄 Contexto cargado")
    context_path = Path("context")
    if context_path.exists():
        files = list(context_path.glob("*.md"))
        if files:
            for f in files:
                st.markdown(f"✅ `{f.name}`")
        else:
            st.warning("No hay archivos .md en /context")
    else:
        st.warning("La carpeta /context no existe")

    st.divider()

    if st.button("🗑️ Limpiar chat"):
        st.session_state.messages = []
        st.rerun()

# --- Historial de mensajes ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Input del usuario ---
if prompt := st.chat_input("Escribe tu pregunta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):

            messages_to_send = []

            if context_text:
                messages_to_send.append({
                    "role": "system",
                    "content": (
                        "Eres un asistente útil. Usa el siguiente contexto como base "
                        "para responder las preguntas del usuario. Si la respuesta no "
                        "está en el contexto, responde con tu conocimiento general.\n\n"
                        f"CONTEXTO:\n{context_text}"
                    )
                })

            messages_to_send += st.session_state.messages

            response = ollama.chat(
                model=selected_model,
                messages=messages_to_send
            )
            answer = response.message.content
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})