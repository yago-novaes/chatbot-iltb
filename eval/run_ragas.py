"""
Avaliação do pipeline RAG com métricas RAGAS.
Uso: python -m eval.run_ragas

Pré-requisitos:
  - Collection indexada (POST /ingest ou python -m app.scripts.ingest)
  - LLM_PROVIDER != "mock" e LLM_API_KEY válida no .env
  - pip install ragas datasets langchain-openai
"""
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.src.config import settings
from app.src.llm.client import generate
from app.src.rag.ingestion.indexer import collection_exists
from app.src.rag.retriever import retrieve

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

EVAL_DIR = Path(__file__).parent
TEST_SET = EVAL_DIR / "test_set.json"
RESULTS_DIR = EVAL_DIR / "results"

SLEEP_BETWEEN_CALLS = 2  # segundos — respeita rate limit do Groq free tier


def _check_prerequisites():
    if settings.llm_provider == "mock" or settings.llm_api_key in ("mock", "", None):
        print("ERRO: LLM está em modo mock. Configure LLM_PROVIDER e LLM_API_KEY no .env.")
        sys.exit(1)
    if not collection_exists():
        print("ERRO: Collection não indexada. Execute: python -m app.scripts.ingest")
        sys.exit(1)


def _load_test_set() -> list[dict]:
    data = json.loads(TEST_SET.read_text(encoding="utf-8"))
    # Filtra perguntas fora do escopo (sem ground_truth) — não entram no RAGAS
    in_scope = [q for q in data if q.get("ground_truth") is not None]
    out_of_scope = [q for q in data if q.get("ground_truth") is None]
    print(f"Test set: {len(in_scope)} perguntas in-scope + {len(out_of_scope)} fora do escopo")
    return in_scope, out_of_scope


async def _run_pipeline(question: str, top_k: int = 4) -> tuple[str, list[str]]:
    """Executa RAG completo: retrieve + generate. Retorna (resposta, [textos dos chunks])."""
    chunks = retrieve(question, top_k=top_k)
    if not chunks:
        return "Não encontrei trechos relevantes nos protocolos.", []

    from app.src.rag.retriever import build_context
    context = build_context(chunks)
    answer = await generate(context=context, question=question)
    return answer, [c.text for c in chunks]


async def _collect_results(questions: list[dict]) -> list[dict]:
    records = []
    for i, item in enumerate(questions, 1):
        q = item["question"]
        print(f"  [{i}/{len(questions)}] {q[:60]}...")
        try:
            answer, contexts = await _run_pipeline(q)
            records.append({
                "id": item["id"],
                "question": q,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": item["ground_truth"],
                "category": item["category"],
            })
        except Exception as e:
            logger.error("Erro na pergunta %s: %s", item["id"], e)
            records.append({
                "id": item["id"],
                "question": q,
                "answer": f"ERRO: {e}",
                "contexts": [],
                "ground_truth": item["ground_truth"],
                "category": item["category"],
            })
        if i < len(questions):
            time.sleep(SLEEP_BETWEEN_CALLS)
    return records


def _run_ragas(records: list[dict]) -> dict:
    try:
        from datasets import Dataset
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from ragas import RunConfig, evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
    except ImportError as e:
        print(f"\nERRO: Dependência não instalada: {e}")
        print("Execute: pip install ragas datasets langchain-openai")
        sys.exit(1)

    dataset = Dataset.from_dict({
        "question": [r["question"] for r in records],
        "answer": [r["answer"] for r in records],
        "contexts": [r["contexts"] for r in records],
        "ground_truth": [r["ground_truth"] for r in records],
    })

    # LLM juiz: usa RAGAS_LLM_* do .env se configurado, senão cai no LLM de produção
    if settings.ragas_llm_api_key:
        eval_api_key = settings.ragas_llm_api_key
        eval_model = settings.ragas_llm_model or "gemini-2.0-flash"
        eval_base_url = settings.ragas_llm_base_url or None
        # Provider dedicado (ex: Gemini): sem restrições de TPM restritivas — pode paralelizar
        run_config = RunConfig(timeout=120, max_retries=3, max_workers=4)
        print(f"LLM juiz: {eval_model} (provider dedicado — max_workers=4)")
    else:
        # Fallback: Groq free tier — TPM 6K tokens/min exige processamento sequencial
        eval_api_key = settings.llm_api_key
        eval_model = "llama-3.1-8b-instant"
        eval_base_url = settings.llm_base_url or None
        run_config = RunConfig(timeout=180, max_retries=3, max_workers=1)
        print(f"LLM juiz: {eval_model} (Groq fallback — max_workers=1, TPM restritivo)")

    evaluator_llm = ChatOpenAI(
        model=eval_model,
        openai_api_key=eval_api_key,
        openai_api_base=eval_base_url,
        temperature=0,
    )

    # Embeddings: usa sentence-transformers local (mesmo modelo do pipeline de produção)
    # Evita dependência de chave OpenAI para calcular answer_relevancy
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper

    evaluator_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name=settings.embedding_model)
    )

    print("\nCalculando métricas RAGAS (pode levar alguns minutos)...")
    try:
        result = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=evaluator_llm,
            embeddings=evaluator_embeddings,
            run_config=run_config,
        )
    except Exception as e:
        print(f"\nERRO ao executar RAGAS: {e}")
        print("Possíveis causas:")
        print("  - Rate limit do Groq durante avaliação (muitas chamadas simultâneas ao LLM)")
        print("  - Incompatibilidade de versão do RAGAS com Python 3.14")
        raise

    return result


