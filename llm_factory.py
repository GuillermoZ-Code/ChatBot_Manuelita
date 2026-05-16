"""Construcción de clientes LLM para proveedores soportados."""

from __future__ import annotations

from typing import Dict, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
import ollama

from env_utils import read_env
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
        provider = "google" if model_name.startswith("gemini") else "openai"
        catalog[label] = {"provider": provider, "model": model_name}

    for model_name in get_ollama_models():
        catalog[f"Ollama · {model_name}"] = {
            "provider": "ollama",
            "model": model_name,
        }
    return catalog


def build_llm(model_config: Dict[str, str], settings: Dict[str, float]):
    """Instancia un LLM de LangChain según el proveedor seleccionado."""
    provider = model_config["provider"]
    model_name = model_config["model"]

    if provider == "google":
        api_key = read_env("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Falta GEMINI_API_KEY en el archivo .env."
            )
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=settings["temperature"],
            top_p=settings["top_p"],
            max_output_tokens=settings["num_predict"],
        )

    if provider == "openai":
        api_key = read_env("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Falta OPENAI_API_KEY en el archivo .env.")
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=settings["temperature"],
            top_p=settings["top_p"],
            max_tokens=settings["num_predict"],
        )

    if provider == "ollama":
        return ChatOllama(
            model=model_name,
            temperature=settings["temperature"],
            top_p=settings["top_p"],
            num_predict=settings["num_predict"],
            repeat_penalty=settings["repeat_penalty"],
            num_ctx=settings["num_ctx"],
        )

    raise ValueError(f"Proveedor no soportado: {provider}")
