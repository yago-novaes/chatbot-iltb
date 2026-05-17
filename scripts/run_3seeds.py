"""Orquestra 3 seeds do RAGAS sobre o gate final.

Cada seed:
  1. Coleta respostas frescas do Llama (temp=0.1 → variancia natural).
  2. Roda RAGAS com gpt-4o-mini (temp=0 → juiz determinístico).
  3. Salva detailed/cache/scores em eval/results/seeds/seed{N}_*.json.

Resume-able: se ragas_detailed.json ja existir com 38 respostas validas,
pula a coleta e roda apenas --scores-only. Se ja existir
eval/results/seeds/seedN_scores.json, pula a seed inteira.

No final, agrega media +- DP por metrica em aggregate.json.
"""
from __future__ import annotations

import json
import shutil
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "eval" / "results"
SEEDS_DIR = RESULTS / "seeds"
CACHE = RESULTS / "_ragas_cache.json"
DETAILED = RESULTS / "ragas_detailed.json"
SCORES = RESULTS / "ragas_scores.json"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"

N_SEEDS = 3
METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run_python(*args: str) -> int:
    """Roda python sem redirecionar stderr (evita NativeCommandError do PS).

    Retorna exit code. stderr fica visivel inline.
    """
    cmd = [str(PYTHON), "-m", "eval.run_ragas", *args]
    log(f"$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode


def cache_has_full_38() -> bool:
    if not CACHE.exists():
        return False
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    return len(cache) >= 38


def detailed_has_full_38() -> bool:
    if not DETAILED.exists():
        return False
    data = json.loads(DETAILED.read_text(encoding="utf-8"))
    return len(data) >= 38


def latest_scores_entry() -> dict | None:
    if not SCORES.exists():
        return None
    hist = json.loads(SCORES.read_text(encoding="utf-8"))
    if not isinstance(hist, list) or not hist:
        return None
    return hist[-1]


def save_seed_artifacts(seed: int) -> dict:
    """Copia detailed/cache, extrai a ultima entrada de scores, salva tudo em seeds/."""
    SEEDS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(DETAILED, SEEDS_DIR / f"seed{seed}_detailed.json")
    shutil.copy(CACHE, SEEDS_DIR / f"seed{seed}_cache.json")
    entry = latest_scores_entry()
    if entry is None:
        raise RuntimeError("ragas_scores.json vazio ou ausente — RAGAS nao rodou")
    seed_scores_path = SEEDS_DIR / f"seed{seed}_scores.json"
    seed_scores_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry


def run_seed(seed: int, *, resume_from_detailed: bool = False) -> dict:
    """Roda uma seed completa (coleta + RAGAS) ou apenas RAGAS se resumindo.

    resume_from_detailed=True usa ragas_detailed.json existente (38 respostas) e roda
    apenas o RAGAS. Util quando coleta da seed ja completou mas RAGAS nao.
    """
    log(f"========== SEED {seed}/{N_SEEDS} ==========")

    seed_scores_path = SEEDS_DIR / f"seed{seed}_scores.json"
    if seed_scores_path.exists():
        log(f"seed{seed}_scores.json ja existe — pulando seed inteira")
        return json.loads(seed_scores_path.read_text(encoding="utf-8"))

    if resume_from_detailed and detailed_has_full_38():
        log(f"ragas_detailed.json ja tem 38 respostas — rodando apenas --scores-only")
        rc = run_python("--scores-only")
    else:
        log("Limpando cache e coletando do zero")
        rc = run_python("--clear-cache")

    if rc != 0:
        log(f"ERRO: exit code {rc} na seed {seed}. Inspect output acima.")
        sys.exit(rc)

    entry = save_seed_artifacts(seed)
    log(f"Seed {seed} OK: {entry}")
    return entry


def aggregate() -> dict:
    log("========== AGREGACAO ==========")
    runs = []
    for i in range(1, N_SEEDS + 1):
        p = SEEDS_DIR / f"seed{i}_scores.json"
        if not p.exists():
            log(f"AVISO: {p} ausente — agregacao incompleta")
            continue
        runs.append(json.loads(p.read_text(encoding="utf-8")))

    if len(runs) < 2:
        log("Menos de 2 seeds completas — DP nao calculavel")
        return {"n_seeds": len(runs), "per_seed": runs}

    out = {"n_seeds": len(runs), "per_seed": runs, "aggregate": {}}
    print()
    print(f"{'Metric':<22} {'Mean':>8}  {'SD':>8}  {'Min':>8}  {'Max':>8}")
    print("-" * 60)
    for m in METRICS:
        vals = [float(r[m]) for r in runs if m in r]
        mean = statistics.mean(vals)
        sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
        out["aggregate"][m] = {
            "mean": round(mean, 4),
            "sd": round(sd, 4),
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
            "values": vals,
        }
        print(f"{m:<22} {mean:8.4f}  {sd:8.4f}  {min(vals):8.4f}  {max(vals):8.4f}")

    agg_path = SEEDS_DIR / "aggregate.json"
    agg_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nAggregate salvo em {agg_path}")
    return out


def main() -> None:
    SEEDS_DIR.mkdir(parents=True, exist_ok=True)

    # Seed 1: pode ter detailed.json com 38 respostas ja coletadas (da execucao
    # PowerShell anterior que abortou antes de RAGAS) — reaproveitar.
    seed1_has_detailed = detailed_has_full_38() and not (SEEDS_DIR / "seed1_scores.json").exists()
    run_seed(1, resume_from_detailed=seed1_has_detailed)

    # Seeds 2 e 3: sempre coleta nova
    run_seed(2, resume_from_detailed=False)
    run_seed(3, resume_from_detailed=False)

    aggregate()
    log("CONCLUIDO")


if __name__ == "__main__":
    main()
