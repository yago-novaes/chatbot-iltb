"""
Entrypoint FastAPI — produção.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.src.config import settings
from app.src.api.routes import health, chat  # webhook added in Phase 2

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up %s v%s", settings.api_title, settings.api_version)
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(chat.router)
