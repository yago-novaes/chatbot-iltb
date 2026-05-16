"""Extrai turnos específicos do _raw_history.json para Markdown estruturado.

Uso:
  py _extract.py D2 8,10,11
  py _extract.py D7 12,13,14 --titles "Validação,Lacuna,Reconsiderar"
"""
import json
import sys
from pathlib import Path

DEFAULT_TITLES = ["Q1 — Validação", "Q2 — Lacuna", "Q3 — Reconsiderar"]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    decision = sys.argv[1]
    turns = [int(t) for t in sys.argv[2].split(",")]
    titles = DEFAULT_TITLES[: len(turns)]
    if "--titles" in sys.argv:
        i = sys.argv.index("--titles")
        titles = sys.argv[i + 1].split(",")

    here = Path(__file__).parent
    raw = json.loads((here / "_raw_history.json").read_text(encoding="utf-8"))
    pairs = {q["turn"]: q for q in raw["qa_pairs"]}

    out = [f"# {decision} — Respostas do NotebookLM\n"]
    out.append(f"**Notebook:** RAG Chatbot for Clinical Nursing Support in Latent Tuberculosis Management")
    out.append(f"**Conversation:** `{raw['conversation_id']}`\n")
    for turn, title in zip(turns, titles):
        if turn not in pairs:
            out.append(f"## {title} (turn {turn} — NÃO ENCONTRADO)\n")
            continue
        q = pairs[turn]
        out.append(f"## {title} (turn {turn})\n")
        out.append(f"**Pergunta:**\n\n> {q['question']}\n")
        out.append(f"**Resposta:**\n\n{q['answer']}\n")
        out.append("---\n")

    target = here / f"{decision}.md"
    target.write_text("\n".join(out), encoding="utf-8")
    print(f"Escrito: {target}")


if __name__ == "__main__":
    main()
