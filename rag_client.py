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
    """Construye y cachea el modelo de embeddings usado por Chroma."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    """Carga y cachea el vector store persistido de Chroma."""
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


def query_rag_documents(question: str, k: int = 4):
    """Recupera documentos similares desde Chroma para una consulta."""
    return get_vectorstore().similarity_search(question, k=k)


def query_rag_context(question: str, k: int = 4) -> str:
    """Serializa el contexto recuperado para incluirlo en un prompt."""
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
