import asyncio

from fastapi import APIRouter

from app.src.config import settings
from app.src.rag.ingestion.indexer import collection_exists

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    ready = await asyncio.to_thread(collection_exists)
    return {
        "status": "ok",
        "version": settings.api_version,
        "collection_ready": ready,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
    }
