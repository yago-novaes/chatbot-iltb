"""
Indexação de documentos no ChromaDB.
Suporta .pdf, .md e .txt.
"""
import logging
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.src.config import settings
from app.src.rag.ingestion.chunker import split_by_sections
from app.src.rag.ingestion.pdf_extractor import extract_markdown

logger = logging.getLogger(__name__)

_embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name=settings.embedding_model
)


def _get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=settings.chroma_path)


def collection_exists() -> bool:
    try:
        _get_client().get_collection(settings.chroma_collection, embedding_function=_embedding_fn)
        return True
    except Exception:
        return False


def _load_text(file: Path) -> str:
    if file.suffix == ".pdf":
        return extract_markdown(file)
    return file.read_text(encoding="utf-8")


def ingest_documents(docs_path: str | None = None) -> int:
    """
    Lê .pdf, .md e .txt da pasta docs_path e indexa no ChromaDB.
    Retorna o número de chunks indexados.
    """
    folder = Path(docs_path or settings.docs_path)
    if not folder.exists():
        raise FileNotFoundError(f"Pasta de documentos não encontrada: {folder}")

    files = (
        list(folder.glob("*.pdf"))
        + list(folder.glob("*.md"))
        + list(folder.glob("*.txt"))
    )
    if not files:
        raise ValueError(f"Nenhum arquivo .pdf, .md ou .txt encontrado em {folder}")

    client = _get_client()
    try:
        client.delete_collection(settings.chroma_collection)
    except Exception:
        pass

    collection = client.create_collection(
        name=settings.chroma_collection,
        embedding_function=_embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    ids, documents, metadatas = [], [], []
    for file in files:
        logger.info("Processando: %s", file.name)
        text = _load_text(file)
        chunks = split_by_sections(text, settings.chunk_size)
        for i, chunk in enumerate(chunks):
            ids.append(f"{file.stem}_{i}")
            documents.append(chunk)
            metadatas.append({"source": file.name, "chunk_index": i})
        logger.info("  %d chunks gerados", len(chunks))

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    logger.info("Total indexado: %d chunks", len(ids))
    return len(ids)
