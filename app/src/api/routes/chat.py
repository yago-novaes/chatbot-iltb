import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.src.config import settings
from app.src.llm.client import generate
from app.src.rag.ingestion.indexer import collection_exists
from app.src.rag.retriever import build_context, retrieve

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=5)
    top_k: int = Field(default=4, ge=1, le=10)
    session_id: str = "default"  # usado na Fase 2 para histórico


class SourceChunk(BaseModel):
    source: str
    score: float
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    llm_provider: str
    llm_model: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    ready = await asyncio.to_thread(collection_exists)
    if not ready:
        raise HTTPException(
            status_code=409,
            detail="Base de conhecimento não indexada. Execute POST /ingest primeiro.",
        )

    chunks = await asyncio.to_thread(retrieve, request.question, request.top_k)
    if not chunks:
        raise HTTPException(status_code=404, detail="Nenhum trecho relevante encontrado.")

    context = build_context(chunks)
    answer = await generate(context=context, question=request.question)

    return ChatResponse(
        answer=answer,
        sources=[
            SourceChunk(
                source=c.source,
                score=c.score,
                excerpt=c.text[:300] + ("..." if len(c.text) > 300 else ""),
            )
            for c in chunks
        ],
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
    )
