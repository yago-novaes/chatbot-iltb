#!/usr/bin/env python
"""
Script CLI para indexar os documentos no ChromaDB.
Executar da raiz do projeto:
    python scripts/ingest.py
"""
import sys
from pathlib import Path

# garante que src/ está no path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.ingestion import ingest_documents

if __name__ == "__main__":
    print("Iniciando ingestão dos documentos...")
    try:
        total = ingest_documents()
        print(f"OK: {total} chunks indexados com sucesso.")
    except Exception as e:
        print(f"ERRO: {e}")
        sys.exit(1)
