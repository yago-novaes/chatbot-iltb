"""
Ingestion pipeline: lê documentos da pasta docs/, divide em chunks
e indexa no ChromaDB com embeddings locais (sentence-transformers).
"""
import re
from pathlib import Path
from typing import List

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from src.config import settings

COLLECTION_NAME = "iltb_protocols"

_embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)


def _get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=settings.chroma_path)


def _split_by_sections(text: str, max_size: int) -> List[str]:
    """
    Divide o markdown por cabeçalhos (##, ###).
    Se uma seção for maior que max_size, divide por parágrafos.
    Seções pequenas são agrupadas até o limite.
    """
    # Separa nas linhas que começam com ## ou ###
    section_re = re.compile(r"(?=^#{1,3} )", re.MULTILINE)
    raw_sections = [s.strip() for s in section_re.split(text) if s.strip()]

    chunks = []
    buffer = ""

    for section in raw_sections:
        # Seção cabe no buffer atual
        if len(buffer) + len(section) <= max_size:
            buffer = (buffer + "\n\n" + section).strip()
        else:
            # Salva o buffer e começa novo
            if buffer:
                chunks.append(buffer)
            # Seção maior que max_size: subdivide por parágrafos
            if len(section) > max_size:
                paragraphs = [p.strip() for p in re.split(r"\n{2,}", section) if p.strip()]
                sub = ""
                for para in paragraphs:
                    if len(sub) + len(para) <= max_size:
                        sub = (sub + "\n\n" + para).strip()
                    else:
                        if sub:
                            chunks.append(sub)
                        sub = para
                if sub:
                    chunks.append(sub)
                buffer = ""
            else:
                buffer = section

    if buffer:
        chunks.append(buffer)

    return chunks


def _load_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def ingest_documents(docs_path: str | None = None) -> int:
    """
    Lê todos os arquivos .md e .txt da pasta docs/ e indexa no ChromaDB.
    Retorna o número de chunks indexados.
    """
    folder = Path(docs_path or settings.docs_path)
    if not folder.exists():
        raise FileNotFoundError(f"Pasta de documentos não encontrada: {folder}")

    files = list(folder.glob("*.md")) + list(folder.glob("*.txt"))
    if not files:
        raise ValueError(f"Nenhum arquivo .md ou .txt encontrado em {folder}")

    client = _get_client()

    # Recriar a collection para garantir dados frescos
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=_embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    ids, documents, metadatas = [], [], []

    for file in files:
        text = _load_markdown(file)
        chunks = _split_by_sections(text, settings.chunk_size)
        for i, chunk in enumerate(chunks):
            ids.append(f"{file.stem}_{i}")
            documents.append(chunk)
            metadatas.append({"source": file.name, "chunk": i})

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


def collection_exists() -> bool:
    try:
        client = _get_client()
        client.get_collection(COLLECTION_NAME, embedding_function=_embedding_fn)
        return True
    except Exception:
        return False
