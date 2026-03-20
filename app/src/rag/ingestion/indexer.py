"""
Indexação de documentos no ChromaDB.
Suporta .md e .txt (Fase 1). PDF via pdf_extractor (Fase 2).
"""
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.src.config import settings
from app.src.rag.ingestion.chunker import split_by_sections

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


def ingest_documents(docs_path: str | None = None) -> int:
    """
    Lê .md e .txt da pasta docs_path e indexa no ChromaDB.
    Retorna o número de chunks indexados.
    """
    folder = Path(docs_path or settings.docs_path)
    if not folder.exists():
        raise FileNotFoundError(f"Pasta de documentos não encontrada: {folder}")

    files = list(folder.glob("*.md")) + list(folder.glob("*.txt"))
    if not files:
        raise ValueError(f"Nenhum arquivo .md ou .txt encontrado em {folder}")

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
        text = file.read_text(encoding="utf-8")
        chunks = split_by_sections(text, settings.chunk_size)
        for i, chunk in enumerate(chunks):
            ids.append(f"{file.stem}_{i}")
            documents.append(chunk)
            metadatas.append({"source": file.name, "chunk_index": i})

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)
