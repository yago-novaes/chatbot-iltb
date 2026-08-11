"""
Extração de PDF via Docling, exportando para Markdown com os títulos e tabelas
preservados.
"""
import logging
from pathlib import Path

from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)

_converter = None


def _get_converter() -> DocumentConverter:
    global _converter
    if _converter is None:
        _converter = DocumentConverter()
    return _converter


def extract_markdown(pdf_path: Path) -> str:
    """
    Converte um PDF para Markdown, mantendo os cabeçalhos de que o chunker precisa.
    Devolve string vazia em caso de erro, tipo std::bad_alloc em PDF grande.
    """
    logger.info("Extraindo PDF: %s", pdf_path.name)
    try:
        result = _get_converter().convert(str(pdf_path))
        return result.document.export_to_markdown()
    except Exception as e:
        logger.error("Falha ao extrair %s: %s", pdf_path.name, e)
        return ""
