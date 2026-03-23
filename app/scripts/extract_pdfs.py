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

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROTOCOLOS = Path(__file__).resolve().parents[2] / "docs" / "protocolos"


def sanitize_markdown(text: str) -> str:
    """Limpa artefatos comuns de extração Docling/OCR.

    Camada 1 (automática): resolve ~40% dos problemas.
    Problemas estruturais (tabelas partidas, hierarquia de cabeçalhos,
    listas fragmentadas) exigem revisão manual (Camada 2).
    Ver seção 2.14 do diário técnico.
    """
    # === ARTEFATOS DE CARACTERE/OCR ===

    # 1. Artefato de seta → bullet
    text = text.replace("Î ", "- ")

    # 2. Espaço no meio de palavras comuns de extração
    text = text.replace("T abela", "Tabela")
    text = text.replace("F igura", "Figura")

    # 3. Remover marcadores de imagem
    text = re.sub(r"<!-- image -->\s*", "", text)

    # 4. Caracteres de controle Unicode lixo (ex: \x00-\x1f exceto \t, \n, \r)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    # 5. Caracteres de escape falsos em URLs e nomes de arquivo
    text = text.replace(r"\_", "_")
    text = text.replace(r"\-", "-")

    # === FORMATAÇÃO DE LISTAS ===

    # 6. Bullets duplos (- - texto → * texto)
    text = re.sub(r"^- - ", "* ", text, flags=re.MULTILINE)

    # 7. Bullets híbridos (- 1 texto → 1. texto)
    text = re.sub(r"^- (\d+)\s", r"\1. ", text, flags=re.MULTILINE)

    # === ESPAÇAMENTO ===

    # 8. Múltiplos espaços (layout multi-coluna)
    text = re.sub(r"  +", " ", text)

    # 9. Espaço antes de vírgula/ponto (artefato de OCR)
    text = re.sub(r" ([,.])", r"\1", text)

    # 10. Espaço dentro de parênteses: "( texto )" → "(texto)"
    text = re.sub(r"\( ", "(", text)
    text = re.sub(r" \)", ")", text)

    # 11. Espaço dentro de barras: "pulmonar/ laríngea" → "pulmonar/laríngea"
    text = re.sub(r" / ", "/", text)

    # === HIFENIZAÇÃO QUEBRADA POR OCR ===

    # 12. Palavras quebradas por hifenização de fim de linha
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # 13. Palavras com espaço no meio (hifenização OCR conhecida)
    common_broken = {
        "esta belecer": "estabelecer",
        "atuali zações": "atualizações",
        "consi derado": "considerado",
        "labo ratorialmente": "laboratorialmente",
        "desfa vorável": "desfavorável",
        "pron tuário": "prontuário",
        "tera pêuticos": "terapêuticos",
        "reco mendações": "recomendações",
        "cien tíficas": "científicas",
        "enfatizamse": "enfatizam-se",
        "devese": "deve-se",
        "ajudálos": "ajudá-los",
        "interrompêlas": "interrompê-las",
        "apressálas": "apressá-las",
        "pre cisa": "precisa",
    }
    for broken, fixed in common_broken.items():
        text = text.replace(broken, fixed)

    # === LIMPEZA DE SUMÁRIO/ÍNDICE ===

    # 14. Linhas de pontos de sumário/índice (10+ pontos seguidos)
    text = re.sub(r"\.{10,}", "", text)

    # === CITAÇÕES BIBLIOGRÁFICAS ===

    # 15. Números órfãos como referências (ex: "adoecimento 5 ," → "adoecimento [5],")
    text = re.sub(r"(\w) (\d{1,3}) ([;.,])", r"\1 [\2]\3", text)

    # === CAPITALIZAÇÃO ANÔMALA ===

    # 16. Corrigir "QUADRo" → "Quadro" (capitalização parcial de OCR)
    text = re.sub(r"QUADRo", "Quadro", text)

    # === URLs E EMAILS QUEBRADOS ===

    # 17. Espaços dentro de URLs
    def fix_url_spaces(match: re.Match) -> str:
        return match.group(0).replace(" ", "")

    text = re.sub(r"https?://[^\s\)>\"]+(?:\s+[^\s\)>\"]+)*", fix_url_spaces, text)

    # 18. Espaços em emails (ex: "tuberculose@ saude.gov.br")
    text = re.sub(r"(\w)@ (\w)", r"\1@\2", text)

    return text


def main():
    from app.src.rag.ingestion.pdf_extractor import extract_markdown

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
