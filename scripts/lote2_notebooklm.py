"""
Submete as 24 perguntas do lote 2 (D1, D3, D4, D5, D6, D8, D9, D11) ao
NotebookLM via CLI e salva as respostas estruturadas em
docs/notebooklm_respostas/D{N}.md, mantendo o formato dos arquivos do lote 1.

Uso:
    .venv/Scripts/python.exe scripts/lote2_notebooklm.py             # roda todas
    .venv/Scripts/python.exe scripts/lote2_notebooklm.py --only D1   # roda apenas D1

Requer:
    - notebooklm-py instalado e autenticado (`notebooklm login`)
    - playwright + chromium
    - Notebook do TCC já em contexto (`notebooklm use <id>`)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs" / "notebooklm_respostas"
CLI = ROOT / ".venv" / "Scripts" / "notebooklm.exe"
TIMEOUT_S = 180
SLEEP_BETWEEN = 5  # segundos entre prompts (cortesia + evita rate limit)

# Mantém o ConversationID que foi usado no lote 1 (referência cruzada no diário 2.28)
# Vide _raw_history.json: "10219a1c-4f7d-4fb5-8b2c-29422ebd7e16"

PERGUNTAS = {
    "D1": {
        "decisao": "Arquitetura RAG vs fine-tuning",
        "embasamento_atual": "lewis2021, gao2024, bang2023 — status Forte",
        "perguntas": [
            ("Validação",
             "Os artigos disponíveis sustentam a escolha de arquitetura RAG (recuperação + geração) sobre fine-tuning de LLM para tarefas de pergunta-resposta sobre protocolos clínicos específicos? Cite os trechos principais que sustentam essa preferência em domínios de baixa frequência terminológica."),
            ("Lacuna",
             "Há nas fontes alguma comparação empírica direta entre RAG e fine-tuning para corpora pequenos (centenas a milhares de chunks) em domínio médico? Se sim, quais as métricas reportadas?"),
            ("Reconsiderar",
             "Existem nas fontes argumentos para preferir RAFT (Retrieval-Augmented Fine-Tuning) ou outras arquiteturas híbridas em vez de Naive RAG para o cenário deste TCC (corpus pequeno, domínio médico em português, sem rotulagem)?"),
        ],
    },
    "D3": {
        "decisao": "Vector Store: ChromaDB (HNSW)",
        "embasamento_atual": "malkov2016 (indireto, via HNSW) — status Parcial",
        "perguntas": [
            ("Validação",
             "Os artigos sustentam o uso do HNSW para busca aproximada de vizinhos mais próximos em corpora pequenos (< 10k chunks)? Cite trechos que justifiquem a escolha por critérios de complexidade computacional e robustez."),
            ("Lacuna",
             "Há comparações nas fontes entre ChromaDB, FAISS, Qdrant ou Pinecone em termos de latência, recall ou facilidade de operação para POCs acadêmicos? Se não, qual o critério recomendado para essa escolha?"),
            ("Reconsiderar",
             "Para um corpus de 898 chunks e demo via FastAPI+ngrok (sem servidor dedicado), as fontes apontam alguma alternativa mais leve ou mais adequada que ChromaDB? Indexação em memória pura seria suficiente?"),
        ],
    },
    "D4": {
        "decisao": "LLM: Llama 3.3 70B via Groq",
        "embasamento_atual": "dubey2024, brown2020, bang2023 — status Adequado",
        "perguntas": [
            ("Validação",
             "Os artigos disponíveis avaliam o desempenho do Llama 3.x (especialmente 70B) em tarefas de raciocínio em português ou em domínio médico? Há comparação com GPT-4 ou Claude em benchmarks clínicos?"),
            ("Lacuna",
             "Há nas fontes discussão sobre a tendência de modelos abstrativos (Llama, GPT) parafrasearem o contexto recuperado, penalizando métricas RAGAS baseadas em correspondência exata? Isso fundamenta o teto observado de faithfulness 0.515?"),
            ("Reconsiderar",
             "Os artigos sugerem LLMs alternativos mais adequados a respostas extrativas ou treinados em corpora médicos em português (e.g., Sabiá-2, Gemma médico, BioMistral) que justifiquem revisitar a escolha?"),
        ],
    },
    "D5": {
        "decisao": "Chunking Semântico por Cabeçalhos Markdown",
        "embasamento_atual": "gao2024, advancedChunkingRAG2025 — status Parcial",
        "perguntas": [
            ("Validação",
             "As fontes sustentam que chunking semântico por fronteiras estruturais do documento (cabeçalhos, seções) supera chunking por tamanho fixo em corpora estruturados (como protocolos clínicos)? Há resultados quantitativos?"),
            ("Lacuna",
             "Há nas fontes comparações controladas entre Small-to-Big, Sliding Window, DenseX e índice hierárquico para recuperação em texto técnico estruturado? Qual estratégia tem o melhor trade-off recall/precisão?"),
            ("Reconsiderar",
             "O experimento de chunking contextual (prefixar chunks com hierarquia de cabeçalhos) reduziu RAGAS neste projeto. As fontes explicam essa falha como propriedade dos embeddings de baixa dimensionalidade? Isso já justifica a decisão por não reverter, ou é argumento para migrar embedding antes (D2)?"),
        ],
    },
    "D6": {
        "decisao": "Framework de Avaliação: RAGAS",
        "embasamento_atual": "es2024 — status Forte",
        "perguntas": [
            ("Validação",
             "Os artigos discutem RAGAS como o framework de referência para avaliação reference-free de RAG? Há crítica metodológica relevante (vieses do LLM juiz, sensibilidade a paráfrase, dependência do modelo avaliador)?"),
            ("Lacuna",
             "As fontes mencionam alternativas a RAGAS (TruLens, ARES, DeepEval, BEIR adaptado) que possam complementar a avaliação? Qual a posição na literatura sobre uso combinado?"),
            ("Reconsiderar",
             "Para um projeto que avançará para avaliação com 1 expert clínico (e não piloto de 30 dias com 5 enfermeiras), as fontes recomendam manter RAGAS como instrumento primário, ou priorizar avaliação humana qualitativa estruturada (e.g., rubrica de Lin et al., G-Eval)?"),
        ],
    },
    "D8": {
        "decisao": "Metodologia DSRM",
        "embasamento_atual": "peffers2007 — status Forte",
        "perguntas": [
            ("Validação",
             "Os artigos confirmam DSRM como metodologia padrão para TCCs/dissertações que desenvolvem artefatos computacionais? Há aderência ao formato 6-fases (identificação do problema, objetivos, design, demonstração, avaliação, comunicação) em trabalhos análogos da área de IA em saúde?"),
            ("Lacuna",
             "Existem alternativas metodológicas mais recentes (Action Design Research — ADR, ou DSRM revisado pós-2015) que as fontes recomendem em vez do DSRM clássico para sistemas baseados em IA?"),
            ("Reconsiderar",
             "Com a mudança de piloto (5 enfermeiras × 30 dias) para avaliação com 1 expert, a fase de 'Demonstração' do DSRM ainda é robustamente atendida, ou as fontes recomendam complementar com outro instrumento (estudo de caso, ATC — Action-Theoretical Case Study)?"),
        ],
    },
    "D9": {
        "decisao": "Contexto Epidemiológico ILTB/TB",
        "embasamento_atual": "who2018, who2023, brasil2022, artigo_perfil — status Forte",
        "perguntas": [
            ("Validação",
             "As fontes consolidam o argumento epidemiológico de que ILTB é etapa crítica para eliminação da TB ativa no Brasil? Os dados de incidência, prevalência e cobertura de tratamento são suficientes para uma seção de 'Justificativa' de TCC?"),
            ("Lacuna",
             "Há nas fontes literatura específica sobre barreiras operacionais no manejo da ILTB pela enfermagem brasileira (esquemas 6H, 3HP, 4R; rastreio em PVHIV; contactantes domiciliares)?"),
            ("Reconsiderar",
             "Os documentos da WHO/MS citados estão na versão mais recente disponível? Há atualização de protocolo posterior a brasil2022 que mudaria recomendações de primeira linha?"),
        ],
    },
    "D11": {
        "decisao": "Busca Híbrida como Trabalho Futuro",
        "embasamento_atual": "cormack2009, formal2021, khattab2020 — status Adequado",
        "perguntas": [
            ("Validação",
             "As fontes sustentam que busca híbrida (densa + esparsa) supera busca apenas densa em corpora com terminologia técnica de baixa frequência (siglas, nomes de fármacos)? Há ganho quantitativo reportado?"),
            ("Lacuna",
             "Entre RRF (simples, sem parâmetros), SPLADE (esparso neural) e ColBERT (interação tardia), qual a recomendação para corpora pequenos (< 1000 chunks) em português médico? Há comparações nas fontes?"),
            ("Reconsiderar",
             "Diante do encerramento da Fase 5 (sem VPS) e do gate de faithfulness não atingido, vale antecipar a implementação de busca híbrida ainda no escopo do TCC, ou mantê-la como trabalho futuro é decisão metodologicamente defensável?"),
        ],
    },
}


def submeter(prompt: str) -> dict:
    """Chama o CLI notebooklm e retorna o JSON parseado da resposta."""
    proc = subprocess.run(
        [str(CLI), "ask", prompt, "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=TIMEOUT_S,
    )
    if proc.returncode != 0:
        return {"error": True, "stderr": proc.stderr.strip(), "stdout": proc.stdout.strip()}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return {"error": True, "exception": str(e), "stdout": proc.stdout.strip()}


def formatar_arquivo(decision_id: str, decision_meta: dict, respostas: list[dict]) -> str:
    """Gera o conteúdo Markdown para um arquivo D{N}.md no padrão do lote 1."""
    lines = [
        f"# {decision_id} — {decision_meta['decisao']}",
        "",
        f"**Embasamento atual da bibliografia:** {decision_meta['embasamento_atual']}",
        "",
        f"**Conversação NotebookLM:** captura via CLI (notebooklm-py) em {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
    ]
    for (categoria, pergunta), resposta in zip(decision_meta["perguntas"], respostas):
        lines.append(f"## {decision_id}.{categoria}")
        lines.append("")
        lines.append(f"**Pergunta:** {pergunta}")
        lines.append("")
        lines.append("### Resposta NotebookLM")
        lines.append("")
        if resposta.get("error"):
            lines.append(f"> ⚠️ ERRO ao chamar o NotebookLM:")
            lines.append(f"> stderr: `{resposta.get('stderr', '—')}`")
            lines.append(f"> stdout: `{resposta.get('stdout', '—')[:200]}`")
        else:
            lines.append(resposta["answer"])
            if resposta.get("references"):
                lines.append("")
                lines.append("**Referências citadas (source_ids):**")
                seen = set()
                for ref in resposta["references"]:
                    sid = ref["source_id"][:8]
                    if sid not in seen:
                        seen.add(sid)
                        lines.append(f"- [{ref['citation_number']}] `{sid}...` — `{ref['cited_text'][:80]}...`")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def main(only: list[str] | None = None) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    selecionadas = only if only else list(PERGUNTAS.keys())

    for decision_id in selecionadas:
        if decision_id not in PERGUNTAS:
            print(f"AVISO: {decision_id} não está no lote 2. Pulando.")
            continue
        meta = PERGUNTAS[decision_id]
        print(f"\n=== {decision_id} — {meta['decisao']} ===")
        respostas = []
        for i, (categoria, prompt) in enumerate(meta["perguntas"], 1):
            print(f"  [{i}/3] {categoria}: submetendo ({len(prompt)} chars)...", flush=True)
            t0 = time.time()
            resposta = submeter(prompt)
            elapsed = time.time() - t0
            if resposta.get("error"):
                print(f"      ERRO ({elapsed:.1f}s): {resposta.get('stderr', '—')[:120]}")
            else:
                print(f"      OK ({elapsed:.1f}s, {len(resposta.get('answer', ''))} chars de resposta)")
            respostas.append(resposta)
            if i < len(meta["perguntas"]):
                time.sleep(SLEEP_BETWEEN)

        # Salva o markdown
        md = formatar_arquivo(decision_id, meta, respostas)
        out_path = OUTPUT_DIR / f"{decision_id}.md"
        out_path.write_text(md, encoding="utf-8")
        print(f"  -> salvo em {out_path.relative_to(ROOT)}")

        # Pequeno respiro entre decisões
        if decision_id != selecionadas[-1]:
            time.sleep(SLEEP_BETWEEN)

    print("\n=== Lote 2 concluído ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submete o lote 2 de decisões ao NotebookLM")
    parser.add_argument(
        "--only",
        nargs="+",
        choices=list(PERGUNTAS.keys()),
        help="Submeter apenas decisões específicas (default: todas)",
    )
    args = parser.parse_args()
    main(only=args.only)
