"""
Extração de texto de PDFs via Docling (IBM).
Exporta para Markdown preservando títulos, tabelas e estrutura hierárquica.
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
    Converte um PDF para Markdown estruturado.
    Preserva títulos (## / ###), tabelas e parágrafos — compatível com o chunker existente.
    """
    logger.info("Extraindo PDF: %s", pdf_path.name)
    result = _get_converter().convert(str(pdf_path))
    return result.document.export_to_markdown()
