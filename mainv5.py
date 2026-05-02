import json
import base64
import streamlit as st
import ollama
from pathlib import Path

st.set_page_config(
    page_title="Asistente Virtual — Manuelita S.A.",
    page_icon="🌿",
    layout="centered",
)


# ============================================================
# ESTILOS CORPORATIVOS MANUELITA
# Paleta: Verde oscuro #2D6A27 | Amarillo #D4A017 | Gris #3A3A3A
# Para cambiar colores edita las variables CSS al inicio del bloque
# ============================================================
st.markdown("""
<style>
  /* --- VARIABLES DE COLOR CORPORATIVO --- */
  :root {
    --verde-oscuro:  #2D6A27;
    --verde-medio:   #4A8C3F;
    --verde-claro:   #6AAB5E;
    --amarillo:      #D4A017;
    --gris-oscuro:   #3A3A3A;
    --gris-medio:    #5A5A5A;
    --blanco:        #FFFFFF;
    --fondo-app:     #F4F7F2;
  }

  /* --- FONDO GENERAL --- */
  .stApp {
    background-color: var(--fondo-app);
    background-image:
      radial-gradient(circle at 10% 20%, rgba(45,106,39,0.07) 0%, transparent 50%),
      radial-gradient(circle at 90% 80%, rgba(212,160,23,0.06) 0%, transparent 50%);
  }

  /* --- HEADER / TÍTULO PRINCIPAL --- */
  .main-header {
    background: linear-gradient(135deg, var(--verde-oscuro) 0%, var(--verde-medio) 100%);
    border-radius: 12px;
    padding: 18px 24px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: 0 4px 16px rgba(45,106,39,0.25);
  }
  .main-header h1 {
    color: var(--blanco) !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    padding: 0 !important;
    letter-spacing: 0.3px;
  }
  .main-header .tagline {
    color: rgba(255,255,255,0.80);
    font-size: 0.82rem;
    margin-top: 2px;
  }
  .logo-circle {
    background: var(--amarillo);
    border-radius: 50%;
    width: 46px;
    height: 46px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    flex-shrink: 0;
  }

  /* --- OCULTAR TÍTULO NATIVO DE STREAMLIT --- */
  h1[data-testid="stHeading"] { display: none !important; }
  /* Ocultar decoración naranja por defecto */
  header[data-testid="stHeader"] { background: transparent !important; }

  /* --- SIDEBAR --- */
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--verde-oscuro) 0%, #1e4a1a 100%) !important;
  }
  section[data-testid="stSidebar"] * {
    color: var(--blanco) !important;
  }
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] .stExpander summary p {
    color: rgba(255,255,255,0.90) !important;
  }
  /* Selectbox en sidebar */
  section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: 8px !important;
    color: var(--blanco) !important;
  }
  /* Expanders en sidebar */
  section[data-testid="stSidebar"] .stExpander {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
    margin-bottom: 6px !important;
  }
  /* Botones de preguntas en sidebar */
  section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.10) !important;
    border: 1px solid rgba(255,255,255,0.20) !important;
    color: var(--blanco) !important;
    border-radius: 6px !important;
    font-size: 0.78rem !important;
    text-align: left !important;
    padding: 6px 10px !important;
    transition: background 0.2s ease !important;
  }
  section[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--amarillo) !important;
    color: var(--gris-oscuro) !important;
    border-color: var(--amarillo) !important;
  }
  /* Botón limpiar chat */
  section[data-testid="stSidebar"] .stButton:last-of-type > button {
    background: rgba(212,160,23,0.25) !important;
    border: 1px solid var(--amarillo) !important;
    color: var(--amarillo) !important;
  }
  section[data-testid="stSidebar"] .stButton:last-of-type > button:hover {
    background: var(--amarillo) !important;
    color: var(--gris-oscuro) !important;
  }
  /* Divider sidebar */
  section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.20) !important;
  }

  /* --- ÁREA DE CHAT --- */
  .stChatMessage {
    border-radius: 10px !important;
    margin-bottom: 6px !important;
  }
  /* Mensaje usuario */
  .stChatMessage[data-testid="stChatMessageUser"] {
    background: rgba(45,106,39,0.08) !important;
    border-left: 3px solid var(--verde-oscuro) !important;
  }
  /* Mensaje asistente */
  .stChatMessage[data-testid="stChatMessageAssistant"] {
    background: rgba(255,255,255,0.85) !important;
    border-left: 3px solid var(--amarillo) !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06) !important;
  }

  /* --- INPUT DE CHAT --- */
  .stChatInput > div {
    border: 2px solid var(--verde-oscuro) !important;
    border-radius: 10px !important;
    background: var(--blanco) !important;
    box-shadow: 0 2px 8px rgba(45,106,39,0.12) !important;
  }
  .stChatInput > div:focus-within {
    border-color: var(--amarillo) !important;
    box-shadow: 0 2px 12px rgba(212,160,23,0.20) !important;
  }

  /* --- EXPANDER DE PREGUNTAS (OPCIÓN B) --- */
  .stExpander {
    border: 1px solid rgba(45,106,39,0.25) !important;
    border-radius: 10px !important;
    background: var(--blanco) !important;
    margin-bottom: 12px !important;
  }
  .stExpander summary {
    color: var(--verde-oscuro) !important;
    font-weight: 600 !important;
  }
  /* Botones de preguntas en expander principal */
  .stExpander .stButton > button {
    background: rgba(45,106,39,0.06) !important;
    border: 1px solid rgba(45,106,39,0.20) !important;
    color: var(--verde-oscuro) !important;
    border-radius: 6px !important;
    font-size: 0.80rem !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
  }
  .stExpander .stButton > button:hover {
    background: var(--verde-oscuro) !important;
    color: var(--blanco) !important;
  }

  /* --- BADGE DE ARCHIVOS CARGADOS --- */
  .context-badge {
    display: inline-block;
    background: rgba(45,106,39,0.15);
    border: 1px solid rgba(45,106,39,0.30);
    color: var(--verde-oscuro);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.75rem;
    margin: 2px 0;
  }

  /* --- SPINNER --- */
  .stSpinner > div { border-top-color: var(--verde-oscuro) !important; }

  /* --- FOOTER BRANDING --- */
  .brand-footer {
    text-align: center;
    padding: 10px 0 4px 0;
    color: var(--gris-medio);
    font-size: 0.72rem;
    border-top: 1px solid rgba(45,106,39,0.15);
    margin-top: 16px;
  }
  .brand-footer span { color: var(--verde-oscuro); font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER PERSONALIZADO
# ============================================================
st.markdown("""
<div class="main-header">
  <div class="logo-circle">🌿</div>
  <div>
    <h1>Asistente Virtual — Manuelita S.A.</h1>
    <div class="tagline">Cultivamos cosas buenas que generan progreso y bienestar · Desde 1864</div>
  </div>
</div>
""", unsafe_allow_html=True)


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
# print (context_text)

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
    st.warning("⚠️ Asegúrate de que Ollama esté corriendo. Ejecuta `ollama serve` en una terminal.")
    st.stop()


# ============================================================
# ESTADO DE SESIÓN
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""

if "input_key" not in st.session_state:
    st.session_state.input_key = 0


# ============================================================
# FUNCIÓN PARA PROCESAR UN PROMPT
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
                        "No respondas con base en tu conocimiento, solo responde del contexto proporcionado. "
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
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    selected_model = st.selectbox("Modelo Ollama", models, key="current_model")

    st.divider()

    # Archivos de contexto
    st.markdown("### 📄 Base de conocimiento")
    context_path = Path("context")
    if context_path.exists():
        files = list(context_path.glob("*.md"))
        if files:
            for f in files:
                st.markdown(f'<span class="context-badge">✅ {f.name}</span>', unsafe_allow_html=True)
        else:
            st.warning("No hay archivos .md en /context")
    else:
        st.warning("La carpeta /context no existe")

    st.divider()

    # ----------------------------------------------------------
    # OPCIÓN A: Preguntas en el SIDEBAR
    # Para desactivar: comenta desde "# >>> OPCIÓN A START"
    #                  hasta          "# >>> OPCIÓN A END"
    # ----------------------------------------------------------
    # >>> OPCIÓN A START
    if questions:
        st.markdown("### 💬 Preguntas sugeridas")
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
                        st.session_state.input_key += 1
                        st.rerun()
    # >>> OPCIÓN A END

    st.divider()

    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.session_state.selected_question = ""
        st.session_state.input_key += 1
        st.rerun()

    # Branding sidebar
    st.markdown("""
    <div style="margin-top:20px; text-align:center; opacity:0.6; font-size:0.72rem; color:white;">
      🌿 Manuelita S.A. · 1864 - 2025<br>
      <em>Valle del Cauca, Colombia</em>
    </div>
    """, unsafe_allow_html=True)


# # ============================================================
# # OPCIÓN B: Expander de preguntas sobre el chat
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
if not st.session_state.messages:
    st.markdown("""
    <div style="
      text-align:center;
      padding: 32px 20px;
      color: #5A5A5A;
      background: rgba(255,255,255,0.6);
      border-radius: 12px;
      border: 1px dashed rgba(45,106,39,0.25);
      margin: 10px 0 20px 0;
    ">
      <div style="font-size:2rem; margin-bottom:8px;">🌾</div>
      <div style="font-weight:600; color:#2D6A27; font-size:1rem;">¿En qué puedo ayudarte?</div>
      <div style="font-size:0.83rem; margin-top:4px;">
        Selecciona una pregunta sugerida o escribe directamente tu consulta.
      </div>
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ============================================================
# PROCESAR PREGUNTA SELECCIONADA POR BOTÓN
# ============================================================
if st.session_state.selected_question:
    pending = st.session_state.selected_question
    st.session_state.selected_question = ""
    process_prompt(pending)


# ============================================================
# INPUT MANUAL DEL USUARIO
# ============================================================
if prompt := st.chat_input(
    placeholder="Escribe tu pregunta sobre Manuelita S.A. ...",
    key=f"chat_input_{st.session_state.input_key}",
):
    process_prompt(prompt)


# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="brand-footer">
  <span>Manuelita S.A.</span> · Asistente Virtual
</div>
""", unsafe_allow_html=True)