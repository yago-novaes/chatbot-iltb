"""
Aplica sanitize_markdown() nos .md que ainda não foram higienizados manualmente.

Uso:
    python -m app.scripts.sanitize_existing_md [--dry-run]

Flag --dry-run mostra quantas linhas seriam alteradas sem salvar.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.scripts.extract_pdfs import sanitize_markdown

DOCS_DIR = Path("docs/protocolos")

# Arquivos já higienizados manualmente — NÃO tocar
SKIP_FILES = {
    "9789275728185_por.md",
    "af_protocolo_vigilancia_iltb_2ed_9jun22_ok_web.md",
    "GEDIIB_TratamentoTuberculose.md",
    "patch_interacoes_medicamentosas.md",
}


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    for md_file in sorted(DOCS_DIR.glob("*.md")):
        if md_file.name in SKIP_FILES:
            print(f"SKIP  {md_file.name}")
            continue

        original = md_file.read_text(encoding="utf-8")
        sanitized = sanitize_markdown(original)

        if original == sanitized:
            print(f"OK    {md_file.name}  (sem mudanças)")
            continue

        orig_lines = original.splitlines()
        sani_lines = sanitized.splitlines()
        diff_lines = sum(1 for a, b in zip(orig_lines, sani_lines) if a != b)
        char_diff = len(original) - len(sanitized)

        if dry_run:
            print(f"DRY   {md_file.name}  ({diff_lines} linhas alteradas, {char_diff:+d} chars)")
        else:
            md_file.write_text(sanitized, encoding="utf-8")
            print(f"DONE  {md_file.name}  ({diff_lines} linhas alteradas, {char_diff:+d} chars)")


if __name__ == "__main__":
    main()
