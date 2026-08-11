"""
Etapa pós-retrieval: reordena os candidatos do retriever com um cross-encoder
multilíngue (Alibaba-NLP/gte-multilingual-reranker-base, Zhang et al. 2024).

O cross-encoder processa (query, chunk) junto, então enxerga relevância que o
bi-encoder denso perde ao comparar vetores independentes.
"""
from __future__ import annotations

import threading
from typing import List

from sentence_transformers import CrossEncoder

from app.src.config import settings
from app.src.rag.retriever import RetrievedChunk


_reranker: CrossEncoder | None = None
_reranker_lock = threading.Lock()


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is not None:
        return _reranker
    with _reranker_lock:
        if _reranker is not None:
            return _reranker
        # o mGTE traz tokenização e atenção custom (LongRoPE), daí o trust_remote_code
        _reranker = CrossEncoder(
            settings.reranker_model,
            trust_remote_code=True,
            max_length=512,
        )
    return _reranker


def rerank(query: str, candidates: List[RetrievedChunk], top_k: int) -> List[RetrievedChunk]:
    """Reordena candidates e devolve os top_k, com score do cross-encoder."""
    if not candidates:
        return candidates
    pairs = [(query, c.text) for c in candidates]
    scores = _get_reranker().predict(pairs, convert_to_numpy=True)
    ranked = sorted(
        zip(candidates, scores),
        key=lambda x: float(x[1]),
        reverse=True,
    )[:top_k]
    return [
        RetrievedChunk(text=c.text, source=c.source, score=round(float(s), 6))
        for c, s in ranked
    ]