def _print_summary(result) -> dict:
    targets = {"faithfulness": 0.80, "context_precision": 0.75}
    scores = {}

    # RAGAS 0.4: result[key] retorna lista de scores por amostra (não float agregado)
    # É necessário calcular a média manualmente, ignorando None e nan (jobs que falharam)
    import math

    def _get_score(name: str):
        try:
            val = result[name]
            if val is None:
                return None
            if isinstance(val, list):
                valid = [
                    v for v in val
                    if v is not None and not (isinstance(v, float) and math.isnan(v))
                ]
                return sum(valid) / len(valid) if valid else None
            v = float(val)
            return None if math.isnan(v) else v
        except (KeyError, TypeError):
            return None

    # Diagnóstico: quantas amostras foram avaliadas com sucesso por métrica
    def _valid_count(name: str) -> int:
        try:
            val = result[name]
            if not isinstance(val, list):
                return 0
            return sum(
                1 for v in val
                if v is not None and not (isinstance(v, float) and math.isnan(v))
            )
        except (KeyError, TypeError):
            return 0

    total = len(records) if hasattr(result, '__len__') else "?"

    print("\n=== Resultados RAGAS ===")
    any_score = False
    for metric_name in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        val = _get_score(metric_name)
        n_valid = _valid_count(metric_name)
        if val is None:
            print(f"  {metric_name:<22} N/A  (0/{total} amostras avaliadas — rate limit)")
            continue
        any_score = True
        score = round(float(val), 4)
        scores[metric_name] = score
        target = targets.get(metric_name)
        if target:
            status = "PASS" if score >= target else "FAIL"
            print(f"  {metric_name:<22} {score:.3f}  (alvo: >= {target})  [{status}]  ({n_valid}/{total} amostras)")
        else:
            print(f"  {metric_name:<22} {score:.3f}  ({n_valid}/{total} amostras)")
    print("=" * 40)

    if not any_score:
        print("\nNenhum score calculado — rate limit esgotado. Aguarde o reset do TPD (~24h) e rode --scores-only novamente.")
        return scores

    passed = all(
        scores.get(k, 0) >= v for k, v in targets.items() if k in scores
    )
    print(f"\n{'APROVADO - pipeline pronto para piloto.' if passed else 'REPROVADO - ajustes necessarios antes do piloto.'}")
    return scores


def _check_fallback(out_of_scope: list[dict]):
    """Verifica se o pipeline retorna fallback para perguntas fora do escopo."""
    print(f"\n--- Verificando fallback ({len(out_of_scope)} perguntas fora do escopo) ---")
    for item in out_of_scope:
        chunks = retrieve(item["question"], top_k=4)
        if not chunks:
            print(f"  OK  (sem chunks) — {item['question'][:60]}")
        else:
            max_score = max(c.score for c in chunks)
            print(f"  {'OK ' if max_score < 0.50 else 'AVISO'} (score máx: {max_score:.3f}) — {item['question'][:60]}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Avaliação RAGAS — Chatbot ILTB")
    parser.add_argument(
        "--scores-only",
        action="store_true",
        help="Recalcula apenas as métricas RAGAS usando ragas_detailed.json já salvo. "
             "Útil quando o pipeline RAG já foi executado mas a avaliação falhou (ex: TPD esgotado).",
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        default=None,
        metavar="N",
        help="Limita a avaliação RAGAS às primeiras N perguntas. "
             "Útil para caber no TPM do Groq free tier (6K tokens/min). "
             "Recomendado: --max-questions 12 (48 jobs, ~57K tokens total).",
    )
    args = parser.parse_args()

    print("=== Avaliação RAGAS — Chatbot ILTB ===\n")

    if args.scores_only:
        detailed_path = RESULTS_DIR / "ragas_detailed.json"
        if not detailed_path.exists():
            print(f"ERRO: {detailed_path} não encontrado. Execute sem --scores-only primeiro.")
            sys.exit(1)
        records = json.loads(detailed_path.read_text(encoding="utf-8"))
        print(f"Carregados {len(records)} registros de {detailed_path}")
        # Verifica apenas o LLM (não precisa de collection para recalcular métricas)
        if settings.llm_provider == "mock" or settings.llm_api_key in ("mock", "", None):
            print("ERRO: LLM está em modo mock. Configure LLM_PROVIDER e LLM_API_KEY no .env.")
            sys.exit(1)
    else:
        _check_prerequisites()
        in_scope, out_of_scope = _load_test_set()

        print("\nExecutando pipeline RAG para cada pergunta...")
        records = asyncio.run(_collect_results(in_scope))

        print("\nSalvando resultados detalhados...")
        RESULTS_DIR.mkdir(exist_ok=True)
        (RESULTS_DIR / "ragas_detailed.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    if args.max_questions and args.max_questions < len(records):
        print(f"Limitando avaliação a {args.max_questions}/{len(records)} perguntas (--max-questions).")
        records = records[:args.max_questions]

    result = _run_ragas(records)
    scores = _print_summary(result)

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "ragas_scores.json").write_text(
        json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nResultados salvos em {RESULTS_DIR}/")

    if not args.scores_only:
        _check_fallback(out_of_scope)


if __name__ == "__main__":
    main()
