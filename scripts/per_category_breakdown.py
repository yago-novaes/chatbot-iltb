"""Gera breakdown por categoria do gate final (3 seeds).

Re-roda RAGAS sobre cada um dos 3 detailed.json do gate final
(eval/results/seeds/seed{1,2,3}_detailed.json), capturando metricas por amostra,
e agrega por categoria.

Saida:
  - eval/results/seeds/per_sample_seed{N}.json (3 arquivos)
  - eval/results/seeds/per_category.json (agregado)
  - imprime tabela LaTeX no stdout
"""
from __future__ import annotations

import json
import math
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Le env vars do .env e injeta ANTES de importar app.src.config (que faz Settings())
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
OPENAI_KEY = ENV.get("RAGAS_LLM_API_KEY", "")

# Sobrescreve env para garantir que o juiz seja gpt-4o-mini OpenAI
os.environ["RAGAS_LLM_PROVIDER"] = "openai"
os.environ["RAGAS_LLM_API_KEY"] = OPENAI_KEY
os.environ["RAGAS_LLM_MODEL"] = "gpt-4o-mini"
os.environ["RAGAS_LLM_BASE_URL"] = ""
# Garante que o embedding usado pelo RAGAS para answer_relevancy seja BGE-M3
os.environ["EMBEDDING_MODEL"] = "BAAI/bge-m3"

from app.src.config import settings  # noqa: E402

METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
SEEDS_DIR = ROOT / "eval" / "results" / "seeds"


def _run_ragas_per_sample(records: list[dict]) -> dict[str, list]:
    """Roda RAGAS retornando dict {metric: list_of_scores}, indexado pela ordem
    dos records."""
    from datasets import Dataset
    from langchain_openai import ChatOpenAI
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from ragas import RunConfig, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

    dataset = Dataset.from_dict({
        "question": [r["question"] for r in records],
        "answer": [r["answer"] for r in records],
        "contexts": [r["contexts"] for r in records],
        "ground_truth": [r["ground_truth"] for r in records],
    })

    evaluator_llm = ChatOpenAI(
        model="gpt-4o-mini",
        openai_api_key=OPENAI_KEY,
        temperature=0,
    )

    evaluator_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    )

    run_config = RunConfig(timeout=120, max_retries=3, max_workers=4)

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        run_config=run_config,
    )

    out: dict[str, list] = {}
    for m in METRICS:
        val = result[m]
        if isinstance(val, list):
            out[m] = [None if (v is None or (isinstance(v, float) and math.isnan(v))) else float(v) for v in val]
        else:
            out[m] = [None] * len(records)
    return out


