import streamlit as st
import ollama

st.set_page_config(page_title="Chat con Ollama", layout="centered")
st.title("🤖 Chat con Ollama")

# --- Obtener modelos disponibles ---
@st.cache_data
def get_models():
    try:
        models = ollama.list()
        return [m.model for m in models.models]
    except Exception as e:
        st.error(f"No se pudo conectar con Ollama: {e}")
        return []

models = get_models()

if not models:
    st.warning("Asegúrate de que Ollama esté corriendo. Ejecuta `ollama serve` en una terminal.")
    st.stop()

# --- Sidebar: selección de modelo ---
with st.sidebar:
    st.header("⚙️ Configuración")
    selected_model = st.selectbox("Modelo", models)
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
            response = ollama.chat(
                model=selected_model,
                messages=st.session_state.messages
            )
            answer = response.message.content
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})