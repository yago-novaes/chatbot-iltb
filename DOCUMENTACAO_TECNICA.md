# Documentação Técnica — POC Chatbot ILTB

**Projeto:** Chatbot de Suporte Clínico para Enfermeiros — Infecção Latente pelo Mycobacterium tuberculosis (ILTB)
**Instituição:** UFES — Universidade Federal do Espírito Santo
**Status:** Prova de Conceito (POC) funcional

---

## 1. Visão Geral

### 1.1 Problema

Enfermeiros da atenção primária e secundária precisam consultar protocolos clínicos do Ministério da Saúde durante o atendimento de pacientes com ILTB. Esses protocolos são extensos, técnicos e estão em documentos PDF/texto densos, dificultando a consulta rápida.

### 1.2 Solução

Um chatbot conversacional que responde perguntas clínicas em linguagem natural, com respostas **fundamentadas exclusivamente nos protocolos oficiais do MS**, citando a fonte. O profissional pergunta como faria a um colega especialista; o sistema busca o trecho correto e formula uma resposta objetiva.

### 1.3 Premissas de Privacidade

- **Nenhum dado do paciente é enviado à API do LLM.** O chatbot recebe apenas perguntas técnicas sobre protocolos (doses, esquemas, condutas).
- Dados identificadores (nome, CPF, prontuário) **nunca fazem parte do fluxo**.
- Isso elimina a restrição de infraestrutura on-premise e viabiliza o uso de cloud.

---

## 2. Arquitetura

### 2.1 Padrão Arquitetural: RAG (Retrieval-Augmented Generation)

O RAG é um padrão que combina busca semântica com geração de linguagem natural. Em vez de depender da memória de treinamento do LLM (que pode alucinar), o sistema **recupera o trecho relevante do documento antes de gerar a resposta**.

```
┌─────────────────────────────────────────────────────┐
│                    FLUXO DE CHAT                    │
│                                                     │
│  Pergunta do enfermeiro                             │
│         │                                           │
│         ▼                                           │
│  [Embedding da pergunta]                            │
│  texto → vetor numérico (384 dimensões)             │
│         │                                           │
│         ▼                                           │
│  [Busca vetorial no ChromaDB]                       │
│  similaridade coseno → top-K chunks                 │
│         │                                           │
│         ▼                                           │
│  [Montagem do Prompt]                               │
│  system_prompt + contexto + pergunta                │
│         │                                           │
│         ▼                                           │
│  [LLM — Groq/Llama ou OpenAI]                       │
│  gera resposta baseada no contexto                  │
│         │                                           │
│         ▼                                           │
│  Resposta + fontes + scores                         │
└─────────────────────────────────────────────────────┘
```

### 2.2 Componentes

| Componente | Tecnologia | Papel |
|---|---|---|
| API REST | FastAPI (Python) | Orquestra o fluxo, expõe endpoints |
| Embedding | sentence-transformers (local) | Converte texto em vetores |
| Vector Store | ChromaDB (local) | Armazena e busca vetores |
| LLM | Groq (Llama 3.3 70B) / OpenAI | Gera a resposta final |
| Configuração | pydantic-settings + .env | Gerencia variáveis de ambiente |

### 2.3 Stack de Tecnologias

```
Python 3.11+
├── FastAPI 0.135+          — framework web/API
├── Uvicorn                 — servidor ASGI
├── Pydantic v2             — validação de dados e settings
├── ChromaDB 1.x            — banco vetorial persistente local
├── sentence-transformers   — modelo de embedding multilingual
│   └── paraphrase-multilingual-MiniLM-L12-v2
├── openai SDK              — cliente HTTP OpenAI-compatible
└── python-dotenv           — leitura do .env
```

---

## 3. Pipeline de Ingestão (Indexação)

### 3.1 O que é a Ingestão

A ingestão é o processo **offline** de preparar os documentos para busca. Deve ser executada uma vez ao adicionar ou atualizar documentos.

```bash
python scripts/ingest.py
```

### 3.2 Etapas do Pipeline

