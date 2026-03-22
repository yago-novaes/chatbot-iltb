"""
Extrai todos os PDFs de docs/protocolos/ para .md via Docling.
Salva os .md no mesmo diretório com o mesmo nome base.
Uso: python -m app.scripts.extract_pdfs [--force]
"""
import argparse
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.src.rag.ingestion.pdf_extractor import extract_markdown

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROTOCOLOS = Path(__file__).resolve().parents[2] / "docs" / "protocolos"


def sanitize_markdown(text: str) -> str:
    """Limpa artefatos comuns de extração Docling/OCR.

    Resolve problemas automáticos (~40% dos casos). Problemas estruturais
    (tabelas partidas, hierarquia de cabeçalhos, listas fragmentadas)
    exigem revisão manual — ver seção 2.14 do diário técnico.
    """
    # 1. Artefato de seta → bullet
    text = text.replace("Î ", "- ")

    # 2. Espaço no meio de palavras comuns
    text = text.replace("T abela", "Tabela")
    text = text.replace("F igura", "Figura")

    # 3. Remover marcadores de imagem
    text = re.sub(r"<!-- image -->\s*", "", text)

    # 4. Bullets duplos
    text = re.sub(r"^- - ", "* ", text, flags=re.MULTILINE)

    # 5. Múltiplos espaços (layout multi-coluna)
    text = re.sub(r"  +", " ", text)

    # 6. Espaço antes de vírgula/ponto (artefato de OCR)
    text = re.sub(r" ([,.])", r"\1", text)

    # 7. Espaço dentro de parênteses: "( texto )" → "(texto)"
    text = re.sub(r"\( ", "(", text)
    text = re.sub(r" \)", ")", text)

    # 8. Linhas de pontos de sumário/índice (10+ pontos seguidos)
    text = re.sub(r"\.{10,}", "", text)

    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Sobrescrever .md existentes")
    args = parser.parse_args()

    pdfs = sorted(PROTOCOLOS.glob("*.pdf"))
    if not pdfs:
        logger.error("Nenhum PDF encontrado em %s", PROTOCOLOS)
        sys.exit(1)

    generated, skipped, errors = 0, 0, 0

    for pdf in pdfs:
        md_path = pdf.with_suffix(".md")

        if md_path.exists() and not args.force:
            logger.info("Pulando %s (já existe — use --force para sobrescrever)", pdf.name)
            skipped += 1
            continue

        logger.info("Extraindo: %s", pdf.name)
        text = extract_markdown(pdf)
        text = sanitize_markdown(text)

        if not text:
            logger.error("  ERRO: extração retornou texto vazio para %s", pdf.name)
            errors += 1
            continue

        md_path.write_text(text, encoding="utf-8")
        logger.info("  Salvo: %s (%d chars)", md_path.name, len(text))
        generated += 1

    print(f"\n=== Extração concluída ===")
    print(f"  Gerados : {generated}")
    print(f"  Pulados : {skipped}")
    print(f"  Erros   : {errors}")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
