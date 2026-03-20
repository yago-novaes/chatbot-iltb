"""
Retriever vetorial — busca chunks relevantes no ChromaDB por similaridade coseno.
Fase 3: evoluir para busca híbrida (Qdrant + RRF).
"""
from dataclasses import dataclass
from typing import List

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.src.config import settings
from app.src.rag.ingestion.indexer import _get_client

_embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name=settings.embedding_model
)


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


def retrieve(query: str, top_k: int | None = None) -> List[RetrievedChunk]:
    k = top_k or settings.retriever_top_k
    collection = _get_client().get_collection(
        settings.chroma_collection, embedding_function=_embedding_fn
    )
    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    return [
        RetrievedChunk(
            text=doc,
            source=meta.get("source", "desconhecido"),
            score=round(1 - dist, 4),  # distância coseno → similaridade
        )
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


def build_context(chunks: List[RetrievedChunk]) -> str:
    """Formata chunks como bloco de contexto para o prompt."""
    return "\n\n---\n\n".join(
        f"[Trecho {i} — {c.source}]\n{c.text}"
        for i, c in enumerate(chunks, 1)
    )
