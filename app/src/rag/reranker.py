"""
Reranker cross-encoder (TF1) — etapa pós-retrieval que reordena os candidatos
do retriever (denso ou híbrido) usando um modelo cross-encoder multilíngue.

Modelo padrão: Alibaba-NLP/gte-multilingual-reranker-base (Zhang et al. 2024,
EMNLP-Industry). Cross-encoders processam (query, chunk) conjuntamente e
capturam relevância fine-grained que bi-encoders dense não capturam.

Referência (já citada em main.tex):
  - zhang2024mgte — modelo cross-encoder multilíngue
  - wang2024bestpractices — empiricamente +5-10pp Faithfulness sobre retrieval
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
    """Carrega (lazy + thread-safe) o cross-encoder mGTE."""
    global _reranker
    if _reranker is not None:
        return _reranker
    with _reranker_lock:
        if _reranker is not None:
            return _reranker
        # trust_remote_code=True é necessário pro mGTE; o modelo tem código
        # custom para tokenização e atenção (LongRoPE)
        _reranker = CrossEncoder(
            settings.reranker_model,
            trust_remote_code=True,
            max_length=512,
        )
    return _reranker


def rerank(query: str, candidates: List[RetrievedChunk], top_k: int) -> List[RetrievedChunk]:
    """
    Reordena candidates pelo score do cross-encoder e devolve os top_k.
    Score retornado em RetrievedChunk.score passa a ser o score do reranker.
    """
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
