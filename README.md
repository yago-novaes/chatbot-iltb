# Chatbot ILTB

Assistente clínico para enfermeiros sobre **Infecção Latente pelo Mycobacterium tuberculosis (ILTB)**, desenvolvido como TCC em Engenharia de Produção na UFES (defesa: junho/2026).

Arquitetura **RAG (Retrieval-Augmented Generation)** sobre 7 documentos do Ministério da Saúde e OMS, com embeddings locais e LLM via API.

**Status:** pipeline RAG funcional com avaliação RAGAS (baseline estabelecido). Próxima fase: re-indexação pós-sanitização + deploy piloto na Hetzner.

---

## Arquitetura

```
Pergunta do enfermeiro
        │
        ▼
  [ FastAPI /chat ]
        │
        ▼
  [ Retriever ]  ──→  ChromaDB  ←──  sentence-transformers (local, 384D)
        │              top_k=4, threshold=0.40
        ▼
  [ Prompt Builder ]  (contexto + pergunta)
        │
        ▼
  [ LLM Client ]  ──→  Groq / OpenAI / Ollama / Mock
        │
        ▼
  Resposta fundamentada nos protocolos
```

**Pipeline de ingestão (offline):**

```
docs/protocolos/*.pdf
        │
        ▼
  [ Docling → .md ]  ──→  sanitize_markdown() v3  (25 regras automáticas)
        │                        │
        │              revisão manual (3 docs higienizados manualmente)
        ▼
  [ split_by_sections() ]  (chunking semântico por cabeçalhos markdown)
        │
        ▼
  [ ChromaDB ]  (928 chunks — coleção iltb_protocols)
```

---

## Stack

| Componente | Tecnologia |
|---|---|
| Backend | FastAPI async + uvicorn |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (local, 384D, sem chave) |
| Vector store | ChromaDB (persistente, cosine similarity) |
| LLM produção | Groq `llama-3.3-70b-versatile` (free tier) |
| LLM juiz RAGAS | OpenAI `gpt-4o-mini` |
| Extração PDF | Docling (IBM, local, PDF → Markdown) |
| Avaliação | RAGAS 0.4 (faithfulness, answer_relevancy, context_precision, context_recall) |

---

## Base de Conhecimento

7 arquivos indexados (928 chunks):

| Documento | Fonte | Status |
|---|---|---|
| Manual de Recomendações para o Controle da TB no Brasil | Ministério da Saúde | 🔄 sanitização automática |
| Recomendações para o Controle da TB | Ministério da Saúde | 🔄 sanitização automática |
| Protocolo de Vigilância da ILTB (2ª ed.) | Ministério da Saúde | ✅ higienizado manualmente |
| GEDIIB — Tratamento da Tuberculose | GEDIIB | ✅ higienizado manualmente |
| Tratamento ILTB com Rifapentina | Ministério da Saúde | 🔄 sanitização automática |
| Manual Operacional OMS — Módulo 4 | OMS | ✅ higienizado manualmente |
| patch_interacoes_medicamentosas.md | MS (reconstruído) | ✅ patch manual |

> O patch foi necessário porque o Docling falhou na extração das tabelas de interações medicamentosas (seção 6.3 do Manual — páginas com alta complexidade visual).

---

## Avaliação (RAGAS)

40 perguntas clínicas (36 in-scope + 4 fora do escopo) cobrindo 7 categorias: esquemas terapêuticos, populações especiais, efeitos adversos, manejo odontológico, interações medicamentosas, diagnóstico e imunossuprimidos.

LLM produção: `llama-3.3-70b-versatile` (Groq). LLM juiz: `gpt-4o-mini` (OpenAI). 38 perguntas in-scope avaliadas.

| Métrica | Baseline (pré-sanitização) | Atual (pós-sanitização) | Alvo |
|---|---|---|---|
| faithfulness | 0.375 | **0.528** | ≥ 0.80 |
| context_precision | 0.548 | **0.619** | ≥ 0.75 |
| context_recall | 0.382 | **0.579** | — |
| answer_relevancy | 0.310 | **0.486** | — |

---

## Pré-requisitos

- Python 3.11+
- pip

---

## Instalação

```bash
git clone https://github.com/yago-novaes/chatbot-iltb.git
cd chatbot-iltb

python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

pip install -r app/requirements.txt

cp .env.example .env
# Edite o .env conforme a seção abaixo
```

---

## Configuração do LLM

### Opção A — Groq (gratuito, recomendado para desenvolvimento)

```env
LLM_PROVIDER=groq
LLM_API_KEY=gsk_sua_chave_aqui
LLM_MODEL=llama-3.3-70b-versatile
LLM_BASE_URL=https://api.groq.com/openai/v1
```

> **Atenção:** o free tier do Groq tem limite de 6k tokens/min e 100k tokens/dia. Para o pipeline RAGAS completo (40 perguntas), usar `SLEEP_BETWEEN_CALLS=15` no `.env` ou preferir OpenAI.

