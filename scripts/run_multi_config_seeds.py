"""Roda 3 seeds para cada configuracao da ablacao 2x2 + iteracoes pos-recuperacao.

Configuracoes (gate final ja rodado em separado, ver eval/results/seeds/):

  C1: Llama 3.3 70B + MiniLM 384D + dense           (ablacao Tabela 4.4 linha 1)
  C2: GPT-4o          + MiniLM 384D + dense           (ablacao Tabela 4.4 linha 2)
  C3: GPT-4o          + BGE-M3 1024D + dense          (ablacao Tabela 4.4 linha 3)
  C4: Llama 3.3 70B + BGE-M3 1024D + dense           (ablacao Tabela 4.4 linha 4 / pos-mig)
  C5: Llama 3.3 70B + BGE-M3 1024D + hybrid          (Tabela 4.5 linha 2)

Cada configuracao roda 3 seeds (re-coleta Llama temp=0.1 / GPT-4o temp=0 — note que
GPT-4o sera 0 por escolha de pipeline, ver pipeline_temperature_override se quiser
forcar 0.1 para variancia).

Saidas: eval/results/multi_config_seeds/{config}_seed{N}_{cache,detailed,scores}.json
Agregacao: eval/results/multi_config_seeds/aggregate.json

Resume-able: pula configs/seeds ja com arquivo de scores presente.
"""
from __future__ import annotations

import json
import os
import shutil
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "eval" / "results"
OUT_DIR = RESULTS / "multi_config_seeds"
CACHE = RESULTS / "_ragas_cache.json"
DETAILED = RESULTS / "ragas_detailed.json"
SCORES = RESULTS / "ragas_scores.json"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"

N_SEEDS = 3
METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]

# Lendo .env apenas para extrair as chaves de API (nao queremos depender do
# Settings auto-load, que tambem le LLM_* do env do shell e provoca o bug do
# override). Lemos manualmente e injetamos APENAS o que queremos.
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

GROQ_KEY = ENV.get("LLM_API_KEY", "")  # assumindo .env atual tem chave Groq
OPENAI_KEY = ENV.get("RAGAS_LLM_API_KEY", "")  # OpenAI usada pelo juiz; reutilizamos como gerador GPT-4o

# Sanidade
if not GROQ_KEY.startswith("gsk_"):
    print(f"ERRO: LLM_API_KEY no .env nao parece chave Groq (esperado gsk_...). Recebido: {GROQ_KEY[:8]}...")
    sys.exit(2)
if not OPENAI_KEY.startswith("sk-"):
    print(f"ERRO: RAGAS_LLM_API_KEY no .env nao parece chave OpenAI. Recebido: {OPENAI_KEY[:8]}...")
    sys.exit(2)

# Configuracoes (todas usam mesmo juiz RAGAS: gpt-4o-mini via OpenAI)
CONFIGS: list[dict] = [
    {
        "id": "C1_llama_minilm_dense",
        "label": "Llama 3.3 70B + MiniLM 384D + dense",
        "env": {
            "LLM_PROVIDER": "groq",
            "LLM_API_KEY": GROQ_KEY,
            "LLM_MODEL": "llama-3.3-70b-versatile",
            "LLM_BASE_URL": "https://api.groq.com/openai/v1",
            "EMBEDDING_MODEL": "paraphrase-multilingual-MiniLM-L12-v2",
            "CHROMA_PATH": "./chroma_db_minilm384",
            "RETRIEVER_MODE": "dense",
        },
    },
    {
        "id": "C2_gpt4o_minilm_dense",
        "label": "GPT-4o + MiniLM 384D + dense",
        "env": {
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": OPENAI_KEY,
            "LLM_MODEL": "gpt-4o",
            "LLM_BASE_URL": "https://api.openai.com/v1",
            "EMBEDDING_MODEL": "paraphrase-multilingual-MiniLM-L12-v2",
            "CHROMA_PATH": "./chroma_db_minilm384",
            "RETRIEVER_MODE": "dense",
        },
    },
    {
        "id": "C3_gpt4o_bgem3_dense",
        "label": "GPT-4o + BGE-M3 1024D + dense",
        "env": {
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": OPENAI_KEY,
            "LLM_MODEL": "gpt-4o",
            "LLM_BASE_URL": "https://api.openai.com/v1",
            "EMBEDDING_MODEL": "BAAI/bge-m3",
            "CHROMA_PATH": "./chroma_db_bgem3",
            "RETRIEVER_MODE": "dense",
        },
    },
    {
        "id": "C4_llama_bgem3_dense",
        "label": "Llama 3.3 70B + BGE-M3 1024D + dense (pos-migracao)",
        "env": {
            "LLM_PROVIDER": "groq",
            "LLM_API_KEY": GROQ_KEY,
            "LLM_MODEL": "llama-3.3-70b-versatile",
            "LLM_BASE_URL": "https://api.groq.com/openai/v1",
            "EMBEDDING_MODEL": "BAAI/bge-m3",
            "CHROMA_PATH": "./chroma_db_bgem3",
            "RETRIEVER_MODE": "dense",
        },
    },
    {
        "id": "C5_llama_bgem3_hybrid",
        "label": "Llama 3.3 70B + BGE-M3 1024D + hybrid (sem rerank)",
        "env": {
            "LLM_PROVIDER": "groq",
            "LLM_API_KEY": GROQ_KEY,
            "LLM_MODEL": "llama-3.3-70b-versatile",
            "LLM_BASE_URL": "https://api.groq.com/openai/v1",
            "EMBEDDING_MODEL": "BAAI/bge-m3",
            "CHROMA_PATH": "./chroma_db_bgem3",
            "RETRIEVER_MODE": "hybrid",
        },
    },
]


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


