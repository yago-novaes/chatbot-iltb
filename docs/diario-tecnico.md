# Diário Técnico — Chatbot ILTB

> Registro cronológico das decisões de engenharia, experimentos, erros e aprendizados ao longo do desenvolvimento. Destinado ao TCC.

---

## Convenções

| Ícone | Significado |
|---|---|
| ✅ | Funcionou — decisão mantida |
| ❌ | Não funcionou — descartado ou substituído |
| ⚠️ | Funciona parcialmente / tem ressalva |
| 🔄 | Em andamento |
| 📌 | Decisão de design (trade-off explícito) |

---

## FASE 1 — POC (Prova de Conceito)

**Objetivo:** Validar se RAG com embeddings locais + LLM externo consegue responder perguntas clínicas sobre ILTB dentro do escopo dos protocolos do MS, sem alucinação.

**Período:** início do projeto até commit `99dbb3d` (validação com 12 perguntas).

---

### 1.1 Decisões de Tecnologia

#### Embedding model: `paraphrase-multilingual-MiniLM-L12-v2` ✅

**Motivação:** modelo multilíngue, gratuito, roda 100% local sem chave de API. ~120 MB. Produz vetores de 384 dimensões.

**Alternativas consideradas:**
- `text-embedding-3-small` (OpenAI) — pago, dependência de API externa, risco de LGPD em contexto hospitalar
- `bert-base-portuguese-cased` — apenas português, menor cobertura terminológica clínica inglês/espanhol presente nos PDFs do MS

**Resultado:** funcionou bem para português técnico clínico. Scores de similaridade entre 0.69–0.87 nas perguntas validadas.

---

#### Vector store: ChromaDB ✅

**Motivação:** embutido em processo (sem servidor separado), persiste em disco, integração nativa com sentence-transformers, gratuito e open-source.

**Alternativas consideradas:**
- Qdrant — melhor para busca híbrida (dense + sparse), mas exige servidor Docker separado; planejado para produção (Fase 5)
- FAISS — sem persistência nativa, requires serialização manual
- Pinecone — pago, dependência de nuvem

**Resultado:** adequado para POC e piloto. Limitação identificada: sem suporte a busca por palavra-chave (sparse). Decisão: migrar para busca híbrida apenas em produção (Fase 5).

---

#### LLM: Groq free tier (`llama-3.3-70b-versatile`) ✅ para POC/piloto

**Motivação:** gratuito, latência ~1 s (inferência em hardware dedicado), API compatível com OpenAI SDK.

**Alternativas consideradas:**
- Ollama local (`llama3`, `mistral`) — zero custo, mas exige ~8 GB RAM/VRAM; CX22 do piloto tem 4 GB RAM apenas
- GPT-4o-mini — ~$0,002/1k tokens de saída; custo estimado R$8,71/mês para 2.200 req/mês — planejado para produção
- Claude Haiku — alternativa viável, mas aumentaria dependência de fornecedor único

**Resultado:** Groq é a escolha certa para POC e piloto. Risco: free tier tem rate limit (6.000 req/min, ~30 req/min por IP) — adequado para 5 enfermeiras em piloto.

---

#### Chunking: por seções markdown (cabeçalhos `##`/`###`) ✅

**Motivação:** documentos do MS são organizados em seções numeradas (3.1, 3.2…). Chunking por tamanho fixo quebrava seções clínicas no meio, separando dose de indicação.

**Experimento descartado:** chunking por tamanho fixo de 512 tokens com overlap de 50 tokens.

**Problema identificado:** uma seção como `## 3.3 Esquemas terapêuticos` continha dose + contraindicação + monitoramento. Com tamanho fixo, a dose ficava num chunk e a contraindicação em outro — o retriever retornava chunks incompletos.

**Solução implementada:** `split_by_sections()` em [chunker.py](../app/src/rag/ingestion/chunker.py):
1. Divide por cabeçalhos `#`, `##`, `###`
2. Agrupa seções pequenas (< `chunk_size`) em buffer único
3. Subdivide seções grandes por parágrafos