### Opção B — OpenAI

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-sua_chave_aqui
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
```

### Opção C — Ollama (100% local, sem chave)

```bash
ollama pull llama3.2
```

```env
LLM_PROVIDER=ollama
LLM_API_KEY=ollama
LLM_MODEL=llama3.2
LLM_BASE_URL=http://localhost:11434/v1
```

### Modo Mock (sem configuração)

Se `LLM_API_KEY` não estiver definida, a API roda em modo mock: o RAG funciona normalmente (busca e recupera trechos), mas a geração de texto é simulada.

---

## Uso

### 1. Indexar os documentos

```bash
python -m app.scripts.ingest
```

Chunkeia os `.md` em `docs/protocolos/` e indexa no ChromaDB. Re-executar re-indexa tudo.

### 2. Iniciar a API

```bash
python -m app.src.main
```

API disponível em `http://localhost:8000` — documentação interativa em `http://localhost:8000/docs`.

---

## Endpoints

### `GET /health`

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "collection_ready": true,
  "llm_provider": "groq",
  "llm_model": "llama-3.3-70b-versatile"
}
```

### `POST /chat`

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual a dose de isoniazida no esquema 6H para adultos?"}'
```

```json
{
  "answer": "No esquema 6H, a dose de isoniazida para adultos é 5–10 mg/kg/dia, máximo 300 mg/dia, via oral, preferencialmente em jejum, por 6 meses.",
  "sources": [
    {
      "source": "recomendacoes-para-o-controle-da-tuberculose.md",
      "score": 0.87,
      "excerpt": "..."
    }
  ],
  "llm_provider": "groq",
  "llm_model": "llama-3.3-70b-versatile"
}
```

### `POST /search`

Retorna chunks relevantes sem gerar resposta (útil para depurar o RAG):

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "efeitos adversos isoniazida", "top_k": 3}'
```

### `POST /ingest`

Re-indexa os documentos via HTTP (equivalente ao script CLI):

```bash
curl -X POST http://localhost:8000/ingest
```

---

## Avaliação RAGAS

```bash
# Requer RAGAS_LLM_API_KEY no .env (OpenAI recomendado como juiz)
python -m eval.run_ragas

# Apenas gerar respostas (sem avaliar)
python -m eval.run_ragas --pipeline-only

# Apenas avaliar respostas já geradas
python -m eval.run_ragas --scores-only

# Limitar número de perguntas
python -m eval.run_ragas --max-questions 10
```

> Com Groq free tier: definir `SLEEP_BETWEEN_CALLS=15` no `.env` para respeitar o limite de TPM.

---

## Estrutura do Projeto

```
chatbot-iltb/
├── app/
│   ├── requirements.txt
│   ├── scripts/
│   │   ├── extract_pdfs.py          # Extrai PDFs → .md via Docling + sanitize_markdown() v3
│   │   ├── sanitize_existing_md.py  # Aplica sanitize_markdown() nos .md já extraídos
│   │   └── ingest.py                # Indexa os .md no ChromaDB
│   └── src/
│       ├── config.py                # Settings via .env (pydantic-settings)
│       ├── main.py                  # FastAPI entrypoint
│       ├── api/routes/              # chat, health, ingest, search
│       ├── llm/
│       │   ├── client.py            # Cliente unificado (Groq/OpenAI/Ollama/mock)
│       │   └── prompts.py           # Templates de prompt clínico
│       ├── rag/
│       │   ├── embeddings.py        # sentence-transformers local
│       │   ├── retriever.py         # Busca vetorial no ChromaDB (top_k=4, threshold=0.40)
│       │   └── ingestion/
│       │       ├── chunker.py       # split_by_sections() — chunking por cabeçalhos markdown
│       │       ├── indexer.py       # Indexação no ChromaDB
│       │       └── pdf_extractor.py # Docling wrapper
│       └── session/
│           └── manager.py           # Histórico de conversa por sessão (TTL 30min)
├── docs/
│   ├── protocolos/                  # PDFs originais + .md higienizados (7 arquivos)
│   ├── audit_ingestion.md           # Relatório de auditoria de integridade dos .md
│   └── diario-tecnico.md            # Diário de engenharia (decisões, experimentos, lições)
├── eval/
│   ├── run_ragas.py                 # Pipeline de avaliação RAGAS
│   ├── test_set.json                # 40 perguntas clínicas com ground truths
│   └── results/                     # ragas_scores.json, ragas_detailed.json
├── infra/
│   ├── Dockerfile
│   ├── docker-compose.yml           # Bind 127.0.0.1:8000 — não expõe porta publicamente
│   └── nginx/
│       └── default.conf
├── poc/                             # Versão inicial da POC (referência histórica)
├── .env.example
└── README.md
```

---

## Roadmap

- [x] POC funcional (RAG + FastAPI + mock)
- [x] Ingestão dos 7 documentos reais do MS/OMS/GEDIIB
- [x] Pipeline de extração PDF → Markdown (Docling + `sanitize_markdown()` v3 — 25 regras)
- [x] Auditoria de integridade da base de conhecimento
- [x] Avaliação RAGAS — baseline (40 perguntas, `gpt-4o-mini` como juiz)
- [x] Re-indexação + re-avaliação RAGAS pós-sanitização completa
- [ ] Deploy piloto — Hetzner CPX31 via Docker
- [ ] Integração WhatsApp Business API (webhook Meta)
- [ ] Histórico de conversa persistido por usuário
- [ ] Logging de perguntas para análise (sem dados do paciente)
- [ ] Busca híbrida (dense + sparse) — Fase 5
