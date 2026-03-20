from fastapi import APIRouter

from app.src.config import settings
from app.src.rag.ingestion.indexer import collection_exists

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {
        "status": "ok",
        "version": settings.api_version,
        "collection_ready": collection_exists(),
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
    }
