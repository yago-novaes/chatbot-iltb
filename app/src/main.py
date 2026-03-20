"""
Entrypoint FastAPI — Chatbot ILTB
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.src.config import settings
from app.src.api.routes import chat, health, ingest, search

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando %s v%s", settings.api_title, settings.api_version)
    yield
    logger.info("Encerrando")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=(
        "Assistente clínico para enfermeiros sobre Infecção Latente pelo "
        "Mycobacterium tuberculosis (ILTB), baseado em RAG sobre protocolos do MS."
    ),
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(ingest.router)
app.include_router(search.router)
