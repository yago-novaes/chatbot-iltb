"""
Chunking semântico por fronteiras hierárquicas.

Estratégia: o nível do cabeçalho determina o comportamento de flush.

  Nível 1-2 (# / ##)  → flush imediato. São mudanças de capítulo/parte.
  Nível 3-4 (### / ####) → flush condicional: só descarrega o buffer se
                            ele já tem >= MIN_CHUNK_SIZE chars. Caso contrário,
                            acumula a subseção no buffer atual para evitar
                            micro-fragmentos em hierarquias densas.

Seções maiores que max_size são subdivididas por parágrafos.
"""
import re
from typing import List

MIN_CHUNK_SIZE = 400


def _heading_level(section: str) -> int:
    """Retorna o nível do cabeçalho que abre a seção (1–6), ou 0 se não houver."""
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
    """
    Divide o markdown usando fronteiras hierárquicas:
    - # / ##  → split imediato (mudança de capítulo)
    - ### / #### → split só se buffer >= MIN_CHUNK_SIZE (evita micro-chunks)
    - Seções maiores que max_size são subdivididas por parágrafos.
    """
    # Captura cabeçalhos de todos os níveis relevantes (1–4)
    section_re = re.compile(r"(?=^#{1,4} )", re.MULTILINE)
    raw_sections = [s.strip() for s in section_re.split(text) if s.strip()]

    chunks: List[str] = []
    buffer = ""

    for section in raw_sections:
        level = _heading_level(section)

        # Níveis 1-2: fronteira de capítulo — flush imediato
        if level in (1, 2):
            if buffer:
                chunks.append(buffer)
            if len(section) > max_size:
                chunks.extend(_subdivide_by_paragraphs(section, max_size))
                buffer = ""
            else:
                buffer = section
            continue

        # Níveis 3-4 (e 0 = conteúdo sem cabeçalho): flush condicional
        if len(buffer) + len(section) <= max_size:
            # Cabe no buffer — acumula
            buffer = (buffer + "\n\n" + section).strip()
        elif len(buffer) < MIN_CHUNK_SIZE:
            # Buffer abaixo do piso — força acumulação mesmo estourando max_size
            # (preferível a um micro-chunk isolado)
            buffer = (buffer + "\n\n" + section).strip()
        else:
            # Buffer acima do piso — descarrega e processa a seção
            chunks.append(buffer)
            if len(section) > max_size:
                chunks.extend(_subdivide_by_paragraphs(section, max_size))
                buffer = ""
            else:
                buffer = section

    if buffer:
        chunks.append(buffer)

    return chunks
