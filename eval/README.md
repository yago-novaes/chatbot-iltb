# Avaliação do Pipeline RAG — Chatbot ILTB

Este diretório contém o conjunto de testes e scripts de avaliação do pipeline RAG.

## Pré-requisitos

- Collection indexada: `POST /ingest` ou `python -m app.scripts.ingest`
- LLM configurado: `LLM_PROVIDER=groq` e `LLM_API_KEY` válida no `.env`
- O modo mock **não funciona** para avaliação RAGAS (o RAGAS precisa de um LLM real como juiz)

## Arquivos

```
eval/
├── test_set.json          # Conjunto de perguntas e ground truths
├── run_ragas.py           # Script de avaliação — executa e salva métricas
├── results/
│   ├── ragas_scores.json      # Scores agregados (média por métrica)
│   └── ragas_detailed.json    # Scores por pergunta
└── README.md              # Este arquivo
```

## Test Set (`test_set.json`)

**Total:** 40 perguntas

**Distribuição por categoria:**

| Categoria | Qtd | Descrição |
|---|---|---|
| `esquemas_terapeuticos` | 7 | Doses, durações, escolha por perfil (3HP, 4R, 6H, 9H) |
| `monitoramento` | 5 | Frequência de consultas, critérios de suspensão, seguimento |
| `interacoes_medicamentosas` | 5 | Rifampicina + ARV, contraceptivos, isoniazida + fenitoína |
| `populacoes_especiais` | 7 | Gestantes, crianças, PVHIV, anti-TNF, hepatopatas |
| `diagnostico` | 5 | TT/IGRA pontos de corte, exclusão TB ativa, resultado indeterminado |
| `indicacoes_tratamento` | 5 | Elegibilidade, grupos prioritários, indicações sem PT/IGRA |
| `efeitos_adversos` | 4 | Hepatotoxicidade, neuropatia, piridoxina, encerramento |
| `fora_do_escopo` | 4 | TB ativa, pneumonia, COVID — esperam fallback, não resposta |

## Ground Truth

Os `ground_truth` foram extraídos **literalmente** dos `.md` gerados a partir dos PDFs reais do MS:
- `af_protocolo_vigilancia_iltb_2ed_9jun22_ok_web.md`
- `GEDIIB_TratamentoTuberculose.md`
- `tratamento_infeccao_latente_tuberculose_rifapentina_eletronico.md`
- `recomendacoes-para-o-controle-da-tuberculose.md`
- `9789275728185_por.md`

> **Importante:** Este test set deve ser revisado por enfermeira especialista em TB antes de ser usado como gate definitivo. O ground truth é uma extração do texto dos documentos, não uma validação clínica independente.

## Perguntas `fora_do_escopo`

As 4 perguntas na categoria `fora_do_escopo` têm `ground_truth: null`. O comportamento esperado é o **fallback** do sistema (resposta indicando que o assunto está fora do escopo dos protocolos de ILTB), não uma resposta clínica. Essas perguntas **não entram no cálculo das métricas RAGAS** — são usadas apenas para verificar se o sistema não alucina.

## Executar Avaliação

```bash
python -m eval.run_ragas
```

## Métricas e Alvos

| Métrica | Alvo | Descrição |
|---|---|---|
| Faithfulness | ≥ 0.80 | Resposta sustentada pelos chunks recuperados |
| Answer Relevancy | — | Resposta relevante para a pergunta |
| Context Precision | ≥ 0.75 | Chunks recuperados são relevantes para a pergunta |
| Context Recall | — | Chunks recuperados cobrem o ground truth |

Se Faithfulness < 0.80 ou Context Precision < 0.75, **não avançar para o piloto com enfermeiras** (gate do roadmap).