#### Etapa 1 — Leitura dos Documentos

- Lê todos os arquivos `.md` e `.txt` da pasta `docs/`
- Encoding: UTF-8 obrigatório
- Suporte atual: Markdown e texto plano
- Para adicionar PDFs: converter para `.md` ou `.txt` antes

```python
# src/rag/ingestion.py
files = list(folder.glob("*.md")) + list(folder.glob("*.txt"))
text = path.read_text(encoding="utf-8")
```

#### Etapa 2 — Chunking (Divisão em Trechos)

**Problema:** LLMs têm limite de tokens por prompt. Documentos inteiros não cabem no contexto. A solução é dividir em trechos menores (chunks) e enviar apenas os relevantes.

**Estratégia adotada: Chunking por Seções Markdown**

O texto é dividido nas linhas que começam com `#`, `##` ou `###` (cabeçalhos do markdown). Isso garante que cada chunk corresponde a uma **seção semântica coesa** do documento (ex: "4.1 Esquema 6H" fica inteiro no mesmo chunk).

```
# Protocolo ILTB          ← separador de chunk
## 1. Definição            ← separador de chunk
## 2. Indicações           ← separador de chunk
### 2.1 Contatos de Casos  ← separador de chunk
```

**Regras de agrupamento:**
- Seções pequenas são **agrupadas** até o limite de `CHUNK_SIZE` (padrão: 800 chars)
- Seções maiores que `CHUNK_SIZE` são **subdivididas por parágrafos**
- Parágrafos maiores que `CHUNK_SIZE` ficam como chunk único (caso raro)

**Por que não chunking por caracteres fixos?**

O chunking por tamanho fixo (ex: a cada 800 caracteres) corta no meio de seções, misturando conteúdo de contextos diferentes no mesmo chunk. Isso prejudica a qualidade do embedding e da busca. No teste inicial com chunking fixo, a dose do esquema 6H estava dividida entre dois chunks, fazendo o LLM responder com o fallback de "não encontrei a informação".

#### Etapa 3 — Geração de Embeddings

Cada chunk é convertido em um vetor numérico de 384 dimensões pelo modelo `paraphrase-multilingual-MiniLM-L12-v2`.

**Embedding** é uma representação matemática do significado semântico do texto. Textos com significado parecido geram vetores próximos no espaço vetorial, independentemente das palavras exatas usadas.

```
"dose isoniazida adultos"    → [0.12, -0.34, 0.87, 0.21, ...]
"quanto tomar de INH"        → [0.11, -0.31, 0.85, 0.19, ...]  ← próximos
"interação rifampicina"      → [0.95,  0.72, -0.21, 0.44, ...] ← distante
```

**Por que este modelo?**
- Multilingual: treinado em português e outras línguas
- Leve: roda em CPU sem GPU
- Sem API key: 100% local, zero custo
- Qualidade suficiente para domínio médico em PT-BR

#### Etapa 4 — Armazenamento no ChromaDB

Os chunks e seus vetores são armazenados no ChromaDB persistente (pasta `chroma_db/`).

```python
collection.add(
    ids=["protocolo_iltb_exemplo_0", "protocolo_iltb_exemplo_1", ...],
    documents=["### 4.1 Isoniazida...", "### 4.2 Isoniazida 9H...", ...],
    metadatas=[{"source": "protocolo_iltb_exemplo.md", "chunk": 0}, ...]
)
```

- **ids:** identificador único por chunk (`{nome_arquivo}_{índice}`)
- **documents:** texto original do chunk (recuperado na busca)
- **metadatas:** arquivo de origem e índice (para exibir a fonte na resposta)
- **Espaço métrico:** coseno (`hnsw:space: cosine`)

**Regra de re-indexação:** toda execução do ingest apaga e recria a collection. Isso garante consistência quando documentos são atualizados ou adicionados.

---

## 4. Pipeline de Recuperação (Retrieval)

### 4.1 Busca por Similaridade

Quando o usuário faz uma pergunta via `POST /chat`:

1. A pergunta é convertida em vetor pelo **mesmo modelo de embedding** usado na ingestão
2. O ChromaDB calcula a **similaridade coseno** entre o vetor da pergunta e todos os vetores armazenados
3. Retorna os `TOP_K_RESULTS` chunks com maior similaridade (padrão: 4)

**Similaridade coseno** mede o ângulo entre dois vetores (não a distância euclidiana). Varia de 0 a 1:
- **1.0** = vetores idênticos (mesmo significado)
- **0.7+** = alta relevância
- **0.5** = relevância moderada
- **< 0.3** = pouco relevante

```python
# src/rag/retriever.py
results = collection.query(
    query_texts=[query],
    n_results=top_k,
    include=["documents", "metadatas", "distances"],
)
score = round(1 - distance, 4)  # distância coseno → similaridade
```

### 4.2 Construção do Contexto

Os chunks recuperados são formatados em um bloco de contexto estruturado:

```
[Trecho 1 — protocolo_iltb_exemplo.md]
### 4.1 Isoniazida (INH) — Esquema 6H (Padrão)
- Dose adultos: 5-10 mg/kg/dia, máximo 300 mg/dia
...

---

[Trecho 2 — protocolo_iltb_exemplo.md]
### 4.2 Isoniazida por 9 meses — Esquema 9H
...
```

---

## 5. Geração de Resposta (LLM)

### 5.1 System Prompt

O comportamento do LLM é controlado pelo system prompt, que define regras rígidas:

```
Você é um assistente clínico especializado em ILTB, desenvolvido para apoiar
enfermeiros da atenção primária e secundária.

Suas respostas devem:
- Ser baseadas EXCLUSIVAMENTE no contexto fornecido (protocolos do MS)
- Ser objetivas, claras e em linguagem acessível para profissionais de saúde
- Indicar a fonte do trecho quando relevante
- Alertar quando a pergunta estiver fora do escopo dos protocolos disponíveis
- NUNCA inventar informações não presentes no contexto

Se o contexto não contiver informação suficiente para responder, diga:
"Não encontrei essa informação nos protocolos disponíveis."
```

**Regras críticas do system prompt:**
- **Exclusividade:** o LLM só pode usar o contexto injetado, não conhecimento próprio
- **Fallback explícito:** quando não encontrar, deve declarar isso ao invés de inventar
- **Citação de fonte:** encoraja o LLM a mencionar o trecho de origem
- **Tom profissional:** linguagem técnica mas acessível para enfermeiros

### 5.2 Montagem do Prompt Final

```
SYSTEM: [system prompt acima]

USER:
## Contexto dos Protocolos ILTB

[Trecho 1 — protocolo_iltb_exemplo.md]
{chunk_1}

---

[Trecho 2 — protocolo_iltb_exemplo.md]
{chunk_2}

## Pergunta

{pergunta_do_usuario}
```

### 5.3 Parâmetros do LLM

```python
client.chat.completions.create(
    model=settings.llm_model,
    messages=messages,
    temperature=0.1,   # baixo: respostas mais factuais, menos criativas
    max_tokens=1024,   # suficiente para respostas clínicas completas
)
```

**Temperature 0.1:** valor próximo de zero reduz aleatoriedade. O modelo tende a escolher as palavras mais prováveis, gerando respostas mais consistentes e reproduzíveis — importante para contexto clínico.

### 5.4 Providers Suportados

O cliente usa a interface OpenAI-compatible, permitindo trocar de provider apenas alterando variáveis de ambiente:

| Provider | Custo | Modelo padrão | Chave necessária |
|---|---|---|---|
| Groq | Gratuito (free tier) | llama-3.3-70b-versatile | Sim (groq.com) |
| OpenAI | Pago | gpt-4o-mini | Sim |
| Ollama | Gratuito (local) | llama3.2 | Não |
| Mock | Gratuito | — | Não |

**Modo Mock:** quando `LLM_PROVIDER=mock` ou sem chave configurada, o sistema retorna uma resposta simulada que inclui o contexto recuperado. Útil para validar o pipeline RAG sem custo.

