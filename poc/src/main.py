"""
FastAPI — Chatbot ILTB POC
Endpoints:
  POST /chat        — envia uma pergunta, recebe resposta RAG + LLM
  POST /ingest      — (re)indexa documentos da pasta docs/
  GET  /health      — status do serviço
  GET  /search      — busca trechos relevantes sem gerar resposta (debug)
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.config import settings
from src.llm.client import generate
from src.rag.ingestion import collection_exists, ingest_documents
from src.rag.retriever import build_context, retrieve

app = FastAPI(
    title="Chatbot ILTB — POC",
    description=(
        "Assistente clínico para enfermeiros sobre Infecção Latente pelo "
        "Mycobacterium tuberculosis (ILTB), baseado em RAG sobre protocolos do MS."
    ),
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=5, example="Qual é a dose de isoniazida para adultos no esquema 6H?")
    top_k: int = Field(default=4, ge=1, le=10)


class SourceChunk(BaseModel):
    source: str
    score: float
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    llm_provider: str
    llm_model: str


class IngestResponse(BaseModel):
    status: str
    chunks_indexed: int
    message: str


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_k: int = Field(default=4, ge=1, le=10)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "collection_ready": collection_exists(),
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
    }


@app.post("/ingest", response_model=IngestResponse)
def ingest():
    """Indexa (ou re-indexa) todos os documentos da pasta docs/."""
    try:
        total = ingest_documents()
        return IngestResponse(
            status="success",
            chunks_indexed=total,
            message=f"{total} chunks indexados com sucesso.",
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Responde uma pergunta clínica sobre ILTB usando RAG + LLM.
    Os documentos devem estar indexados (POST /ingest) antes de usar.
    """
    if not collection_exists():
        raise HTTPException(
            status_code=409,
            detail="Base de conhecimento não indexada. Execute POST /ingest primeiro.",
        )

    chunks = retrieve(request.question, top_k=request.top_k)

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="Nenhum trecho relevante encontrado para a pergunta.",
        )

    context = build_context(chunks)
    answer = generate(context=context, question=request.question)

    sources = [
        SourceChunk(
            source=c.source,
            score=c.score,
            excerpt=c.text[:300] + ("..." if len(c.text) > 300 else ""),
        )
        for c in chunks
    ]

    return ChatResponse(
        answer=answer,
        sources=sources,
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
    )


@app.post("/search")
def search(request: SearchRequest):
    """Busca trechos relevantes sem gerar resposta — útil para debug do RAG."""
    if not collection_exists():
        raise HTTPException(
            status_code=409,
            detail="Base de conhecimento não indexada. Execute POST /ingest primeiro.",
        )

    chunks = retrieve(request.query, top_k=request.top_k)
    return {
        "query": request.query,
        "results": [
            {"source": c.source, "score": c.score, "text": c.text}
            for c in chunks
        ],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host=settings.api_host, port=settings.api_port, reload=True)
