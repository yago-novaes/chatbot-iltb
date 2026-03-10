# POC Chatbot ILTB

Prova de conceito do chatbot de suporte clínico para enfermeiros sobre **Infecção Latente pelo Mycobacterium tuberculosis (ILTB)**.

Arquitetura: **RAG (Retrieval-Augmented Generation)** sobre protocolos do Ministério da Saúde, com LLM via API.

---

## Arquitetura

```
Pergunta do enfermeiro
        │
        ▼
  [ FastAPI /chat ]
        │
        ▼
  [ Retriever ]  ──→  ChromaDB (embeddings locais sentence-transformers)
        │
        ▼
  [ Prompt Builder ]  (contexto + pergunta)
        │
        ▼
  [ LLM Client ]  ──→  Groq / OpenAI / Ollama
        │
        ▼
  Resposta fundamentada no protocolo
```

---

## Pré-requisitos

- Python 3.11+
- pip

---

## Instalação

```bash
# 1. Clone ou entre na pasta do projeto
cd poc-chatbot-iltb

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure o ambiente
cp .env.example .env
# Edite o .env com suas configurações (ver seção abaixo)
```

---

## Configuração do LLM

Edite o arquivo `.env`. Três opções:

### Opção A — Groq (gratuito, recomendado para a POC)

1. Cadastre-se em [console.groq.com](https://console.groq.com) (gratuito)
2. Gere uma API Key
3. Configure o `.env`:

```env
LLM_PROVIDER=groq
LLM_API_KEY=gsk_sua_chave_aqui
LLM_MODEL=llama-3.3-70b-versatile
LLM_BASE_URL=https://api.groq.com/openai/v1
```

### Opção B — OpenAI (pago)

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-sua_chave_aqui
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
```

### Opção C — Ollama (100% local, sem chave)

1. Instale o [Ollama](https://ollama.com)
2. Baixe um modelo: `ollama pull llama3.2`
3. Configure o `.env`:

```env
LLM_PROVIDER=ollama
LLM_API_KEY=ollama
LLM_MODEL=llama3.2
LLM_BASE_URL=http://localhost:11434/v1
```

### Modo Mock (sem nenhuma configuração)

Se não configurar nada, a API roda em **modo mock**: o RAG funciona normalmente (busca e recupera trechos), mas a geração de texto é simulada. Útil para validar o pipeline.

---

## Uso

### 1. Indexar os documentos

```bash
python scripts/ingest.py
```

Saída esperada:
```
Iniciando ingestão dos documentos...
✓ 42 chunks indexados com sucesso.
```

### 2. Iniciar a API

```bash
python -m src.main
```

A API estará disponível em `http://localhost:8000`.

Documentação interativa: `http://localhost:8000/docs`

---

## Endpoints

### `GET /health`
Verifica o status do serviço.

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

---

### `POST /ingest`
Indexa (ou re-indexa) os documentos da pasta `docs/`.

```bash
curl -X POST http://localhost:8000/ingest
```

```json
{
  "status": "success",
  "chunks_indexed": 42,
  "message": "42 chunks indexados com sucesso."
}
```

---

### `POST /chat`
Envia uma pergunta e recebe resposta baseada nos protocolos.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual é a dose de isoniazida para adultos no esquema 6H?"}'
```

```json
{
  "answer": "No esquema 6H, a dose de isoniazida para adultos é de 5-10 mg/kg/dia, com dose máxima de 300 mg/dia, administrada por via oral preferencialmente em jejum, durante 6 meses.",
  "sources": [
    {
      "source": "protocolo_iltb_exemplo.md",
      "score": 0.91,
      "excerpt": "### 4.1 Isoniazida (INH) — Esquema 6H (Padrão)\n- **Dose adultos:** 5-10 mg/kg/dia, máximo 300 mg/dia..."
    }
  ],
  "llm_provider": "groq",
  "llm_model": "llama-3.3-70b-versatile"
}
```

---

### `POST /search`
Busca trechos relevantes sem gerar resposta (útil para depurar o RAG).

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "efeitos adversos isoniazida", "top_k": 3}'
```

---

## Estrutura do Projeto

```
poc-chatbot-iltb/
├── docs/
│   └── protocolo_iltb_exemplo.md   # Documento de exemplo (substituir pelos reais)
├── scripts/
│   └── ingest.py                   # CLI para indexar documentos
├── src/
│   ├── config.py                   # Configurações via .env
│   ├── main.py                     # FastAPI app
│   ├── llm/
│   │   └── client.py               # Cliente LLM (Groq/OpenAI/Ollama/mock)
│   └── rag/
│       ├── ingestion.py            # Leitura, chunking e indexação
│       └── retriever.py            # Busca vetorial no ChromaDB
├── .env.example                    # Modelo de configuração
├── requirements.txt
└── README.md
```

---

## Adicionando Documentos Reais

Basta colocar arquivos `.md` ou `.txt` na pasta `docs/` e re-executar:

```bash
python scripts/ingest.py
```

Formatos PDF: converter para `.md` ou `.txt` antes (ex: usando `pymupdf` ou `pdfplumber`).

---

## Próximos Passos (roadmap da POC → produção)

- [ ] Integração com WhatsApp Business API (webhook Meta)
- [ ] Suporte a PDF direto na ingestão
- [ ] Histórico de conversa por usuário
- [ ] Logging de perguntas para análise (sem dados do paciente)
- [ ] Deploy no Hetzner CPX31 via Docker
- [ ] Autenticação básica na API