**Resultado:** chunks semanticamente coerentes. Seções clínicas críticas (esquemas de dose, critérios de elegibilidade) preservadas integralmente.

---

### 1.2 Validação — 12 Perguntas Clínicas

**Metodologia:** 12 perguntas formuladas com auxílio de enfermeira especialista em TB. Avaliação manual: resposta correta, fonte citada, sem alucinação.

**Resultados:**
- 12/12 respondidas dentro do escopo dos protocolos
- 0 alucinações identificadas (LLM não inventou doses ou critérios)
- Scores de similaridade: mín. 0.69, máx. 0.87, média ~0.76
- Tempo médio de resposta: ~2 s (embedding local + Groq)

**Limitação identificada:** perguntas que exigem raciocínio multi-documento (ex.: "quais são as contraindicações da rifapentina em gestantes com coinfecção HIV?") às vezes retornavam apenas um dos documentos relevantes. Causa: retriever retorna top-k chunks do documento mais similar, não necessariamente cobre todos os documentos.

**Decisão:** aumentar `top_k` default de 3 para 4. Investigar busca híbrida em produção.

---

### 1.3 O que NÃO funcionou na POC

#### ❌ Extração de PDF com PyMuPDF (`fitz`)

**Tentativa:** `fitz.open(pdf).get_text("text")` para extrair texto plano.

**Problema:** PDFs do MS são escaneados ou têm layout complexo em múltiplas colunas. O PyMuPDF retornava texto em ordem de leitura do PDF (coluna por coluna), não em ordem lógica do documento. Tabelas de doses saíam como sequência de números sem contexto.

**Exemplo de falha:**
```
# Output PyMuPDF (fragmento real):
"300 mg 4 meses 900 mg 4 meses 300 mg"
# Sem indicação de qual campo é qual coluna da tabela
```

**Decisão:** substituir por Docling (ver Fase 2).

#### ❌ Chunking por overlap fixo com LangChain `RecursiveCharacterTextSplitter`

**Tentativa:** `chunk_size=512, chunk_overlap=50`.

**Problema:** overlap criava chunks redundantes. O retriever retornava 2–3 chunks muito similares (um era a sobreposição do outro), desperdiçando o `top_k` com conteúdo duplicado.

**Decisão:** chunk sem overlap, por limite semântico (cabeçalho). Chunks distintos por definição.

---

## FASE 2 — Engenharia de Dados

**Objetivo:** substituir extração de texto placeholder por pipeline robusto com PDFs reais do MS. Validar qualidade dos chunks antes de avançar ao backend.

**Commits:** `f08bbcf` (Docling), estrutura de `app/` a partir de `76e3e19`.

---

### 2.1 Reestruturação: POC → Estrutura de Produção

**Motivação:** a POC tinha tudo em `src/` flat na raiz. Para o piloto ser implantável, precisava de:
- Separação entre código de produção (`app/`) e código experimental (`poc/`)
- Container Docker reproducível
- Configuração via variáveis de ambiente (não hardcoded)

**O que foi feito:**
- `git mv` de todo o código POC para `poc/` (histórico preservado)
- Scaffold de `app/src/` com módulos separados: `api/`, `rag/`, `llm/`, `session/`
- `pydantic-settings` para config centralizado em [config.py](../app/src/config.py)
- Dockerfile multi-stage em [infra/Dockerfile](../infra/Dockerfile)

**Decisão de design 📌:** manter POC e produção no mesmo repositório (não criar novo repo). Motivo: TCC — manter histórico completo da evolução para defesa.

---

### 2.2 Extração de PDF com Docling ✅

**Motivação:** PyMuPDF falhou em PDFs com layout complexo (ver 1.3). Docling (IBM, open-source) converte PDF → Markdown estruturado, preservando hierarquia de títulos e tabelas.

**Instalação:** `pip install docling` → v2.80.0 (~2 GB de modelos de ML baixados: layout detection, table recognition, OCR via RapidOCR/ONNX).

**Implementação:** [pdf_extractor.py](../app/src/rag/ingestion/pdf_extractor.py)
```python
from docling.document_converter import DocumentConverter
result = converter.convert(str(pdf_path))
return result.document.export_to_markdown()
```