def run_one_seed(config: dict, seed: int) -> dict | None:
    """Roda 1 seed: limpa cache, coleta, RAGAS, salva. Retorna scores dict."""
    out_scores = OUT_DIR / f"{config['id']}_seed{seed}_scores.json"
    if out_scores.exists():
        log(f"{config['id']} seed{seed}: ja existe — pulando")
        return json.loads(out_scores.read_text(encoding="utf-8"))

    log(f"--- {config['id']} seed{seed} ({config['label']}) ---")

    # Limpa cache antes da nova coleta
    if CACHE.exists():
        CACHE.unlink()

    # Monta env do subprocess: herda PATH e essencial Windows, mas sobrescreve LLM_*/EMBEDDING_/CHROMA_/RETRIEVER_
    sub_env = os.environ.copy()
    # Remove qualquer LLM_* previo do shell para evitar override surpresa
    for k in list(sub_env.keys()):
        if k.startswith(("LLM_", "EMBEDDING_", "CHROMA_", "RETRIEVER_", "RERANKER_")):
            del sub_env[k]
    sub_env.update(config["env"])
    # Mantem juiz RAGAS sempre OpenAI gpt-4o-mini
    sub_env["RAGAS_LLM_PROVIDER"] = "openai"
    sub_env["RAGAS_LLM_API_KEY"] = OPENAI_KEY
    sub_env["RAGAS_LLM_MODEL"] = "gpt-4o-mini"
    sub_env["RAGAS_LLM_BASE_URL"] = ""

    cmd = [str(PYTHON), "-m", "eval.run_ragas", "--clear-cache"]
    log(f"$ env LLM={config['env']['LLM_MODEL']} EMB={config['env']['EMBEDDING_MODEL']} CHROMA={config['env']['CHROMA_PATH']} MODE={config['env']['RETRIEVER_MODE']} ...")
    proc = subprocess.run(cmd, cwd=ROOT, env=sub_env)
    if proc.returncode != 0:
        log(f"ERRO: {config['id']} seed{seed} exit code {proc.returncode}")
        return None

    # Salva artefatos
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(DETAILED, OUT_DIR / f"{config['id']}_seed{seed}_detailed.json")
    shutil.copy(CACHE, OUT_DIR / f"{config['id']}_seed{seed}_cache.json")

    entry = latest_scores_entry()
    if entry is None:
        log(f"AVISO: ragas_scores.json sem entrada — RAGAS nao salvou")
        return None
    # Anota config
    entry["_config_id"] = config["id"]
    entry["_config_label"] = config["label"]
    entry["_seed"] = seed
    out_scores.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"OK: faith={entry.get('faithfulness')}, ans_rel={entry.get('answer_relevancy')}, ctx_prec={entry.get('context_precision')}, ctx_rec={entry.get('context_recall')}")
    return entry


def aggregate_all() -> None:
    log("========== AGREGACAO FINAL ==========")
    agg: dict[str, dict] = {}
    for cfg in CONFIGS:
        runs = []
        for i in range(1, N_SEEDS + 1):
            p = OUT_DIR / f"{cfg['id']}_seed{i}_scores.json"
            if p.exists():
                runs.append(json.loads(p.read_text(encoding="utf-8")))
        if not runs:
            continue
        config_agg = {"label": cfg["label"], "n_seeds": len(runs), "per_seed": runs, "aggregate": {}}
        for m in METRICS:
            vals = [float(r[m]) for r in runs if m in r and r[m] is not None]
            if not vals:
                continue
            mean = statistics.mean(vals)
            sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
            config_agg["aggregate"][m] = {
                "mean": round(mean, 4),
                "sd": round(sd, 4),
                "min": round(min(vals), 4),
                "max": round(max(vals), 4),
                "values": vals,
            }
        agg[cfg["id"]] = config_agg

    out_path = OUT_DIR / "aggregate.json"
    out_path.write_text(json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8")

    # Pretty print
    print()
    print(f"{'Config':<48} {'Faith.':>12}  {'Ans.Rel.':>12}  {'Ctx.Prec.':>12}  {'Ctx.Rec.':>12}")
    print("-" * 100)
    for cfg_id, ca in agg.items():
        ag = ca["aggregate"]
        def fmt(m):
            d = ag.get(m, {})
            if not d:
                return "        N/A"
            return f"{d['mean']:.3f}±{d['sd']:.3f}"
        print(f"{cfg_id:<48} {fmt('faithfulness'):>12}  {fmt('answer_relevancy'):>12}  {fmt('context_precision'):>12}  {fmt('context_recall'):>12}")

    log(f"Aggregate salvo em {out_path}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log(f"Total: {len(CONFIGS)} configs x {N_SEEDS} seeds = {len(CONFIGS)*N_SEEDS} corridas")

    for cfg in CONFIGS:
        for seed in range(1, N_SEEDS + 1):
            run_one_seed(cfg, seed)

    aggregate_all()
    log("CONCLUIDO")


if __name__ == "__main__":
    main()
