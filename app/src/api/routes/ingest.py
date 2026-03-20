import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.src.rag.ingestion.indexer import ingest_documents

router = APIRouter(tags=["ingest"])


class IngestResponse(BaseModel):
    status: str
    chunks_indexed: int
    message: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest():
    """Indexa (ou re-indexa) todos os documentos da pasta docs/protocolos/."""
    try:
        total = await asyncio.to_thread(ingest_documents)
        return IngestResponse(
            status="success",
            chunks_indexed=total,
            message=f"{total} chunks indexados com sucesso.",
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