def main() -> None:
    seeds = (1, 2, 3)
    # Carregar/processar cada seed
    per_seed_data: dict[int, list[dict]] = {}
    for s in seeds:
        per_sample_path = SEEDS_DIR / f"per_sample_seed{s}.json"
        if per_sample_path.exists():
            print(f"[seed{s}] reusando per_sample existente")
            per_seed_data[s] = json.loads(per_sample_path.read_text(encoding="utf-8"))
            continue

        detailed_path = SEEDS_DIR / f"seed{s}_detailed.json"
        records = json.loads(detailed_path.read_text(encoding="utf-8"))
        print(f"[seed{s}] rodando RAGAS sobre {len(records)} amostras...")
        per_sample = _run_ragas_per_sample(records)

        # Anota cada record com seus scores
        annotated = []
        for i, r in enumerate(records):
            annotated.append({
                "id": r["id"],
                "category": r["category"],
                "faithfulness": per_sample["faithfulness"][i],
                "answer_relevancy": per_sample["answer_relevancy"][i],
                "context_precision": per_sample["context_precision"][i],
                "context_recall": per_sample["context_recall"][i],
            })
        per_sample_path.write_text(json.dumps(annotated, ensure_ascii=False, indent=2), encoding="utf-8")
        per_seed_data[s] = annotated
        print(f"[seed{s}] salvo em {per_sample_path}")

    # Agregacao por categoria
    # Para cada categoria, para cada seed, calcula media da categoria.
    # Depois agrega media+-DP das 3 seeds.
    categories: dict[str, dict[str, list[float]]] = {}
    for s, annotated in per_seed_data.items():
        by_cat: dict[str, dict[str, list[float]]] = {}
        for rec in annotated:
            cat = rec["category"]
            by_cat.setdefault(cat, {m: [] for m in METRICS})
            for m in METRICS:
                if rec[m] is not None:
                    by_cat[cat][m].append(rec[m])
        for cat, mvals in by_cat.items():
            categories.setdefault(cat, {m: [] for m in METRICS})
            for m in METRICS:
                if mvals[m]:
                    categories[cat][m].append(statistics.mean(mvals[m]))

    # Reporta
    out_path = SEEDS_DIR / "per_category.json"
    agg = {}
    print()
    print(f"{'Cat.':<28} {'N':>3}  {'Faith.':>14}  {'Ans.Rel.':>14}  {'Ctx.Prec.':>14}  {'Ctx.Rec.':>14}")
    print("-" * 110)

    # Conta N por categoria (sobre seed1, igual para todas)
    n_by_cat: dict[str, int] = {}
    for rec in per_seed_data[1]:
        n_by_cat[rec["category"]] = n_by_cat.get(rec["category"], 0) + 1

    for cat in sorted(categories.keys()):
        row = {"n_questions": n_by_cat.get(cat, 0)}
        cells = []
        for m in METRICS:
            vals = categories[cat][m]
            if len(vals) >= 2:
                mean = statistics.mean(vals)
                sd = statistics.stdev(vals)
                row[m] = {"mean": round(mean, 4), "sd": round(sd, 4), "values": vals}
                cells.append(f"{mean:.3f}±{sd:.3f}")
            elif vals:
                row[m] = {"mean": round(vals[0], 4), "sd": 0.0, "values": vals}
                cells.append(f"{vals[0]:.3f}  N/A")
            else:
                row[m] = None
                cells.append("    N/A")
        agg[cat] = row
        print(f"{cat:<28} {n_by_cat.get(cat, 0):>3}  {cells[0]:>14}  {cells[1]:>14}  {cells[2]:>14}  {cells[3]:>14}")

    out_path.write_text(json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSalvo em {out_path}")

    # Gera LaTeX
    print("\n\n========== LaTeX (cole no apendice da monografia) ==========\n")
    cat_labels = {
        "esquemas_terapeuticos": "Esquemas terapêuticos (ET)",
        "indicacoes_tratamento": "Indicações de tratamento (IND)",
        "populacoes_especiais": "Populações especiais (PE)",
        "diagnostico": "Diagnóstico (DI)",
        "monitoramento": "Monitoramento (MO)",
        "interacoes_medicamentosas": "Interações medicamentosas (IT)",
        "efeitos_adversos": "Efeitos adversos (EA)",
    }
    for cat in sorted(categories.keys()):
        row = agg[cat]
        label = cat_labels.get(cat, cat)
        n = row["n_questions"]
        def fmt(m):
            d = row[m]
            if d is None:
                return "N/A"
            return f"${d['mean']:.3f} \\pm {d['sd']:.3f}$".replace(".", "{,}", 2).replace(".", "{,}")
        # Corrige: usa replace simples
        def fmt2(m):
            d = row[m]
            if d is None:
                return "N/A"
            mean_s = f"{d['mean']:.3f}".replace(".", "{,}")
            sd_s = f"{d['sd']:.3f}".replace(".", "{,}")
            return f"${mean_s} \\pm {sd_s}$"
        print(f"  {label} & {n} & {fmt2('faithfulness')} & {fmt2('answer_relevancy')} & {fmt2('context_precision')} & {fmt2('context_recall')} \\\\")


if __name__ == "__main__":
    main()