**Por que Docling e não LlamaParse (que estava no roadmap original)?**
- LlamaParse: pago ($3/1.000 páginas), envia o PDF para servidor externo — risco de LGPD mesmo com documentos públicos
- Docling: gratuito, 100% local, modelos ONNX otimizados, output Markdown compatível com chunker existente

#### ⚠️ Problema encontrado: `std::bad_alloc` em páginas com imagens grandes

**Sintoma:** durante o ingest dos 6 PDFs do MS, Docling logou centenas de linhas:
```
Stage preprocess failed for run 3, pages [74]: std::bad_alloc
Stage layout failed for run 3: Unable to allocate 9.38 MiB for an array...
```

**Causa:** Docling usa modelos de visão computacional (RT-DETR para layout, ONNX para OCR) que renderizam cada página como imagem 640×640 float64. Com PDFs de 300+ páginas sendo processados em sequência, a RAM do Windows foi esgotada (~16 GB em uso).

**Por que não falhou fatalmente?** Docling tem fallback: quando a extração visual falha, usa extração de texto nativo do PDF (camada de texto do PDF). Documentos do MS têm texto nativo (não são 100% scans), então o fallback funciona.

**Resultado final:** 820 chunks indexados com sucesso dos 6 PDFs. Qualidade dos chunks verificada via query de teste:
```
Query: "quais são as indicações de tratamento da ILTB?"
→ af_protocolo_vigilancia_iltb_2ed_9jun22_ok_web.pdf (score: 0.869)
→ conteúdo: "## 3.5 Monitoramento e avaliação do tratamento da ILTB"
```

**Mitigação planejada para VPS:** na CX22 (4 GB RAM), o `std::bad_alloc` será mais frequente. Opções:
1. Pré-processar os PDFs localmente e commitar apenas os `.md` extraídos no repositório
2. Configurar `DOCLING_NUM_THREADS=1` para reduzir uso de memória paralela
3. Aceitar o fallback para texto nativo (qualidade suficiente para documentos do MS)

**Decisão atual:** opção 1 é a mais robusta para o piloto — rodar Docling uma vez localmente, commitar os `.md`, VPS só faz chunking + indexação.

---

### 2.3 Estrutura de Módulos da Ingestão

```
app/src/rag/ingestion/
├── __init__.py
├── chunker.py        # split_by_sections() — puro, sem I/O
├── indexer.py        # orquestra: lê arquivos → chunker → ChromaDB
└── pdf_extractor.py  # Docling: PDF → Markdown
```

**Decisão de design 📌:** separar `pdf_extractor` de `indexer`. Motivo: permite testar extração independentemente, e facilita substituição do extrator (ex.: trocar Docling por outra lib) sem tocar no indexer.

---

## FASE 3 — Backend FastAPI

**Commits:** `2fac16f` (async), `76e3e19` (scaffold inicial).

---

### 3.1 FastAPI — Rotas Assíncronas ✅

**Problema identificado:** rotas originais eram `def` síncronas. Em FastAPI, `def` roda em thread pool do uvicorn — correto para funções simples. Mas ao escalar para múltiplos usuários simultâneos (5 enfermeiras + possível carga), uma requisição de RAG (ChromaDB + Groq ~2s) bloquearia threads.

**Correção implementada:**

| Componente | Antes | Depois | Motivo |
|---|---|---|---|
| Rotas FastAPI | `def chat()` | `async def chat()` | libera event loop |
| ChromaDB calls | direto | `await asyncio.to_thread(retrieve, ...)` | ChromaDB é síncrono; `to_thread` roda em thread pool sem bloquear event loop |
| LLM call | `openai.ChatCompletion.create()` | `await AsyncOpenAI().chat.completions.create()` | I/O nativo async |

**Anti-padrão evitado:** simplesmente mudar `def` para `async def` sem tratar as chamadas bloqueantes seria pior que deixar síncrono — bloquearia o event loop inteiro.

---

### 3.2 Endpoints Implementados

