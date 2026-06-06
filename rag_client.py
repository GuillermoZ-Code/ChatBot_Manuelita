"""Cliente de acceso al sistema RAG persistido en Chroma."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from settings import CHROMA_DIR

EMBEDDING_MODEL = "intfloat/multilingual-e5-large"


@lru_cache(maxsize=1)
def build_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    db_path = Path(CHROMA_DIR)
    if not db_path.exists():
        raise FileNotFoundError(
            f"No se encontró la base vectorial en '{CHROMA_DIR}'. "
            "Primero ejecuta la ingesta para construir Chroma."
        )

    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=build_embeddings(),
    )


def _expand_query(question: str) -> List[str]:
    q = question.strip()
    lowered = q.lower()

    variants = [q]

    if "fundo" in lowered or "fundó" in lowered or "fundador" in lowered:
        variants.extend([
            "quien fundó manuelita",
            "fundador de manuelita",
            "historia de fundacion de manuelita",
            "origen de manuelita",
        ])

    if "historia" in lowered or "origen" in lowered:
        variants.extend([
            "historia de manuelita",
            "origen de manuelita",
            "trayectoria de manuelita",
        ])

    seen = []
    for item in variants:
        if item not in seen:
            seen.append(item)
    return seen


def query_rag_documents(question: str, k: int = 4):
    store = get_vectorstore()
    docs = []

    for variant in _expand_query(question):
        try:
            results = store.similarity_search(variant, k=k)
            docs.extend(results)
        except Exception:
            continue

    unique = []
    seen_keys = set()
    for doc in docs:
        key = (
            doc.metadata.get("source", ""),
            doc.metadata.get("titulo", ""),
            doc.page_content[:200],
        )
        if key not in seen_keys:
            seen_keys.add(key)
            unique.append(doc)

    return unique[:k]


def query_rag_context(question: str, k: int = 4) -> str:
    docs = query_rag_documents(question, k=k)
    if not docs:
        return "No se recuperó contexto relevante."

    blocks: List[str] = []
    for idx, doc in enumerate(docs, start=1):
        title = doc.metadata.get("titulo", "Sin título")
        source = doc.metadata.get("source", "Sin fuente")
        content = doc.page_content.strip()
        blocks.append(
            f"[Fragmento {idx}]\n"
            f"Título: {title}\n"
            f"Fuente: {source}\n"
            f"Contenido: {content}"
        )

    return "\n\n".join(blocks)