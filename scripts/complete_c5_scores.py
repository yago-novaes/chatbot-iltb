"""Completa as 3 seeds da C5 (Llama+BGE-M3+hybrid sem rerank) rodando --scores-only
sobre os detailed.json ja cacheados em eval/results/multi_config_seeds/.

Pre-requisito: cota OpenAI restaurada (--scores-only chama gpt-4o-mini como juiz).
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
OUT_DIR = RESULTS / "multi_config_seeds"
DETAILED = RESULTS / "ragas_detailed.json"
SCORES = RESULTS / "ragas_scores.json"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"

CONFIG_ID = "C5_llama_bgem3_hybrid"

# Reaproveita as env vars da config C5 (Llama+BGE-M3+hybrid)
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

C5_ENV = {
    "LLM_PROVIDER": "groq",
    "LLM_API_KEY": GROQ_KEY,
    "LLM_MODEL": "llama-3.3-70b-versatile",
    "LLM_BASE_URL": "https://api.groq.com/openai/v1",
    "EMBEDDING_MODEL": "BAAI/bge-m3",
    "CHROMA_PATH": "./chroma_db_bgem3",
    "RETRIEVER_MODE": "hybrid",
    "RAGAS_LLM_PROVIDER": "openai",
    "RAGAS_LLM_API_KEY": OPENAI_KEY,
    "RAGAS_LLM_MODEL": "gpt-4o-mini",
    "RAGAS_LLM_BASE_URL": "",
}


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


def main() -> None:
    for seed in (1, 2, 3):
        out_scores = OUT_DIR / f"{CONFIG_ID}_seed{seed}_scores.json"
        # Verifica se ja tem scores validos
        if out_scores.exists():
            existing = json.loads(out_scores.read_text(encoding="utf-8"))
            if existing.get("faithfulness") is not None:
                log(f"seed{seed}: ja tem scores validos — pulando")
                continue

        detailed_src = OUT_DIR / f"{CONFIG_ID}_seed{seed}_detailed.json"
        if not detailed_src.exists():
            log(f"ERRO: {detailed_src} ausente — coleta nao foi feita")
            sys.exit(1)

        log(f"--- C5 seed{seed}: copiando detailed e rodando --scores-only ---")
        shutil.copy(detailed_src, DETAILED)

        sub_env = os.environ.copy()
        for k in list(sub_env.keys()):
            if k.startswith(("LLM_", "EMBEDDING_", "CHROMA_", "RETRIEVER_", "RERANKER_", "RAGAS_LLM_")):
                del sub_env[k]
        sub_env.update(C5_ENV)

        cmd = [str(PYTHON), "-m", "eval.run_ragas", "--scores-only"]
        proc = subprocess.run(cmd, cwd=ROOT, env=sub_env)
        if proc.returncode != 0:
            log(f"ERRO: seed{seed} exit code {proc.returncode}")
            sys.exit(proc.returncode)

        entry = latest_scores_entry()
        if entry is None or entry.get("faithfulness") is None:
            log(f"AVISO: scores ainda None — quota provavelmente ainda esgotada")
            sys.exit(2)

        entry["_config_id"] = CONFIG_ID
        entry["_config_label"] = "Llama 3.3 70B + BGE-M3 1024D + hybrid (sem rerank)"
        entry["_seed"] = seed
        out_scores.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"OK: faith={entry.get('faithfulness')}, ctx_prec={entry.get('context_precision')}")

    # Reagrega tudo
    log("Reagregando multi_config_seeds/aggregate.json...")
    proc = subprocess.run([str(PYTHON), str(ROOT / "scripts" / "run_multi_config_seeds.py")], cwd=ROOT)
    # Esse re-run vai pular tudo (todas as seeds ja tem scores.json validos) e so reagregar.

    log("CONCLUIDO")


if __name__ == "__main__":
    main()
