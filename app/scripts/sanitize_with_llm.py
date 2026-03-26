"""
Sanitização estrutural de .md via API OpenAI (gpt-4o-mini).

Uso:
    python -m app.scripts.sanitize_with_llm [--dry-run] [--file <path>]

Flags:
    --dry-run    Processa apenas os 3 primeiros blocos e mostra diff sem salvar
    --file       Caminho do .md (default: Manual do MS)

Requer: OPENAI_API_KEY no .env ou variável de ambiente.
"""
import os
import sys
import time
from pathlib import Path
from openai import OpenAI

# === CONFIGURAÇÃO ===

DEFAULT_FILE = Path("docs/protocolos/Manual de Recomendações para o controle da Tuberculose no Brasil.md")
MODEL = "gpt-4o-mini"
MAX_INPUT_TOKENS = 3000  # tokens aprox por bloco
MAX_OUTPUT_TOKENS = 4096  # margem para output maior que input (formatação adicional)
SLEEP_BETWEEN_CALLS = 1  # segundos entre chamadas
MIN_OUTPUT_RATIO = 0.5   # output deve ser >= 50% do input (detecta truncamento)
MAX_OUTPUT_RATIO = 1.5   # output deve ser <= 150% do input (detecta invenção de texto)

# === SYSTEM PROMPT (ESTRITO — NÃO ALTERAR SEM JUSTIFICATIVA) ===

SYSTEM_PROMPT = """Você é um parser de Markdown especializado em documentos clínicos do Ministério da Saúde do Brasil.

Sua ÚNICA função é corrigir a ESTRUTURA DE FORMATAÇÃO (Markdown) do texto fornecido, que foi extraído de PDF com falhas de OCR/parsing.

REGRAS ABSOLUTAS — violação de qualquer regra invalida o output:

1. NUNCA altere, resuma, parafraseie ou remova qualquer termo médico, dosagem, número, sigla ou nome de fármaco.
2. NUNCA adicione texto, explicações ou informações que não estejam no original.
3. NUNCA altere o significado clínico de qualquer frase.
4. Preserve 100% do conteúdo textual — apenas corrija a formatação.

CORREÇÕES PERMITIDAS:

Hierarquia de cabeçalhos:
- Capítulos (1, 2, 3...) → ##
- Subseções (3.1, 4.2...) → ###
- Sub-subseções (3.1.1, 4.2.3...) → ####
- Cabeçalhos falsos (## IMPORTANTE, ## observações:, ## conclusão) → texto em negrito (**Importante:**)
- Cabeçalhos de número isolado (## 4 seguido de ## Das Atribuições) → fundir (## 4. Das Atribuições)

Tabelas:
- Tabelas partidas por quebra de página → unir em uma só
- Tabelas sem cabeçalho (primeira linha de dados usada como header) → adicionar linha de cabeçalho descritivo
- Tabelas de coluna única → converter para lista hierárquica com cabeçalhos
- Células vazias por rowspan falho → repetir valor da célula pai (desnormalizar)
- Listas esmagadas em células (• item1 • item2 na mesma linha) → converter para texto hierárquico com bullets separados

Listas:
- Bullets duplos (- - texto) → * texto
- Listas fragmentadas (parágrafos soltos entre itens numerados) → fundir ao item anterior
- Bullets híbridos (- 1 texto) → 1. texto
- Sub-listas sem indentação → indentar com 4 espaços

Artefatos de OCR:
- Palavras aglutinadas (TratamentodaILTB) → separar (Tratamento da ILTB)
- Capitalização anômala (QUADRo, FIcHA) → corrigir para Title Case
- Cabeçalhos/rodapés de página repetidos (WWW.GEDIIB.ORG.BR, nomes de ministérios) → remover
- Espaços dentro de palavras (consi derado) → corrigir (considerado)
- Caracteres de controle invisíveis → remover

NÃO CORRIGIR:
- Referências bibliográficas entre colchetes [1, 2] ou parênteses (1, 2) — manter como estão
- Siglas médicas em maiúsculas (ILTB, PVHIV, TB-DR) — manter
- Números de dose, mg/kg, intervalos (30-40 mg) — NUNCA alterar

Retorne EXCLUSIVAMENTE o Markdown corrigido, sem explicações, sem markdown code fences, sem comentários."""


def estimate_tokens(text: str) -> int:
    """Estimativa grosseira: 1 token ≈ 4 chars em português."""
    return len(text) // 4


def split_into_blocks(text: str, max_tokens: int = MAX_INPUT_TOKENS) -> list[str]:
    """Fatia o texto em blocos respeitando limites de seção (##)."""
    lines = text.split("\n")
    blocks = []
    current_block = []
    current_tokens = 0

    for line in lines:
        line_tokens = estimate_tokens(line)

        # Se adicionar esta linha excede o limite E o bloco não está vazio
        if current_tokens + line_tokens > max_tokens and current_block:
            # Se a linha é um cabeçalho, é um bom ponto de corte
            if line.startswith("#") or current_tokens + line_tokens > max_tokens * 1.2:
                blocks.append("\n".join(current_block))
                current_block = [line]
                current_tokens = line_tokens
                continue

        current_block.append(line)
        current_tokens += line_tokens

    # Último bloco
    if current_block:
        blocks.append("\n".join(current_block))

    return blocks


