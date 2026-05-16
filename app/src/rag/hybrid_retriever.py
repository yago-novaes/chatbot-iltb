"""
Retriever híbrido: combina busca densa (ChromaDB / BGE-M3) com BM25 (rank_bm25)
via Reciprocal Rank Fusion (RRF).

Implementa a recomendação TF2 da Seção 2.33 do diário (busca híbrida BM25+denso)
para atacar o gap residual de Faithfulness via melhor recall em termos clínicos
exatos (siglas, dosagens, nomes de fármacos).

Referências bibliográficas (já citadas em main.tex):
  - Cormack et al. 2009 — RRF formula
  - Formal et al. 2021 — SPLADE / sparse retrieval
  - Wang et al. 2024 (best practices RAG, EMNLP) — ganhos típicos de hybrid
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import List

import chromadb
from rank_bm25 import BM25Okapi

from app.src.config import settings
from app.src.rag.embeddings import embedding_fn
from app.src.rag.ingestion.indexer import _get_client
from app.src.rag.retriever import RetrievedChunk


# ─── BM25 index (sidecar, construído lazy a partir da collection ChromaDB) ───

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Tokenização simples para PT clínico — case-fold + palavras alfanuméricas."""
    return _TOKEN_RE.findall(text.casefold())


@dataclass
class _BM25Index:
    bm25: BM25Okapi
    ids: list[str]
    documents: list[str]
    metadatas: list[dict]


_bm25_cache: _BM25Index | None = None
_bm25_lock = threading.Lock()


def _load_collection_docs() -> tuple[list[str], list[str], list[dict]]:
    """Lê todos os chunks da collection ChromaDB ativa."""
    collection = _get_client().get_collection(
        settings.chroma_collection, embedding_function=embedding_fn
    )
    raw = collection.get(include=["documents", "metadatas"])
    return raw["ids"], raw["documents"], raw["metadatas"]


def _get_bm25() -> _BM25Index:
    """Carrega (e cacheia) o índice BM25 a partir da collection ChromaDB ativa."""
    global _bm25_cache
    if _bm25_cache is not None:
        return _bm25_cache
    with _bm25_lock:
        if _bm25_cache is not None:
            return _bm25_cache
        ids, docs, metas = _load_collection_docs()
        tokenized = [_tokenize(d) for d in docs]
        _bm25_cache = _BM25Index(
            bm25=BM25Okapi(tokenized),
            ids=ids,
            documents=docs,
            metadatas=metas,
        )
    return _bm25_cache


# ─── Dense + BM25 → RRF ────────────────────────────────────────────────────

def _dense_ranking(query: str, k: int) -> list[tuple[str, str, dict, float]]:
    """Retorna (id, doc, meta, cosine_similarity) ordenado por similaridade desc."""
    collection = _get_client().get_collection(
        settings.chroma_collection, embedding_function=embedding_fn
    )
    res = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    return [
        (id_, doc, meta, round(1 - dist, 4))
        for id_, doc, meta, dist in zip(
            res["ids"][0],
            res["documents"][0],
            res["metadatas"][0],
            res["distances"][0],
        )
    ]


def _bm25_ranking(query: str, k: int) -> list[tuple[str, str, dict, float]]:
    """Retorna (id, doc, meta, bm25_score) ordenado por score desc."""
    idx = _get_bm25()
    tokens = _tokenize(query)
    scores = idx.bm25.get_scores(tokens)
    top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return [(idx.ids[i], idx.documents[i], idx.metadatas[i], float(scores[i])) for i in top]


def _rrf(rankings: list[list[tuple[str, str, dict, float]]], k_const: int) -> dict[str, dict]:
    """
    Reciprocal Rank Fusion (Cormack et al. 2009).
    score(d) = Σ 1 / (k_const + rank(d, ranker_i))
    Retorna {id: {doc, meta, rrf_score, ranks_per_ranker}}.
    """
    fused: dict[str, dict] = {}
    for ranker_idx, ranking in enumerate(rankings):
        for rank_pos, (id_, doc, meta, _) in enumerate(ranking, start=1):
            entry = fused.setdefault(
                id_,
                {"doc": doc, "meta": meta, "rrf_score": 0.0, "ranks": {}},
            )
            entry["rrf_score"] += 1.0 / (k_const + rank_pos)
            entry["ranks"][ranker_idx] = rank_pos
    return fused


def retrieve_hybrid(query: str, top_k: int | None = None) -> List[RetrievedChunk]:
    """
    Busca híbrida densa + BM25 com fusão RRF.
    Retorna até top_k chunks (default settings.retriever_top_k), com score = RRF score.

    Diferenças vs retrieve() denso:
      - Busca em paralelo os top fetch_k candidatos em cada ranker
      - Funde por RRF; ordena pela soma reciprocal
      - Score retornado é o RRF, não cosine — não filtra por retriever_score_threshold
        (a comparação semântica do threshold não se aplica à escala RRF)
    """
    k = top_k or settings.retriever_top_k
    fetch_k = settings.retriever_fetch_k
    k_const = settings.retriever_rrf_k

    dense = _dense_ranking(query, fetch_k)
    sparse = _bm25_ranking(query, fetch_k)
    fused = _rrf([dense, sparse], k_const=k_const)

    ranked = sorted(fused.items(), key=lambda kv: kv[1]["rrf_score"], reverse=True)[:k]
    return [
        RetrievedChunk(
            text=entry["doc"],
            source=entry["meta"].get("source", "desconhecido"),
            score=round(entry["rrf_score"], 6),
        )
        for _, entry in ranked
    ]
