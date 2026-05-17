"""Varredura de top_k sobre o pipeline final (Llama+BGE-M3+hybrid+rerank).

Roda RAGAS para k in {3, 5, 7, 10} em corrida unica por valor (sem replicacao
multi-seed) para mostrar sensibilidade da metrica ao parametro de retrieval.

Saida:
  - eval/results/sweep_topk/k{3,5,7,10}_detailed.json
  - eval/results/sweep_topk/k{3,5,7,10}_scores.json
  - eval/results/sweep_topk/summary.json
  - imprime tabela LaTeX no stdout
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "eval" / "results"
OUT_DIR = RESULTS / "sweep_topk"
CACHE = RESULTS / "_ragas_cache.json"
DETAILED = RESULTS / "ragas_detailed.json"
SCORES = RESULTS / "ragas_scores.json"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"

K_VALUES = [3, 5, 7, 10]
METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


def _read_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip()
    return out


ENV = _read_env_file(ROOT / ".env")
GROQ_KEY = ENV.get("LLM_API_KEY", "")
OPENAI_KEY = ENV.get("RAGAS_LLM_API_KEY", "")


def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def latest_scores_entry() -> dict | None:
    if not SCORES.exists():
        return None
    hist = json.loads(SCORES.read_text(encoding="utf-8"))
    if not isinstance(hist, list) or not hist:
        return None
    return hist[-1]


def run_one_k(k: int) -> dict | None:
    out_scores = OUT_DIR / f"k{k}_scores.json"
    if out_scores.exists():
        log(f"k={k} ja existe — pulando")
        return json.loads(out_scores.read_text(encoding="utf-8"))

    log(f"--- k={k} ---")
    if CACHE.exists():
        CACHE.unlink()

    sub_env = os.environ.copy()
    for var in list(sub_env.keys()):
        if var.startswith(("LLM_", "EMBEDDING_", "CHROMA_", "RETRIEVER_", "RERANKER_", "RAGAS_LLM_")):
            del sub_env[var]
    # Pipeline final
    sub_env.update({
        "LLM_PROVIDER": "groq",
        "LLM_API_KEY": GROQ_KEY,
        "LLM_MODEL": "llama-3.3-70b-versatile",
        "LLM_BASE_URL": "https://api.groq.com/openai/v1",
        "EMBEDDING_MODEL": "BAAI/bge-m3",
        "CHROMA_PATH": "./chroma_db_bgem3",
        "RETRIEVER_MODE": "hybrid_rerank",
        "RETRIEVER_TOP_K": str(k),
        "RAGAS_LLM_PROVIDER": "openai",
        "RAGAS_LLM_API_KEY": OPENAI_KEY,
        "RAGAS_LLM_MODEL": "gpt-4o-mini",
        "RAGAS_LLM_BASE_URL": "",
    })

    cmd = [str(PYTHON), "-m", "eval.run_ragas", "--clear-cache"]
    log(f"$ env RETRIEVER_TOP_K={k} python -m eval.run_ragas --clear-cache")
    proc = subprocess.run(cmd, cwd=ROOT, env=sub_env)
    if proc.returncode != 0:
        log(f"ERRO: k={k} exit code {proc.returncode}")
        return None

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(DETAILED, OUT_DIR / f"k{k}_detailed.json")

    entry = latest_scores_entry()
    if entry is None:
        log(f"AVISO: scores nao salvos para k={k}")
        return None
    entry["_top_k"] = k
    out_scores.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"OK k={k}: faith={entry.get('faithfulness')}, ans_rel={entry.get('answer_relevancy')}, ctx_prec={entry.get('context_precision')}, ctx_rec={entry.get('context_recall')}")
    return entry


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[int, dict] = {}
    for k in K_VALUES:
        entry = run_one_k(k)
        if entry is not None:
            results[k] = entry

    summary = {
        "k_values": K_VALUES,
        "n_questions": 38,
        "seeds": 1,
        "pipeline": "Llama 3.3 70B + BGE-M3 1024D + hybrid + rerank mGTE",
        "judge": "gpt-4o-mini (temp=0)",
        "results": {str(k): results.get(k) for k in K_VALUES},
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # Tabela
    print()
    print(f"{'k':<4} {'Faith.':>9}  {'Ans.Rel.':>9}  {'Ctx.Prec.':>10}  {'Ctx.Rec.':>9}")
    print("-" * 50)
    for k in K_VALUES:
        e = results.get(k)
        if not e:
            print(f"{k:<4}  N/A")
            continue
        print(f"{k:<4} {e['faithfulness']:>9.4f}  {e['answer_relevancy']:>9.4f}  {e['context_precision']:>10.4f}  {e['context_recall']:>9.4f}")

    # LaTeX
    print("\n\n========== LaTeX ==========\n")
    for k in K_VALUES:
        e = results.get(k)
        if not e:
            continue
        cells = []
        for m in METRICS:
            v = f"{e[m]:.3f}".replace(".", "{,}")
            cells.append(f"${v}$")
        marker = "\\textbf{" if k == 5 else ""
        endm = "}" if k == 5 else ""
        print(f"  {marker}{k}{endm} & {cells[0]} & {cells[1]} & {cells[2]} & {cells[3]} \\\\")


if __name__ == "__main__":
    main()
