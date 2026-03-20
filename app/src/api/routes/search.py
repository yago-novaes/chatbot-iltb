"""
POST /search — busca trechos relevantes sem gerar resposta.
Útil para debug do pipeline RAG (ver scores, verificar chunking).
"""
import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.src.rag.ingestion.indexer import collection_exists
from app.src.rag.retriever import retrieve

router = APIRouter(tags=["debug"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_k: int = Field(default=4, ge=1, le=10)


@router.post("/search")
async def search(request: SearchRequest):
    ready = await asyncio.to_thread(collection_exists)
    if not ready:
        raise HTTPException(
            status_code=409,
            detail="Base de conhecimento não indexada. Execute POST /ingest primeiro.",
        )
    chunks = await asyncio.to_thread(retrieve, request.query, request.top_k)
    return {
        "query": request.query,
        "results": [{"source": c.source, "score": c.score, "text": c.text} for c in chunks],
    }
