"""
Instância compartilhada do embedding function.
Centraliza o carregamento do modelo (~120 MB) para evitar duplicação na RAM.
"""
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.src.config import settings

embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name=settings.embedding_model
)
