"""Construcción de clientes LLM para proveedores soportados."""

from __future__ import annotations

from typing import Any, Dict, List

import ollama
from langchain.chat_models import init_chat_model

from settings import FREE_API_MODELS


def get_ollama_models() -> List[str]:
    """Lista modelos de Ollama útiles para chat, excluyendo embeddings."""
    exclude_tokens = ("embed", "embedding", "minilm", "nomic")
    try:
        return [
            model.model
            for model in ollama.list().models
            if not any(token in model.model.lower() for token in exclude_tokens)
        ]
    except Exception:
        return []


def get_model_catalog() -> Dict[str, Dict[str, str]]:
    """Construye un catálogo de modelos y proveedores disponibles."""
    catalog: Dict[str, Dict[str, str]] = {}

    for label, model_name in FREE_API_MODELS.items():
        provider = "google_genai" if model_name.startswith("gemini") else "openai"
        catalog[label] = {"provider": provider, "model": model_name}

    for model_name in get_ollama_models():
        catalog[f"Ollama · {model_name}"] = {
            "provider": "ollama",
            "model": model_name,
        }

    return catalog


def build_llm(model_config: Dict[str, str], settings: Dict[str, Any]):
    """Instancia un LLM de LangChain según el proveedor seleccionado usando init_chat_model."""
    provider = model_config["provider"]
    model_name = model_config["model"]

    kwargs: Dict[str, Any] = {
        "temperature": settings["temperature"],
        "top_p": settings["top_p"],
    }

    if provider == "google_genai":
        kwargs["max_output_tokens"] = settings["num_predict"]
    elif provider == "openai":
        kwargs["max_tokens"] = settings["num_predict"]
    elif provider == "ollama":
        kwargs["num_predict"] = settings["num_predict"]
        kwargs["repeat_penalty"] = settings["repeat_penalty"]
        kwargs["num_ctx"] = settings["num_ctx"]

    return init_chat_model(
        model=model_name,
        model_provider=provider,
        **kwargs,
    )