# Chatbot ILTB

Assistente clínico para enfermeiros sobre Infecção Latente pelo Mycobacterium tuberculosis (ILTB), feito como TCC em Engenharia de Produção na UFES (defesa em junho de 2026).

É um RAG sobre 7 documentos do Ministério da Saúde e da OMS, com embeddings rodando local e o LLM via API.

O pipeline está funcional e avaliado com RAGAS. A fase seguinte é a re-indexação pós-sanitização e o deploy do piloto.

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

Pipeline de ingestão, rodado offline:

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
  [ ChromaDB ]  (928 chunks na coleção iltb_protocols)
```

## Stack

| Componente | Tecnologia |
|---|---|
| Backend | FastAPI async + uvicorn |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (local, 384D, sem chave) |
| Vector store | ChromaDB (persistente, cosine similarity) |
| LLM produção | Groq `llama-3.3-70b-versatile` (free tier) |
| LLM juiz RAGAS | OpenAI `gpt-4o-mini` |
| Extração PDF | Docling (IBM, local, PDF para Markdown) |
| Avaliação | RAGAS 0.4 (faithfulness, answer_relevancy, context_precision, context_recall) |

## Base de conhecimento

7 arquivos indexados, 928 chunks:

| Documento | Fonte | Sanitização |
|---|---|---|
| Manual de Recomendações para o Controle da TB no Brasil | Ministério da Saúde | automática |
| Recomendações para o Controle da TB | Ministério da Saúde | automática |
| Protocolo de Vigilância da ILTB (2ª ed.) | Ministério da Saúde | manual |
| GEDIIB, Tratamento da Tuberculose | GEDIIB | manual |
| Tratamento ILTB com Rifapentina | Ministério da Saúde | automática |
| Manual Operacional OMS, Módulo 4 | OMS | manual |
| patch_interacoes_medicamentosas.md | MS (reconstruído) | patch manual |

O patch existe porque o Docling não deu conta das tabelas de interações medicamentosas da seção 6.3 do Manual, que têm layout visual pesado demais.

## Avaliação (RAGAS)

40 perguntas clínicas, sendo 36 dentro do escopo e 4 fora, cobrindo 7 categorias: esquemas terapêuticos, populações especiais, efeitos adversos, manejo odontológico, interações medicamentosas, diagnóstico e imunossuprimidos.

LLM de produção `llama-3.3-70b-versatile` no Groq, juiz `gpt-4o-mini` na OpenAI, 38 perguntas in-scope avaliadas.

| Métrica | Baseline (pré-sanitização) | Atual (pós-sanitização) | Alvo |
|---|---|---|---|
| faithfulness | 0.375 | 0.528 | ≥ 0.80 |
| context_precision | 0.548 | 0.619 | ≥ 0.75 |
| context_recall | 0.382 | 0.579 | n/a |
| answer_relevancy | 0.310 | 0.486 | n/a |

## Pré-requisitos

Python 3.11 ou superior, e pip.

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

## Configuração do LLM

### Opção A: Groq, gratuito e o que uso no dia a dia

```env
LLM_PROVIDER=groq
LLM_API_KEY=gsk_sua_chave_aqui
LLM_MODEL=llama-3.3-70b-versatile
LLM_BASE_URL=https://api.groq.com/openai/v1
```

O free tier do Groq trava em 6k tokens/min e 100k tokens/dia. Para rodar o RAGAS completo nas 40 perguntas sem esbarrar nisso, defina `SLEEP_BETWEEN_CALLS=15` no `.env`, ou use a OpenAI.

### Opção B: OpenAI

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-sua_chave_aqui
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
```

### Opção C: Ollama, local e sem chave

```bash
ollama pull llama3.2
```

```env
LLM_PROVIDER=ollama
LLM_API_KEY=ollama
LLM_MODEL=llama3.2
LLM_BASE_URL=http://localhost:11434/v1
```

### Modo mock

Sem `LLM_API_KEY` definida a API sobe em modo mock. O RAG funciona igual, busca e recupera os trechos normalmente, mas a geração de texto é simulada.

## Uso

### 1. Indexar os documentos

```bash
python -m app.scripts.ingest
```

Chunkeia os `.md` de `docs/protocolos/` e indexa no ChromaDB. Rodar de novo reindexa tudo do zero.

### 2. Iniciar a API

```bash
python -m app.src.main
```

API em `http://localhost:8000`, com a documentação interativa em `/docs`.

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

Retorna os chunks recuperados sem chamar o LLM. É o endpoint que uso para depurar o RAG:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "efeitos adversos isoniazida", "top_k": 3}'
```

### `POST /ingest`

Mesma coisa que o script de ingestão, mas via HTTP:

```bash
curl -X POST http://localhost:8000/ingest
```

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

No free tier do Groq, defina `SLEEP_BETWEEN_CALLS=15` no `.env` para não estourar o TPM.

## Estrutura do projeto

```
chatbot-iltb/
├── app/
│   ├── requirements.txt
│   ├── scripts/
│   │   ├── extract_pdfs.py          # PDF para .md via Docling + sanitize_markdown() v3
│   │   ├── sanitize_existing_md.py  # roda sanitize_markdown() nos .md já extraídos
│   │   └── ingest.py                # indexa os .md no ChromaDB
│   └── src/
│       ├── config.py                # settings via .env (pydantic-settings)
│       ├── main.py                  # entrypoint FastAPI
│       ├── api/routes/              # chat, health, ingest, search
│       ├── llm/
│       │   ├── client.py            # Groq, OpenAI, Ollama e mock
│       │   └── prompts.py           # prompts clínicos e o histórico de versões
│       ├── rag/
│       │   ├── embeddings.py        # sentence-transformers local
│       │   ├── retriever.py         # busca no ChromaDB (top_k=4, threshold=0.40)
│       │   └── ingestion/
│       │       ├── chunker.py       # split_by_sections(), corta por cabeçalho markdown
│       │       ├── indexer.py       # indexação no ChromaDB
│       │       └── pdf_extractor.py # wrapper do Docling
│       └── session/
│           └── manager.py           # histórico por sessão, TTL de 30min
├── docs/
│   ├── protocolos/                  # PDFs originais e os .md higienizados
│   ├── audit_ingestion.md           # auditoria de integridade dos .md
│   └── diario-tecnico.md            # diário de engenharia: decisões e experimentos
├── eval/
│   ├── run_ragas.py                 # pipeline de avaliação
│   ├── test_set.json                # 40 perguntas clínicas com ground truth
│   └── results/                     # ragas_scores.json, ragas_detailed.json
├── infra/
│   ├── Dockerfile
│   ├── docker-compose.yml           # bind em 127.0.0.1:8000, não expõe a porta
│   └── nginx/
│       └── default.conf
├── poc/                             # POC inicial, mantida como referência
├── .env.example
└── README.md
```

## Roadmap

- [x] POC funcional com RAG, FastAPI e mock
- [x] Ingestão dos 7 documentos do MS, OMS e GEDIIB
- [x] Extração PDF para Markdown com Docling e as 25 regras do `sanitize_markdown()` v3
- [x] Auditoria de integridade da base de conhecimento
- [x] Baseline RAGAS nas 40 perguntas, com `gpt-4o-mini` de juiz
- [x] Re-indexação e re-avaliação depois da sanitização completa
- [x] Busca híbrida BM25 mais denso, com reranker cross-encoder
- [ ] Deploy do piloto em Docker
- [ ] Integração com a WhatsApp Business API
- [ ] Histórico de conversa persistido por usuário
- [ ] Logging das perguntas para análise, sem dado de paciente
