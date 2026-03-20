"""
POST /chat — recebe pergunta, retorna resposta via RAG.
TODO: integrar retriever + llm + session manager.
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    # Placeholder — será implementado ao conectar RAG + LLM
    raise NotImplementedError("chat endpoint not yet wired to RAG pipeline")