| Endpoint | Método | Função |
|---|---|---|
| `/health` | GET | Status do serviço + se a coleção está indexada |
| `/ingest` | POST | (Re)indexa todos os documentos da pasta `docs/protocolos/` |
| `/chat` | POST | Pergunta → RAG → resposta LLM + fontes com scores |
| `/search` | POST | Busca vetorial sem geração — debug do pipeline RAG |

**Decisão de design 📌 — `/search` como ferramenta de debug:** endpoint mantido mesmo em produção. Permite inspecionar quais chunks o retriever está retornando para uma query, sem custo de chamada LLM. Útil para diagnosticar respostas ruins sem precisar de logs de servidor.

---

### 3.3 Modo Mock ✅

**Motivação:** permitir desenvolvimento e testes sem chave de API configurada.

**Comportamento:** se `LLM_PROVIDER=mock` ou `LLM_API_KEY` vazio/`"mock"`, o `generate()` retorna resposta template indicando que está em modo mock, mostrando os chunks recuperados.

**Utilidade:** validar que o pipeline RAG (chunking → indexação → retrieval → formatação de contexto) funciona corretamente, independente do LLM.

---

### 3.4 O que ainda falta na Fase 3

#### 🔄 Session Manager (histórico de conversa)

**Status:** placeholder em `app/src/session/manager.py`. Estrutura prevista mas não implementada.

**Impacto:** atualmente cada pergunta é independente — o LLM não tem memória da conversa. Para perguntas de follow-up ("e no caso de grávidas?"), o usuário precisa repetir o contexto.

**Plano:** implementar com `dict` em memória (piloto) → Redis (produção).

#### 🔄 Webhook WhatsApp

**Status:** não iniciado. Aguardando:
1. Aprovação da Meta Business (conta WhatsApp Business verificada)
2. Deploy na VPS com HTTPS (Meta exige HTTPS para webhook)

---

## INFRAESTRUTURA — Docker

**Commits:** `15bb86f` (fix do modelo não copiado), `76e3e19` (scaffold).

---

### Docker: Multi-stage Build ✅

**Motivação:** separar build (compilação de dependências C/C++ como chromadb, onnxruntime) do runtime. Reduz imagem final e elimina ferramentas de build do container em produção.

**Estrutura:**
```dockerfile
# Builder: instala deps + baixa modelo de embedding (~120 MB)
FROM python:3.11-slim AS builder
RUN python -m venv /venv && /venv/bin/pip install -r requirements.txt
ENV HF_HOME=/model_cache
RUN /venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# Runtime: só o necessário para rodar
FROM python:3.11-slim
COPY --from=builder /venv /venv
COPY --from=builder /model_cache /root/.cache/huggingface
```

#### ❌ Bug crítico — modelo não copiado para runtime

**Erro:** build original usava `pip install --prefix=/install` e copiava `/install` para runtime. O modelo de embedding era baixado para `/model_cache` no builder, mas **não havia `COPY --from=builder /model_cache`** no runtime.

**Sintoma:** container subia, `/health` respondia ok, mas primeiro `POST /ingest` tentava baixar o modelo em runtime — sem internet no container isolado → timeout.

**Fix:** migrar de `--prefix=/install` para `python -m venv /venv` (venv completo), e adicionar `COPY --from=builder /model_cache /root/.cache/huggingface` explicitamente.

**Aprendizado:** sempre verificar que todos os artefatos do stage de build que serão usados em runtime tenham `COPY --from=builder` explícito. O Docker não copia automaticamente.

---

#### ⚠️ Docker Desktop no Windows — Problema de Update

**Situação:** Docker Desktop travou no update via GUI (instalador ficou pendurado por >30 min).

**Solução:**
```powershell
# 1. Matar processos Docker
taskkill /F /IM "Docker Desktop.exe" /T
taskkill /F /IM "dockerd.exe" /T

# 2. Atualizar via winget
winget upgrade Docker.DockerDesktop
# Baixou 602 MB, instalou sem interação

# 3. Reiniciar Docker Desktop normalmente
```

**Nota para VPS:** este problema é específico de Windows dev. Na VPS Hetzner (Ubuntu 22.04), Docker Engine é instalado via apt — sem GUI, sem esse problema.

---

