"""
Instância única do embedding function. O modelo tem ~120 MB, então carregar em
um lugar só evita segunda cópia na RAM.
"""
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.src.config import settings

embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name=settings.embedding_model
)
