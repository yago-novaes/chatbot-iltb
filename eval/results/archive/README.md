# Archive de resultados RAGAS — Chatbot ILTB

Snapshots das execuções de avaliação automatizada conduzidas ao longo do projeto.
Cada execução produz dois artefatos:

- `*.cache.json` — dicionário `{qid: {question, answer, contexts, ground_truth, category}}` usado pelo `eval/run_ragas.py` como checkpoint
- `*.detailed.json` — lista ordenada com os mesmos registros, formato consumido pelo Dataset RAGAS

Histórico agregado de scores em [`../ragas_scores.json`](../ragas_scores.json) (entry por execução, com timestamp e notas).

## Linha do tempo

### Fase 2 — gate antigo (Llama 3.3 70B + MiniLM 384D + dense, top_k=5)
**Seção 2.26 do diário técnico.**

| Arquivo | Conteúdo |
|---|---|
| `2026-04-06_fase2_gate_llama_minilm.cache.json` | 38 respostas Llama+MiniLM, gate final da Fase 2 |
| `2026-04-06_fase2_gate_llama_minilm.detailed.json` | mesmo, formato detailed |

**Métricas:** faithfulness 0.515, answer_relevancy 0.381, context_precision 0.735, context_recall 0.520.

---

### 2026-05-15/16 — Ablação 2×2 LLM × Embedding (Seção 2.32)

Quatro células (Llama vs GPT-4o) × (MiniLM 384D vs BGE-M3 1024D), todas com 38 questões e mesmo juiz `gpt-4o-mini`.

| Arquivo | Configuração |
|---|---|
| `2026-05-15_ablation_gpt4o_minilm.cache.json` | GPT-4o + MiniLM 384D (re-ablação correta após bug 2.31) |
| `2026-05-15_ablation_gpt4o_bgem3.cache.json` | GPT-4o + BGE-M3 1024D (controle estável para isolar embedding) |
| `2026-05-15_RETRACTED_gpt4o_was_llama.cache.json` | ⚠️ Run com cache erroneamente rotulado — env vars de sistema sobrescreveram .env, então rodou Llama mas foi salvo como gpt4o. Preservado como evidência do bug; **não usar para análise**. |
| `2026-05-15_partial_bgem3_llama_tpd.cache.json` | Llama+BGE-M3 parcial 13/38 (categorias fáceis ET/MO/IM-01); TPD Groq esgotou. Não usar isoladamente — subset enviesado. |
| `2026-05-16_gate_post_migration_llama_bgem3.cache.json` | Llama+BGE-M3 1024D 38/38 completo (após upgrade Groq Dev Tier) — gate intermediário pós-migração |

**Métricas-chave (38q completos):**
- Llama+MiniLM 384D: 0.515 / 0.381 / 0.735 / 0.520 (gate Fase 2)
- GPT-4o+MiniLM 384D: 0.383 / 0.315 / 0.761 / 0.533
- GPT-4o+BGE-M3 1024D: 0.600 / 0.618 / 0.907 / 0.796
- Llama+BGE-M3 1024D: 0.675 / 0.686 / 0.949 / 0.740 (gate pós-migração)

---

### 2026-05-16 — Iterações pós-recuperação (Seções 2.34, 2.35, 2.36)

Aplicadas sobre Llama 3.3 70B + BGE-M3 1024D, mesmas 38 questões.

| Arquivo | Configuração |
|---|---|
| `2026-05-16_hybrid_only.cache.json` | + busca híbrida BM25 + denso com RRF (k=60, fetch_k=20). TF2 isolado. |
| `2026-05-16_hybrid_rerank_GATE_FINAL.cache.json` | + reranker cross-encoder mGTE (`Alibaba-NLP/gte-multilingual-reranker-base`), top_k=5. **TF1+TF2 — gate operacional final do artefato.** |
| `2026-05-16_chunk500_test.cache.json` | TF B.4: chunk_size reduzido de 800→500 chars; não ajudou (faith virtualmente igual, ans_rel −5%). Pipeline permanece com chunk_size=800. |

**Métricas-chave:**
- Hybrid sem rerank: 0.689 / 0.737 / 0.912 / 0.826
- **Hybrid + Rerank (gate final): 0.761 / 0.720 / 0.964 / 0.803**
- chunk_size=500 (descartado): 0.756 / 0.683 / 0.951 / 0.811

## Trajetória da faithfulness

```
Gate Fase 2 (Llama+MiniLM)                       0.515
  ├─ migração BGE-M3 (2.32)                      0.675   (+0.160)
  │    └─ + hybrid BM25+RRF (2.34)               0.689   (+0.014)
  │         └─ + reranker mGTE (2.35)            0.761   (+0.072)  ← GATE FINAL
  │              └─ chunk_size=500 (2.36)        0.756   (-0.005, revertido)
  └─ ablação isolada GPT-4o (2.32)               0.383   (modelo prompt-adherent recusa mais)
```

Salto cumulativo gate Fase 2 → gate final: **+0.246 em faithfulness (+47.8%)**, com `context_precision` de 0.735 (FAIL marginal) para 0.964 (PASS robusto).