### docker-compose.yml ✅

**Volume persistente para ChromaDB:**
```yaml
volumes:
  - chroma_data:/app/chroma_db
```

**Motivo:** sem volume nomeado, o ChromaDB seria reinicializado a cada `docker-compose up`. Operação `/ingest` levaria ~2–5 min nos PDFs grandes — inaceitável a cada restart.

---

## DECISÕES FINANCEIRAS

### Infraestrutura por Fase

| Fase | Servidor | Custo | RAM | Motivo |
|---|---|---|---|---|
| POC | Local (Windows) | R$0 | — | desenvolvimento |
| Piloto | Hetzner CX22 | ~R$25/mês | 4 GB | 5 enfermeiras, baixa carga |
| Produção | Hetzner CPX31 | ~R$130/mês | 8 GB | carga institucional |

**Decisão chave 📌:** a análise financeira (v1) indicou CX22 para piloto, não CPX31. A diferença de R$105/mês é significativa para um projeto de TCC sem financiamento externo.

**Limitação da CX22:** 4 GB RAM pode ser insuficiente para Docling processar PDFs grandes (ver seção 2.2). Mitigação: pré-processar PDFs localmente.

---

## PENDÊNCIAS POR FASE

### Fase 2 (Engenharia de Dados) — quase completa

- [ ] **Pré-processar PDFs → `.md` localmente e commitar**: elimina dependência de Docling no container, resolve problema de RAM na VPS
- [ ] **Pipeline RAGAS**: gate de qualidade antes do piloto. Métricas-alvo: Faithfulness ≥ 0.80, Context Precision ≥ 0.75

### Fase 3 (Backend) — parcialmente completa

- [ ] **Session manager**: histórico de conversa em memória (dict por `session_id`)
- [ ] **Webhook Meta/WhatsApp**: rota `GET /webhook` (verificação) + `POST /webhook` (recebimento de mensagens)
- [ ] **Fallback por score baixo**: retornar mensagem padrão quando nenhum chunk supera `retriever_score_threshold` (0.50)

### Fase 4 (Piloto Hetzner) — próxima

- [ ] **Provisionar CX22**: criar conta Hetzner, provisionar servidor Ubuntu 22.04
- [ ] **UFW firewall**: liberar apenas 22 (SSH), 80 (HTTP→HTTPS redirect), 443 (HTTPS)
- [ ] **Nginx + Certbot**: HTTPS obrigatório para webhook Meta
- [ ] **Clonar repo + `docker-compose up`**: deploy inicial
- [ ] **Testes com enfermeiras**: aprovação do CEP necessária

### Fase 5 (Produção) — futura

- [ ] Migrar ChromaDB → Qdrant (busca híbrida dense+sparse)
- [ ] Migrar LLM → gpt-4o-mini (OpenAI)
- [ ] Session manager → Redis
- [ ] Monitoramento: Prometheus + Grafana ou Uptimerobot (simples)
- [ ] Migrar servidor CX22 → CPX31

---

## LIÇÕES APRENDIDAS

1. **Chunking semântico > tamanho fixo para documentos clínicos.** Seções de protocolos têm coesão interna — quebrar por bytes ignora o significado.

2. **Docling é pesado localmente, mas o fallback de texto nativo salva.** Documentos do MS têm camada de texto, então mesmo páginas onde o modelo de visão falhou por falta de RAM, o texto foi extraído.

3. **`async def` sem `asyncio.to_thread` para libs síncronas é pior que `def`.** Bloqueia o event loop inteiro. A correção exige identificar cada chamada bloqueante.

4. **Dockerfile multi-stage: listar explicitamente tudo que runtime precisa do builder.** Docker não herda automaticamente.

5. **Testar com os dados reais o quanto antes.** A POC usou um `.md` de exemplo. Só ao indexar os 6 PDFs reais do MS é que descobrimos o problema de RAM com Docling e que o PyMuPDF não servia para PDFs com layout complexo.

6. **Mode mock é essencial em projetos de TCC.** Permite trabalhar sem gastar créditos de API durante desenvolvimento.

---

*Última atualização: 2026-03-20*