---

## 6. API REST — Endpoints

### `GET /health`

Verifica o estado do serviço.

**Resposta:**
```json
{
  "status": "ok",
  "collection_ready": true,
  "llm_provider": "groq",
  "llm_model": "llama-3.3-70b-versatile"
}
```

**Uso:** monitoramento, verificar se os documentos foram indexados.

---

### `POST /ingest`

Indexa (ou re-indexa) todos os documentos da pasta `docs/`.

**Resposta:**
```json
{
  "status": "success",
  "chunks_indexed": 15,
  "message": "15 chunks indexados com sucesso."
}
```

**Regra:** apaga e recria toda a collection. Idempotente — pode ser chamado múltiplas vezes sem problema.

---

### `POST /chat`

Endpoint principal. Recebe uma pergunta e retorna resposta fundamentada + fontes.

**Request:**
```json
{
  "question": "Qual a dose de isoniazida para adultos no esquema 6H?",
  "top_k": 4
}
```

**Validações:**
- `question`: mínimo 5 caracteres
- `top_k`: entre 1 e 10 (padrão: 4)
- Retorna 409 se a collection não foi indexada

**Response:**
```json
{
  "answer": "A dose de isoniazida para adultos no esquema 6H é de 5-10 mg/kg/dia, com máximo de 300 mg/dia.",
  "sources": [
    {
      "source": "protocolo_iltb_exemplo.md",
      "score": 0.7303,
      "excerpt": "### 4.1 Isoniazida (INH) — Esquema 6H..."
    }
  ],
  "llm_provider": "groq",
  "llm_model": "llama-3.3-70b-versatile"
}
```

---

### `POST /search`

Busca trechos relevantes sem chamar o LLM. Útil para depurar a qualidade do RAG.

**Request:**
```json
{
  "query": "efeitos adversos isoniazida",
  "top_k": 3
}
```

**Uso:** verificar se os chunks corretos estão sendo recuperados, sem consumir tokens do LLM.

---

## 7. Estrutura de Arquivos

```
poc-chatbot-iltb/
│
├── docs/                              ← documentos indexados pelo RAG
│   └── protocolo_iltb_exemplo.md     ← protocolo ILTB de exemplo (MS)
│
├── src/
│   ├── __init__.py
│   ├── config.py                     ← settings via pydantic-settings
│   ├── main.py                       ← FastAPI app e endpoints
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingestion.py              ← leitura, chunking, indexação
│   │   └── retriever.py              ← busca vetorial, construção do contexto
│   │
│   └── llm/
│       ├── __init__.py
│       └── client.py                 ← cliente LLM + system prompt
│
├── scripts/
│   └── ingest.py                     ← CLI para indexar documentos
│
├── chroma_db/                        ← banco vetorial persistente (gerado)
│
├── .env                              ← configurações locais (não versionado)
├── .env.example                      ← modelo de configuração
├── .gitignore                        ← exclui .env, .venv, chroma_db, logs
├── requirements.txt                  ← dependências Python
└── README.md                         ← instruções de uso
```

---

## 8. Configuração (.env)

| Variável | Padrão | Descrição |
|---|---|---|
| `LLM_PROVIDER` | `mock` | Provider do LLM: `groq`, `openai`, `ollama`, `mock` |
| `LLM_API_KEY` | `mock` | Chave de API do provider |
| `LLM_MODEL` | `mock` | Nome do modelo (ex: `llama-3.3-70b-versatile`) |
| `LLM_BASE_URL` | `""` | URL base da API (Groq, Ollama, etc.) |
| `CHROMA_PATH` | `./chroma_db` | Pasta onde o ChromaDB persiste os dados |
| `DOCS_PATH` | `./docs` | Pasta com os documentos a indexar |
| `CHUNK_SIZE` | `800` | Tamanho máximo de cada chunk (em caracteres) |
| `CHUNK_OVERLAP` | `100` | Sobreposição entre chunks (não usado no chunking por seção) |
| `TOP_K_RESULTS` | `4` | Número de chunks recuperados por pergunta |
| `API_HOST` | `0.0.0.0` | Host do servidor |
| `API_PORT` | `8000` | Porta do servidor |

