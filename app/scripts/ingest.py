"""
CLI para indexar documentos da pasta docs/protocolos/ no ChromaDB.
Uso: python -m app.scripts.ingest
"""
import sys
from pathlib import Path

# garante que a raiz do projeto está no path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.src.rag.ingestion.indexer import ingest_documents


def main():
    print("Iniciando indexacao...")
    try:
        total = ingest_documents()
        print(f"OK: {total} chunks indexados.")
    except FileNotFoundError as e:
        print(f"ERRO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERRO inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
