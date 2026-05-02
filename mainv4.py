import json
import streamlit as st
import ollama
from pathlib import Path

st.set_page_config(page_title="Chat Manuelita S.A.", layout="centered")
st.title("🤖 Asistente Virtual — Manuelita S.A.")


# ============================================================
# CARGA DE CONTEXTO DESDE /context
# ============================================================
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


# ============================================================
# CARGA DE PREGUNTAS ESTÁNDAR DESDE questions.json
# ============================================================
def load_questions(filepath: str = "questions.json") -> list:
    path = Path(filepath)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("preguntas", [])


questions = load_questions()


# ============================================================
# OBTENER MODELOS DISPONIBLES EN OLLAMA
# ============================================================
@st.cache_data
def get_models():
    try:
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


# ============================================================
# ESTADO DE SESIÓN
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# Almacena la pregunta seleccionada desde los botones
if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""

# Contador para cambiar el key del chat_input y forzar re-render limpio
if "input_key" not in st.session_state:
    st.session_state.input_key = 0


# ============================================================
# FUNCIÓN PARA PROCESAR UN PROMPT (reutilizable)
# ============================================================
def process_prompt(prompt: str):
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
                        "Eres un asistente virtual oficial de Manuelita S.A. "
                        "Responde ÚNICAMENTE basándote en el contexto proporcionado a continuación. "
                        "Si la información solicitada no está en el contexto, responde exactamente: "
                        "'No tengo información suficiente en mi base de conocimiento para responder esa pregunta.' "
                        "No inventes datos, cifras, fechas ni nombres.\n\n"
                        f"CONTEXTO:\n{context_text}"
                    )
                })

            messages_to_send += st.session_state.messages

            response = ollama.chat(
                model=st.session_state.get("current_model", models[0]),
                messages=messages_to_send
            )
            answer = response.message.content
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})


# ============================================================
# SIDEBAR — Configuración + OPCIÓN A: Preguntas en sidebar
# ============================================================
with st.sidebar:
    st.header("⚙️ Configuración")
    selected_model = st.selectbox("Modelo", models, key="current_model")

    st.divider()

    # Archivos de contexto cargados
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

    # ----------------------------------------------------------
    # OPCIÓN A: Preguntas en el SIDEBAR (agrupadas por categoría)
    # Para desactivar: comenta desde "# >>> OPCIÓN A START"
    #                  hasta          "# >>> OPCIÓN A END"
    # ----------------------------------------------------------
    # >>> OPCIÓN A START
    if questions:
        st.subheader("💬 Preguntas sugeridas")
        categorias: dict = {}
        for q in questions:
            cat = q.get("categoria", "General")
            categorias.setdefault(cat, []).append(q["texto"])

        for cat, preguntas in categorias.items():
            with st.expander(cat, expanded=False):
                for pregunta in preguntas:
                    if st.button(
                        pregunta,
                        key=f"sidebar_{pregunta[:40]}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_question = pregunta
                        st.session_state.input_key += 1  # Fuerza re-render del chat_input
                        st.rerun()
    # >>> OPCIÓN A END

    st.divider()

    if st.button("🗑️ Limpiar chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.selected_question = ""
        st.session_state.input_key += 1
        st.rerun()


# # ============================================================
# # OPCIÓN B: Preguntas como EXPANDER sobre el área de chat
# # Para desactivar: comenta desde "# >>> OPCIÓN B START"
# #                  hasta          "# >>> OPCIÓN B END"
# # ============================================================
# # >>> OPCIÓN B START
# if questions:
#     with st.expander("💡 Selecciona una pregunta sugerida", expanded=False):
#         categorias_b: dict = {}
#         for q in questions:
#             cat = q.get("categoria", "General")
#             categorias_b.setdefault(cat, []).append(q["texto"])

#         for cat, preguntas in categorias_b.items():
#             st.markdown(f"**{cat}**")
#             for pregunta in preguntas:
#                 if st.button(
#                     pregunta,
#                     key=f"expander_{pregunta[:40]}",
#                     use_container_width=True,
#                 ):
#                     st.session_state.selected_question = pregunta
#                     st.session_state.input_key += 1
#                     st.rerun()
#             st.markdown("---")
# # >>> OPCIÓN B END


# ============================================================
# HISTORIAL DE MENSAJES
# ============================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ============================================================
# PROCESAR PREGUNTA SELECCIONADA POR BOTÓN
# Se ejecuta automáticamente cuando hay una pregunta pendiente
# en session_state (sin depender del parámetro value=)
# ============================================================
if st.session_state.selected_question:
    pending = st.session_state.selected_question
    st.session_state.selected_question = ""  # Limpiar ANTES de procesar
    process_prompt(pending)


# ============================================================
# INPUT MANUAL DEL USUARIO
# Key dinámica para evitar conflictos tras selección por botón
# ============================================================
if prompt := st.chat_input(
    placeholder="Escribe tu pregunta...",
    key=f"chat_input_{st.session_state.input_key}",
):
    process_prompt(prompt)