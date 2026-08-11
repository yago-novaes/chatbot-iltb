"""
Fachada de busca. Despacha entre densa (ChromaDB) e híbrida (denso + BM25 com
RRF, ver hybrid_retriever.py) conforme settings.retriever_mode.

retrieve() é a interface usada por eval/run_ragas.py e pela API.
"""
from dataclasses import dataclass
from typing import List

from app.src.config import settings
from app.src.rag.embeddings import embedding_fn
from app.src.rag.ingestion.indexer import _get_client


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


def _retrieve_dense(query: str, k: int) -> List[RetrievedChunk]:
    collection = _get_client().get_collection(
        settings.chroma_collection, embedding_function=embedding_fn
    )
    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    chunks = [
        RetrievedChunk(
            text=doc,
            source=meta.get("source", "desconhecido"),
            score=round(1 - dist, 4),  # distância coseno para similaridade
        )
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]
    return [c for c in chunks if c.score >= settings.retriever_score_threshold]


def retrieve(query: str, top_k: int | None = None) -> List[RetrievedChunk]:
    k = top_k or settings.retriever_top_k
    mode = settings.retriever_mode

    if mode == "hybrid_rerank":
        from app.src.rag.hybrid_retriever import retrieve_hybrid
        from app.src.rag.reranker import rerank
        candidates = retrieve_hybrid(query, top_k=settings.reranker_fetch_k)
        return rerank(query, candidates, top_k=k)

    if mode == "hybrid":
        from app.src.rag.hybrid_retriever import retrieve_hybrid
        return retrieve_hybrid(query, top_k=k)

    return _retrieve_dense(query, k)


def build_context(chunks: List[RetrievedChunk]) -> str:
    """Formata chunks como bloco de contexto para o prompt."""
    return "\n\n---\n\n".join(
        f"[Trecho {i} — {c.source}]\n{c.text}"
        for i, c in enumerate(chunks, 1)
    )