def sanitize_block(client: OpenAI, block: str, block_num: int, total: int) -> str:
    """Envia um bloco para gpt-4o-mini e retorna o resultado sanitizado."""
    input_tokens = estimate_tokens(block)

    print(f"  Bloco {block_num}/{total} ({input_tokens} tokens est.)...", end=" ", flush=True)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": block}
            ],
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.0,  # determinístico — sem criatividade
        )

        result = response.choices[0].message.content.strip()
        output_tokens = estimate_tokens(result)
        ratio = output_tokens / max(input_tokens, 1)

        # Validação de truncamento
        if ratio < MIN_OUTPUT_RATIO:
            print(f"AVISO TRUNCADO (ratio {ratio:.2f} < {MIN_OUTPUT_RATIO})")
            print(f"    Input: {input_tokens} tokens, Output: {output_tokens} tokens")
            print(f"    Mantendo bloco original.")
            return block

        # Validação de invenção de texto
        if ratio > MAX_OUTPUT_RATIO:
            print(f"AVISO EXPANDIDO (ratio {ratio:.2f} > {MAX_OUTPUT_RATIO})")
            print(f"    Input: {input_tokens} tokens, Output: {output_tokens} tokens")
            print(f"    Mantendo bloco original.")
            return block

        # Validação de finish_reason
        if response.choices[0].finish_reason != "stop":
            print(f"AVISO finish_reason={response.choices[0].finish_reason} — mantendo original")
            return block

        print(f"OK (ratio {ratio:.2f}, {response.usage.total_tokens} tokens API)")
        return result

    except Exception as e:
        print(f"ERRO: {e} — mantendo original")
        return block


def main():
    dry_run = "--dry-run" in sys.argv

    # Detectar arquivo
    file_path = DEFAULT_FILE
    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        if idx + 1 < len(sys.argv):
            file_path = Path(sys.argv[idx + 1])

    if not file_path.exists():
        print(f"Arquivo não encontrado: {file_path}")
        sys.exit(1)

    # Verificar API key
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        # Tentar carregar do .env
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY=") or line.startswith("RAGAS_LLM_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not api_key:
        print("ERRO: OPENAI_API_KEY não encontrada no ambiente ou .env")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # Ler arquivo
    original = file_path.read_text(encoding="utf-8")
    print(f"Arquivo: {file_path.name}")
    print(f"Tamanho: {len(original):,} chars, {len(original.splitlines()):,} linhas")
    print(f"Tokens estimados: ~{estimate_tokens(original):,}")

    # Fatiar
    blocks = split_into_blocks(original)
    print(f"Blocos: {len(blocks)}")

    if dry_run:
        blocks = blocks[:3]
        print(f"DRY RUN: processando apenas {len(blocks)} blocos")

    # Processar
    print(f"\nIniciando sanitização com {MODEL}...")
    sanitized_blocks = []
    errors = 0

    for i, block in enumerate(blocks, 1):
        result = sanitize_block(client, block, i, len(blocks))
        sanitized_blocks.append(result)

        if result == block:
            errors += 1

        if i < len(blocks):
            time.sleep(SLEEP_BETWEEN_CALLS)

    # Concatenar
    sanitized = "\n".join(sanitized_blocks)

    # Relatório
    print(f"\n{'='*60}")
    print(f"RELATÓRIO DE SANITIZAÇÃO")
    print(f"{'='*60}")
    print(f"Blocos processados: {len(blocks)}")
    print(f"Blocos com erro/fallback: {errors}")
    print(f"Chars: {len(original):,} -> {len(sanitized):,} ({len(sanitized) - len(original):+,})")
    print(f"Linhas: {len(original.splitlines()):,} -> {len(sanitized.splitlines()):,}")

    if dry_run:
        print(f"\nDRY RUN — arquivo NÃO foi salvo.")
        # Mostrar primeiras 60 linhas do output sanitizado
        sani_lines = sanitized.splitlines()
        orig_lines = original.splitlines()
        print(f"\nPrimeiras 60 linhas do output:")
        for i, line in enumerate(sani_lines[:60]):
            prefix = "  " if i < len(orig_lines) and line == orig_lines[i] else "* "
            print(f"{prefix}{line[:120]}")
    else:
        # Backup do original
        backup_path = file_path.with_suffix(".md.bak")
        if not backup_path.exists():
            file_path.rename(backup_path)
            print(f"Backup salvo: {backup_path.name}")
        else:
            print(f"Backup já existe: {backup_path.name} (não sobrescrito)")

        # Salvar sanitizado
        file_path.write_text(sanitized, encoding="utf-8")
        print(f"Arquivo sanitizado salvo: {file_path.name}")


if __name__ == "__main__":
    main()
