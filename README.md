# Chatbot ILTB — POC

Chatbot de suporte clínico para enfermeiros sobre **Infecção Latente pelo Mycobacterium tuberculosis (ILTB)**, desenvolvido como TCC na UFES.

Arquitetura: **RAG (Retrieval-Augmented Generation)** sobre 6 protocolos do Ministério da Saúde e OMS, com embeddings locais e LLM via API.

**Status:** POC funcional com avaliação RAGAS completa (38 perguntas, 4 métricas). Próxima fase: piloto com 5 enfermeiras na Hetzner.

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
        │
        ▼
  [ Prompt Builder ]  (contexto + pergunta)
        │
        ▼
  [ LLM Client ]  ──→  Groq / OpenAI / Ollama / Mock
        │
        ▼
  Resposta fundamentada nos protocolos
```

**Pipeline de ingestão:**

```
PDFs (docs/protocolos/)
        │
        ▼
  [ Docling → .md ]  ──→  sanitize_markdown() v3  (25 regras — Camada 1 automática)
        │                        │
        │              revisão manual (Camada 2 — 3 docs higienizados)
        ▼
  [ Chunker semântico ]  (por cabeçalhos markdown)
        │
        ▼
  [ ChromaDB ]  (persistido em chroma_db/)
```

> `sanitize_markdown()` cobre: artefatos OCR, hifenização quebrada, bullets malformados, citações, bibliography aglutinada, URLs/emails fragmentados, cabeçalhos repetidos em caps. Ver `app/scripts/extract_pdfs.py`.

---

## Base de Conhecimento

6 documentos indexados:

| Documento | Fonte | Escopo |
|---|---|---|
| Manual de Recomendações para o Controle da TB no Brasil | Ministério da Saúde | Protocolo clínico completo |
| Recomendações para o Controle da TB | Ministério da Saúde | ILTB — atenção básica |
| Protocolo de Vigilância da ILTB (2ª ed.) | Ministério da Saúde | Diagnóstico e vigilância ILTB |
| GEDIIB — Tratamento da Tuberculose | GEDIIB | Especialidades / gastroenterologia |
| Tratamento ILTB com Rifapentina | Ministério da Saúde | Esquema 3HP |
| Manual Operacional OMS Módulo 4 | OMS | Atenção e apoio ao tratamento |

---

## Avaliação (RAGAS)

38 perguntas clínicas cobrindo 7 categorias: esquemas terapêuticos (ET), populações especiais (PE), efeitos adversos (EA), manejo odontológico (MO), interações medicamentosas (IM), diagnóstico (DI) e imunossuprimidos (IT).

| Métrica | Score |
|---|---|
| context_precision | 0.55 |
| faithfulness | 0.38 |
| context_recall | 0.38 |
| answer_relevancy | 0.31 |

LLM juiz: `gpt-4o-mini`. Scores pré-sanitização completa dos `.md`; nova rodada planejada após re-indexação.

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

1. Crie uma conta em [console.groq.com](https://console.groq.com)
2. Gere uma API Key
3. Configure o `.env`:

```env
LLM_PROVIDER=groq
LLM_API_KEY=gsk_sua_chave_aqui
LLM_MODEL=llama-3.3-70b-versatile
LLM_BASE_URL=https://api.groq.com/openai/v1
```

> **Atenção:** o free tier do Groq tem limite de 100k tokens/dia (70B) e 6k tokens/min. Para o pipeline RAGAS completo (38 perguntas), usar OpenAI.

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

Os `.md` em `docs/protocolos/` são chunkados e indexados no ChromaDB. Re-executar re-indexa tudo.

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

## Estrutura do Projeto

```
chatbot-iltb/
├── app/
│   ├── requirements.txt
│   ├── scripts/
│   │   ├── extract_pdfs.py          # Extrai PDFs → .md via Docling + sanitize_markdown()
│   │   ├── ingest.py                # Indexa os .md no ChromaDB
│   │   └── sanitize_existing_md.py  # Aplica sanitize_markdown() nos .md existentes
│   └── src/
│       ├── config.py                # Configurações via .env (pydantic-settings)
│       ├── main.py                  # FastAPI entrypoint
│       ├── api/routes/              # chat, health, ingest, search
│       ├── llm/
│       │   ├── client.py            # Cliente unificado (Groq/OpenAI/Ollama/mock)
│       │   └── prompts.py           # Templates de prompt clínico
│       ├── rag/
│       │   ├── embeddings.py        # sentence-transformers local
│       │   ├── retriever.py         # Busca vetorial no ChromaDB
│       │   └── ingestion/
│       │       ├── chunker.py       # Chunking semântico por cabeçalhos
│       │       ├── indexer.py       # Indexação no ChromaDB
│       │       └── pdf_extractor.py # Docling wrapper
│       └── session/
│           └── manager.py           # Histórico de conversa por sessão
├── docs/
│   ├── protocolos/                  # PDFs + .md higienizados (6 documentos)
│   ├── audit_ingestion.md           # Relatório de auditoria de integridade dos .md
│   └── diario-tecnico.md            # Diário de engenharia (decisões, experimentos, lições)
├── eval/
│   ├── run_ragas.py                 # Pipeline de avaliação RAGAS
│   ├── test_set.json                # 38 perguntas clínicas com ground truths
│   └── results/                     # Scores e detalhamento por pergunta
├── infra/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx/
├── poc/                             # Versão inicial da POC (referência histórica)
├── .env.example
└── README.md
```

---

## Avaliação RAGAS

```bash
# Requer RAGAS_LLM_API_KEY no .env (OpenAI recomendado)
python -m eval.run_ragas

# Apenas gerar respostas (sem avaliar)
python -m eval.run_ragas --pipeline-only

# Apenas avaliar respostas já geradas
python -m eval.run_ragas --scores-only
```

> Com Groq free tier: usar `SLEEP_BETWEEN_CALLS=15` no `.env` e aguardar reset do TPD (100k tokens/dia) entre runs.

---

## Roadmap

- [x] POC funcional (RAG + FastAPI + mock)
- [x] Ingestão dos 6 protocolos reais do MS/OMS
- [x] Pipeline de extração PDF → Markdown (Docling + sanitize_markdown)
- [x] sanitize_markdown() v3 — 25 regras + corpus sanitizado (3 docs manuais + 3 automáticos)
- [x] Auditoria de integridade da base de conhecimento
- [x] Avaliação RAGAS com gpt-4o-mini (38 perguntas, baseline pré-sanitização)
- [ ] Re-avaliação RAGAS pós-sanitização completa dos .md
- [ ] Deploy piloto — Hetzner CPX31 via Docker
- [ ] Integração WhatsApp Business API (webhook Meta)
- [ ] Histórico de conversa persistido por usuário
- [ ] Logging de perguntas para análise (sem dados do paciente)
- [ ] Busca híbrida (dense + sparse) com Qdrant — Fase 5
