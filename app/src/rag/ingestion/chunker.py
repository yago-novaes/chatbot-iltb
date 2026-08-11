"""
Chunking por fronteiras de cabeçalho markdown.

Cabeçalho de nível 1-2 fecha o chunk na hora, porque marca troca de capítulo.
Nível 3-4 só fecha se o buffer já passou de MIN_CHUNK_SIZE; senão acumula, o que
evita picotar hierarquias densas em micro-fragmentos inúteis para o retriever.
Seção maior que max_size é subdividida por parágrafo.
"""
import re
from typing import List

MIN_CHUNK_SIZE = 400


def _heading_level(section: str) -> int:
    """Nível do cabeçalho que abre a seção (1 a 6), ou 0 se não houver."""
    m = re.match(r"^(#{1,6}) ", section)
    return len(m.group(1)) if m else 0


def _subdivide_by_paragraphs(section: str, max_size: int) -> List[str]:
    """Subdivide uma seção grande em sub-chunks por parágrafo."""
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", section) if p.strip()]
    chunks: List[str] = []
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
    return chunks


def split_by_sections(text: str, max_size: int = 800) -> List[str]:
    """Divide o markdown em chunks usando os cabeçalhos como fronteira."""
    section_re = re.compile(r"(?=^#{1,4} )", re.MULTILINE)
    raw_sections = [s.strip() for s in section_re.split(text) if s.strip()]

    chunks: List[str] = []
    buffer = ""

    for section in raw_sections:
        level = _heading_level(section)

        if level in (1, 2):
            if buffer:
                chunks.append(buffer)
            if len(section) > max_size:
                chunks.extend(_subdivide_by_paragraphs(section, max_size))
                buffer = ""
            else:
                buffer = section
            continue

        # nível 3-4, ou 0 para texto solto sem cabeçalho
        if len(buffer) + len(section) <= max_size:
            buffer = (buffer + "\n\n" + section).strip()
        elif len(buffer) < MIN_CHUNK_SIZE:
            # estoura max_size de propósito: melhor que emitir um micro-chunk
            buffer = (buffer + "\n\n" + section).strip()
        else:
            chunks.append(buffer)
            if len(section) > max_size:
                chunks.extend(_subdivide_by_paragraphs(section, max_size))
                buffer = ""
            else:
                buffer = section

    if buffer:
        chunks.append(buffer)

    return chunks
