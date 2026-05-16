"""Aplicación Streamlit del agente conversacional para Manuelita S.A."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from agent_service import AgentService
from chat_memory import ChatMemoryService
from db import (
    clear_all_data,
    delete_chat,
    initialize_database,
    list_chats,
    load_all_settings,
    rename_chat,
    save_setting,
)
from env_utils import load_environment
from langsmith_config import configure_langsmith
from llm_factory import get_model_catalog
from settings import APP_ICON, APP_LAYOUT, APP_TITLE, QUESTIONS_FILE
from ui_components import CUSTOM_CSS, EMPTY_STATE_HTML, HEADER_HTML

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout=APP_LAYOUT)


def load_questions() -> List[Dict[str, Any]]:
    """Carga las preguntas sugeridas desde el archivo JSON."""
    path = Path(QUESTIONS_FILE)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    return data.get("preguntas", [])


def initialize_state() -> None:
    """Inicializa el estado efímero de Streamlit para la sesión actual."""
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = ChatMemoryService.create_new_chat()
    if "rename_buffer" not in st.session_state:
        st.session_state.rename_buffer = ""
    if "selected_model_label" not in st.session_state:
        st.session_state.selected_model_label = None
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = ""


def render_chat_sidebar(chats: List[Dict[str, Any]]) -> None:
    """Renderiza el historial de conversaciones y acciones relacionadas."""
    with st.sidebar:
        st.markdown("### Conversaciones")
        if st.button("＋ Nuevo chat", use_container_width=True):
            st.session_state.current_chat_id = ChatMemoryService.create_new_chat()
            st.rerun()

        for chat in chats:
            col_open, col_delete = st.columns([5, 1])
            with col_open:
                if st.button(chat["title"], key=f"open_chat_{chat['id']}", use_container_width=True):
                    st.session_state.current_chat_id = chat["id"]
                    st.rerun()
            with col_delete:
                if st.button("🗑", key=f"delete_chat_{chat['id']}"):
                    delete_chat(chat["id"])
                    if st.session_state.current_chat_id == chat["id"]:
                        st.session_state.current_chat_id = ChatMemoryService.create_new_chat()
                    st.rerun()

        st.divider()
        st.markdown("### Gestión")
        st.session_state.rename_buffer = st.text_input(
            "Renombrar chat actual",
            value=st.session_state.rename_buffer,
            placeholder="Nuevo título",
        )
        if st.button("Guardar nuevo título", use_container_width=True):
            title = st.session_state.rename_buffer.strip()
            if title:
                rename_chat(st.session_state.current_chat_id, title)
                st.session_state.rename_buffer = title
                st.rerun()

        if st.button("Borrar todo y restablecer", use_container_width=True):
            clear_all_data()
            st.session_state.clear()
            st.rerun()


def render_chat_tab(agent: AgentService, model_catalog: Dict[str, Dict[str, str]]) -> None:
    """Renderiza la vista principal del chat conversacional."""
    memory_service = agent.memory_service
    messages = memory_service.get_messages()

    if not messages:
        st.markdown(EMPTY_STATE_HTML, unsafe_allow_html=True)

    for message in messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and message.get("route_used"):
                st.markdown(f'<span class="route-chip">{message["route_used"]}</span>', unsafe_allow_html=True)
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("model_used"):
                st.caption(f"Modelo: {message['model_used']} · Herramienta: {message.get('tool_used') or 'none'}")

    app_settings = load_all_settings()
    model_label = st.session_state.selected_model_label or app_settings["default_model"]
    if model_label not in model_catalog:
        model_label = next(iter(model_catalog.keys()))
    st.session_state.selected_model_label = model_label

    prompt = st.chat_input(
        placeholder="Escribe tu pregunta sobre Manuelita S.A.",
        max_chars=int(app_settings["question_char_limit"]),
    )
    if prompt:
        model_config = model_catalog[st.session_state.selected_model_label]
        memory_service.append_user_message(prompt, model_used=model_config["model"])
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Procesando consulta..."):
                result = agent.answer_question(prompt, model_config, app_settings)
                st.markdown(f'<span class="route-chip">{result["route"]}</span>', unsafe_allow_html=True)
                st.markdown(result["answer"])
                st.caption(f"Modelo: {model_config['model']} · Herramienta: {result['tool_used']}")
        memory_service.append_assistant_message(
            content=result["answer"],
            route_used=result["route"],
            model_used=model_config["model"],
            tool_used=result["tool_used"],
            metadata=result["metadata"],
        )
        st.rerun()


def render_settings_tab(model_catalog: Dict[str, Dict[str, str]]) -> None:
    """Renderiza la pestaña de configuración técnica de la aplicación."""
    settings = load_all_settings()
    available_models = list(model_catalog.keys())
    default_index = available_models.index(settings["default_model"]) if settings["default_model"] in available_models else 0

    st.markdown("### Configuración técnica")
    selected_model = st.selectbox("Modelo por defecto", available_models, index=default_index)
    temperature = st.slider("Temperatura", 0.0, 1.5, float(settings["temperature"]), 0.05)
    top_p = st.slider("Top-p", 0.1, 1.0, float(settings["top_p"]), 0.05)
    num_predict = st.slider("Máx. tokens de salida", 128, 4096, int(settings["num_predict"]), 64)
    rag_k = st.slider("Fragmentos RAG por consulta", 1, 8, int(settings["rag_k"]), 1)
    num_ctx = st.slider("Ventana de contexto", 1024, 32768, int(settings["num_ctx"]), 512)
    repeat_penalty = st.slider("Repeat penalty", 1.0, 2.0, float(settings["repeat_penalty"]), 0.05)
    question_char_limit = st.number_input(
        "Límite de caracteres por mensaje",
        min_value=50,
        max_value=10000,
        value=int(settings["question_char_limit"]),
        step=50,
    )
    system_prompt_extra = st.text_area(
        "Instrucciones adicionales del sistema",
        value=settings["system_prompt_extra"],
        height=160,
    )

    col_save, col_reset = st.columns(2)
    with col_save:
        if st.button("Guardar configuración", use_container_width=True):
            payload = {
                "default_model": selected_model,
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": num_predict,
                "rag_k": rag_k,
                "num_ctx": num_ctx,
                "repeat_penalty": repeat_penalty,
                "question_char_limit": question_char_limit,
                "system_prompt_extra": system_prompt_extra,
            }
            for key, value in payload.items():
                save_setting(key, value)
            st.session_state.selected_model_label = selected_model
            st.success("Configuración guardada correctamente.")
    with col_reset:
        if st.button("Restablecer valores", use_container_width=True):
            clear_all_data()
            initialize_database()
            st.session_state.clear()
            st.rerun()


def render_questions_sidebar(questions: List[Dict[str, Any]]) -> None:
    """Muestra preguntas sugeridas agrupadas por categoría."""
    with st.sidebar:
        st.divider()
        st.markdown("### Preguntas sugeridas")
        categories: Dict[str, List[str]] = {}
        for item in questions:
            category = item.get("categoria", "General")
            categories.setdefault(category, []).append(item["texto"])

        for category, question_list in categories.items():
            with st.expander(category, expanded=False):
                for idx, question in enumerate(question_list):
                    if st.button(question, key=f"question_{category}_{idx}", use_container_width=True):
                        st.session_state.pending_question = question
                        st.rerun()


def process_pending_question(agent: AgentService, model_catalog: Dict[str, Dict[str, str]]) -> None:
    """Procesa una pregunta sugerida seleccionada desde la barra lateral."""
    prompt = st.session_state.get("pending_question")
    if not prompt:
        return

    app_settings = load_all_settings()
    model_label = st.session_state.selected_model_label or app_settings["default_model"]
    if model_label not in model_catalog:
        model_label = next(iter(model_catalog.keys()))
    model_config = model_catalog[model_label]

    agent.memory_service.append_user_message(prompt, model_used=model_config["model"])
    result = agent.answer_question(prompt, model_config, app_settings)
    agent.memory_service.append_assistant_message(
        content=result["answer"],
        route_used=result["route"],
        model_used=model_config["model"],
        tool_used=result["tool_used"],
        metadata=result["metadata"],
    )
    st.session_state.pending_question = ""
    st.rerun()


def main() -> None:
    """Punto de entrada principal de la aplicación."""
    load_environment()
    configure_langsmith()
    initialize_database()
    initialize_state()

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(HEADER_HTML, unsafe_allow_html=True)

    model_catalog = get_model_catalog()
    if not model_catalog:
        st.error("No hay modelos disponibles. Verifica Ollama o la configuración API.")
        st.stop()

    questions = load_questions()
    chats = list_chats()
    render_chat_sidebar(chats)

    memory_service = ChatMemoryService(st.session_state.current_chat_id)
    agent = AgentService(memory_service)
    render_questions_sidebar(questions)
    process_pending_question(agent, model_catalog)

    chat_tab, settings_tab = st.tabs(["Chat", "Configuración"])
    with chat_tab:
        render_chat_tab(agent, model_catalog)
    with settings_tab:
        render_settings_tab(model_catalog)


if __name__ == "__main__":
    main()