---

## 9. Decisões de Design

### 9.1 ChromaDB vs outros vector stores

| Opção | Vantagem | Desvantagem |
|---|---|---|
| **ChromaDB** (adotado) | Zero infraestrutura, persistência local, API simples | Não escala para milhões de vetores |
| Pinecone | Escala, managed | Pago, dados na nuvem |
| pgvector | Integrado ao Postgres | Requer Postgres, mais complexo |
| FAISS | Muito rápido | Sem persistência nativa, sem metadados |

Para a POC com ~15-100 chunks, ChromaDB é ideal.

### 9.2 sentence-transformers local vs OpenAI Embeddings

Embeddings locais foram escolhidos para:
- **Zero custo:** não consome tokens de embedding
- **Zero latência de rede:** roda na mesma máquina
- **Privacidade:** os documentos não saem da máquina
- **Modelo multilingual:** suporta português nativamente

O modelo `paraphrase-multilingual-MiniLM-L12-v2` tem boa performance para português com apenas 120MB de tamanho.

### 9.3 Chunking por seção vs tamanho fixo

Chunking por tamanho fixo foi descartado após teste: a dose do esquema 6H ficou dividida entre dois chunks (parte do cabeçalho `### 4.1` e parte dos campos de dose em chunks diferentes), fazendo o sistema não recuperar a informação correta.

O chunking por seção markdown garante que cada seção clínica (esquema terapêutico, efeito adverso, indicação) fique **inteira e coesa** em um único chunk.

### 9.4 Temperature 0.1 no LLM

Valores baixos de temperature reduzem a criatividade do modelo em favor de respostas factuais. Em contexto clínico, consistência é mais importante que variedade nas respostas.

---

## 10. Limitações da POC

| Limitação | Impacto | Solução futura |
|---|---|---|
| Sem histórico de conversa | Cada pergunta é independente | Adicionar session_id + memória de conversa |
| Suporte apenas a .md e .txt | PDFs do MS precisam ser convertidos | Adicionar pdfplumber ou pymupdf |
| Sem autenticação | API aberta | Adicionar API key ou JWT |
| ChromaDB local | Não escala para múltiplos servidores | Migrar para ChromaDB server mode ou pgvector |
| Sem interface WhatsApp | Teste via HTTP apenas | Integrar webhook Meta Business API |
| Sem logging estruturado | Difícil auditoria | Adicionar registro de perguntas (sem PII) |

---

## 11. Roadmap para Produção

```
POC (atual)
  ├── RAG funcional com protocolos de exemplo
  ├── API REST com 4 endpoints
  └── LLM via Groq (free tier)

Fase 1 — Piloto interno (próximos passos)
  ├── Substituir docs de exemplo pelos PDFs reais do MS
  ├── Integrar WhatsApp Business API (webhook Meta)
  ├── Adicionar histórico de conversa por sessão
  └── Deploy no Hetzner CPX31 via Docker

Fase 2 — Piloto com enfermeiras
  ├── Autenticação básica
  ├── Logging de perguntas para análise (sem PII)
  ├── Monitoramento de custos (tokens consumidos)
  └── Mecanismo de feedback das enfermeiras

Fase 3 — Produção
  ├── Migrar para gpt-4o-mini (OpenAI) — R$8,71/mês
  ├── Suporte a múltiplos documentos simultâneos
  └── Dashboard de uso e qualidade das respostas
```

---

## 12. Estimativa de Custos (Produção)

Baseado na arquitetura do relatório técnico:

| Item | Custo/mês |
|---|---|
| Hetzner CPX31 (4vCPU, 8GB RAM) | R$ 122,69 |
| OpenAI gpt-4o-mini (2.200 req/mês) | R$ 8,71 |
| WhatsApp Business API (service conversations) | R$ 0,00 |
| **Total** | **R$ 131,40** |

Com orçamento de R$ 8.000: **~60 meses de sustentabilidade**.
