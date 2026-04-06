"""
Chunking semântico por seções markdown.
Estratégia validada na POC: divide em cabeçalhos ##/### antes de tamanho fixo.

MIN_CHUNK_SIZE: piso mínimo para flush do buffer. Se o buffer acumulado tiver
menos que MIN_CHUNK_SIZE chars, o próximo cabeçalho é concatenado ao bloco atual
em vez de gerar um chunk separado. Evita fragmentos inúteis em documentos com
hierarquia densa (ex: Manual do MS reconstruído com ####).
"""
import re
from typing import List

MIN_CHUNK_SIZE = 400


def split_by_sections(text: str, max_size: int = 800) -> List[str]:
    """
    Divide o markdown por cabeçalhos (## / ###).
    - Seções pequenas são agrupadas até max_size.
    - Buffer só é descarregado se atingiu MIN_CHUNK_SIZE (evita micro-chunks).
    - Seções maiores que max_size são subdivididas por parágrafos.
    """
    section_re = re.compile(r"(?=^#{1,3} )", re.MULTILINE)
    raw_sections = [s.strip() for s in section_re.split(text) if s.strip()]

    chunks: List[str] = []
    buffer = ""

    for section in raw_sections:
        if len(buffer) + len(section) <= max_size:
            # Cabe no buffer — acumula normalmente
            buffer = (buffer + "\n\n" + section).strip()
        elif len(buffer) < MIN_CHUNK_SIZE and len(section) <= max_size:
            # Buffer abaixo do piso e seção pequena — força acumulação
            buffer = (buffer + "\n\n" + section).strip()
        else:
            # Buffer atingiu o piso (ou seção é grande) — descarrega
            if buffer:
                chunks.append(buffer)
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
