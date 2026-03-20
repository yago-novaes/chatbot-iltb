"""
Retrieval: busca os chunks mais relevantes para uma query no ChromaDB.
"""
from dataclasses import dataclass
from typing import List

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from src.config import settings
from src.rag.ingestion import COLLECTION_NAME, _get_client

_embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


def retrieve(query: str, top_k: int | None = None) -> List[RetrievedChunk]:
    """
    Busca os chunks mais relevantes para a query.
    Retorna lista ordenada por relevância (menor distância = mais relevante).
    """
    k = top_k or settings.top_k_results
    client = _get_client()
    collection = client.get_collection(COLLECTION_NAME, embedding_function=_embedding_fn)

    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            RetrievedChunk(
                text=doc,
                source=meta.get("source", "desconhecido"),
                score=round(1 - dist, 4),  # distância coseno → similaridade
            )
        )

    return chunks


def build_context(chunks: List[RetrievedChunk]) -> str:
    """Formata os chunks recuperados em bloco de contexto para o prompt."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[Trecho {i} — {chunk.source}]\n{chunk.text}")
    return "\n\n---\n\n".join(parts)
