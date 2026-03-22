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

**Motivação:** ao trabalhar com os PDFs reais do MS, o PyMuPDF falhou em documentos com layout de múltiplas colunas (ver seção 2.3). Docling (IBM, open-source) converte PDF → Markdown estruturado, preservando hierarquia de títulos e tabelas.

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

### 2.3 O que NÃO funcionou ao trabalhar com os PDFs reais

#### ❌ Extração de PDF com PyMuPDF (`fitz`)

**Contexto:** ao receber os 6 PDFs reais do MS e tentar integrá-los ao pipeline, a primeira tentativa foi usar PyMuPDF — biblioteca mais comum para extração de texto de PDF em Python.

**Tentativa:** `fitz.open(pdf).get_text("text")` para extrair texto plano.

**Problema:** PDFs do MS têm layout complexo em múltiplas colunas e tabelas. O PyMuPDF retornava texto em ordem de leitura do PDF (coluna por coluna), não em ordem lógica do documento. Tabelas de doses saíam como sequência de números sem contexto.

**Exemplo de falha:**
```
# Output PyMuPDF (fragmento real):
"300 mg 4 meses 900 mg 4 meses 300 mg"
# Sem indicação de qual campo é qual coluna da tabela
```

**Decisão:** substituir por Docling (ver seção 2.2).

---

#### ❌ Chunking por overlap fixo com LangChain `RecursiveCharacterTextSplitter`

**Contexto:** ao adaptar o pipeline para os PDFs reais, foi avaliado usar LangChain como alternativa ao chunker customizado, pelo ecossistema mais amplo.

**Tentativa:** `chunk_size=512, chunk_overlap=50`.

**Problema:** overlap criava chunks redundantes. O retriever retornava 2–3 chunks muito similares (um era a sobreposição do outro), desperdiçando o `top_k` com conteúdo duplicado e aumentando o contexto enviado ao LLM sem ganho de informação.

**Decisão:** manter o chunker semântico por cabeçalho sem overlap — chunks distintos por definição.

---

### 2.4 Estrutura de Módulos da Ingestão

```
app/src/rag/ingestion/
├── __init__.py
├── chunker.py        # split_by_sections() — puro, sem I/O
├── indexer.py        # orquestra: lê arquivos → chunker → ChromaDB
└── pdf_extractor.py  # Docling: PDF → Markdown
```

**Decisão de design 📌:** separar `pdf_extractor` de `indexer`. Motivo: permite testar extração independentemente, e facilita substituição do extrator (ex.: trocar Docling por outra lib) sem tocar no indexer.

---

### 2.5 Revisão de Código e Correções Técnicas ✅

**Objetivo:** Corrigir anti-padrões e gaps identificados em revisão de engenharia antes de avançar para avaliação RAGAS e deploy.

**Período:** 2026-03-20 (sessão de revisão técnica com assistência de IA).

---

#### 2.5.1 Centralização do Embedding Model ✅

**Problema:** `indexer.py` e `retriever.py` instanciavam `SentenceTransformerEmbeddingFunction` separadamente, carregando o modelo de ~120 MB duas vezes na memória (~240 MB total). Na VPS CX22 com 4 GB de RAM, esse desperdício é crítico.

**Solução:** criado `app/src/rag/embeddings.py` com instância única compartilhada:
```python
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from app.src.config import settings

embedding_fn = SentenceTransformerEmbeddingFunction(
    model_name=settings.embedding_model
)
```

Ambos `indexer.py` e `retriever.py` agora importam de `app.src.rag.embeddings`. Economia estimada: ~120 MB de RAM.

---

#### 2.5.2 Filtro por Score Threshold no Retriever ✅

**Problema:** `config.py` definia `retriever_score_threshold = 0.50`, mas nenhum código filtrava chunks abaixo desse valor. Se o retriever retornasse 4 chunks com scores de 0.30, todos iam para o LLM — que poderia gerar respostas a partir de contexto irrelevante. Em contexto clínico, isso é perigoso.

**Solução em `retriever.py`:**
```python
return [c for c in chunks if c.score >= settings.retriever_score_threshold]
```

**Solução em `chat.py`:** quando nenhum chunk passa no filtro, retorna HTTP 200 com mensagem de fallback (em vez de HTTP 404):
```python
_FALLBACK_ANSWER = (
    "Não encontrei trechos suficientemente relevantes nos protocolos para responder "
    "com segurança. A pergunta pode estar fora do escopo do material indexado. "
    "Consulte diretamente o Manual de Recomendações do Ministério da Saúde."
)
```

**Decisão de design 📌:** retornar 200 com fallback em vez de 404. Motivo: a API funcionou corretamente, apenas não encontrou contexto relevante — não é um erro de recurso inexistente. O 404 anterior confundia clientes HTTP que tratam 4xx como erro.

---

#### 2.5.3 Remoção de `chunk_overlap` do Config de Produção ✅

**Problema:** `config.py` de produção continha `chunk_overlap = 100`, herdado da POC, mas o chunker semântico (`split_by_sections`) não usa overlap. Parâmetro morto que poderia confundir quem lesse o código.

**Solução:** removido de `app/src/config.py`. O parâmetro permanece apenas no código legado da POC (`poc/src/config.py`), preservando o histórico.

---

#### 2.5.4 Client LLM Singleton ✅

**Problema:** `client.py` instanciava `AsyncOpenAI` a cada chamada a `generate()`. Embora o impacto em performance fosse pequeno (o objeto é leve), era um anti-padrão que poderia causar vazamento de conexões HTTP sob carga.

**Solução:** lazy initialization com variável de módulo:
```python
_client: AsyncOpenAI | None = None

def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url or None,
        )
    return _client
```

---

#### 2.5.5 Try/Except no Docling `pdf_extractor.py` ✅

**Problema:** `extract_markdown()` não tratava exceções. Se um PDF falhasse (ex.: `std::bad_alloc`), o pipeline inteiro parava.

**Solução:** `try/except` que retorna string vazia em caso de erro; `indexer.py` agora pula arquivos com texto vazio:
```python
def extract_markdown(pdf_path: Path) -> str:
    try:
        result = _get_converter().convert(str(pdf_path))
        return result.document.export_to_markdown()
    except Exception as e:
        logger.error("Falha ao extrair %s: %s", pdf_path.name, e)
        return ""
```

---

#### 2.5.6 Remoção de `session_id` do `ChatRequest` ✅

**Problema:** `ChatRequest` tinha campo `session_id` que não era usado em nenhum lugar — código morto que dava impressão falsa de que sessões estavam implementadas.

**Solução:** removido o campo. Adicionado comentário na docstring indicando que será implementado na integração com WhatsApp (Fase 3).

---

### 2.6 Pré-extração de PDFs para Markdown ✅

**Objetivo:** eliminar dependência do Docling no container de produção e resolver o problema de RAM na VPS CX22 (4 GB).

**Período:** 2026-03-20.

---

#### 2.6.1 Script `extract_pdfs.py` ✅

**Implementação:** criado `app/scripts/extract_pdfs.py` que:
- Itera sobre todos os `.pdf` em `docs/protocolos/`
- Pula se `.md` de mesmo nome já existe (idempotente)
- Flag `--force` para sobrescrever `.md` existentes
- Reporta gerados/pulados/erros ao final

```bash
python -m app.scripts.extract_pdfs [--force]
```

#### 2.6.2 Resultados da Extração

6 PDFs processados com sucesso:

| Documento | Chars | Cabeçalhos |
|---|---|---|
| `9789275728185_por.md` (OMS Módulo 4) | ~295k | ~133 |
| `Manual de Recomendações para o controle da Tuberculose no Brasil.md` | ~270k | ~120 |
| `af_protocolo_vigilancia_iltb_2ed_9jun22_ok_web.md` | ~30k | ~35 |
| `recomendacoes-para-o-controle-da-tuberculose.md` | ~40k | ~45 |
| `GEDIIB_TratamentoTuberculose.md` | ~12k | ~15 |
| `tratamento_infeccao_latente_tuberculose_rifapentina_eletronico.md` | ~4k | ~11 |

**Decisão:** os `.md` são versionáveis (adicionados ao git); os `.pdf` continuam no `.gitignore` por serem documentos do MS que não devem ser redistribuídos.

---

#### 2.6.3 Atualização do `indexer.py` — `_resolve_files()` ✅

**Problema:** se tanto o `.pdf` quanto o `.md` de mesmo nome estivessem na pasta, o indexer processaria ambos — duplicando chunks.

**Solução:** criada função `_resolve_files()` que prefere `.md` sobre `.pdf` de mesmo stem:
```python
def _resolve_files(folder: Path) -> list[Path]:
    md_stems = {f.stem for f in folder.glob("*.md")}
    files: list[Path] = []
    for pdf in folder.glob("*.pdf"):
        if pdf.stem in md_stems:
            logger.info("PDF ignorado (usando .md equivalente): %s", pdf.name)
        else:
            files.append(pdf)
    files += list(folder.glob("*.md"))
    files += list(folder.glob("*.txt"))
    return files
```

**Resultado:** zero duplicação. VPS só precisa de chunking + indexação (sem Docling).

---

### 2.7 Pipeline de Avaliação RAGAS 🔄

**Objetivo:** Implementar avaliação automatizada do pipeline RAG usando o framework RAGAS, conforme exigido pelos objetivos 1 e 2 do TCC (metodologia DSRM). Métricas-alvo: Faithfulness ≥ 0.80, Context Precision ≥ 0.75.

**Período:** 2026-03-20.

---

#### 2.7.1 Test Set — 40 Perguntas ✅

**Implementação:** `eval/test_set.json` com 40 perguntas divididas em 8 categorias:

| Categoria | Qtd | Descrição |
|---|---|---|
| `esquemas_terapeuticos` | 7 | Doses, durações, escolha por perfil (3HP, 4R, 6H, 9H) |
| `monitoramento` | 5 | Frequência de consultas, critérios de suspensão |
| `interacoes_medicamentosas` | 5 | Rifampicina + ARV, contraceptivos, isoniazida + fenitoína |
| `populacoes_especiais` | 7 | Gestantes, crianças, PVHIV, anti-TNF, hepatopatas |
| `diagnostico` | 5 | PPD/IGRA pontos de corte, exclusão TB ativa |
| `indicacoes_tratamento` | 5 | Elegibilidade, grupos prioritários |
| `efeitos_adversos` | 4 | Hepatotoxicidade, neuropatia, piridoxina |
| `fora_do_escopo` | 4 | TB ativa, pneumonia, COVID — testam fallback |

**Ground truths:** extraídos literalmente dos `.md` gerados pelos PDFs reais do MS. As 4 perguntas `fora_do_escopo` têm `ground_truth: null` e são excluídas do RAGAS — servem apenas para verificar se o fallback funciona.

**Decisão de design 📌:** ground truths são extração do texto dos documentos, não validação clínica independente. O test set deve ser revisado por enfermeira especialista em TB antes de ser usado como gate definitivo na monografia.

---

#### 2.7.2 Script `run_ragas.py` ✅

**Implementação:** `eval/run_ragas.py` — pipeline completo:
1. Carrega test set, separa in-scope (36) e fora do escopo (4)
2. Para cada pergunta in-scope: executa `retrieve()` + `generate()` do pipeline real
3. Salva `eval/results/ragas_detailed.json` com resposta, contextos e ground truth
4. Calcula métricas RAGAS usando Groq como LLM juiz + embeddings locais (mesmo modelo de produção)
5. Salva `eval/results/ragas_scores.json` com médias

**Configuração do LLM avaliador:**
- LLM juiz: Groq `llama-3.3-70b-versatile` via `ChatOpenAI` (interface OpenAI-compatible)
- Embeddings: `HuggingFaceEmbeddings` com `paraphrase-multilingual-MiniLM-L12-v2` (evita dependência de chave OpenAI)
- Sleep de 2s entre chamadas para respeitar rate limit

**Flag `--scores-only`:** permite recalcular apenas as métricas RAGAS usando `ragas_detailed.json` já salvo, sem re-executar o pipeline RAG. Útil quando o rate limit do Groq é atingido durante a fase de avaliação.

**Dependências instaladas:**
- `ragas 0.4.3`
- `datasets 4.8.3`
- `langchain-openai`
- `langchain-community` (para `HuggingFaceEmbeddings`)
- `scikit-network` — exigiu instalação manual do Visual C++ Build Tools no Windows

---

#### 2.7.3 Execuções — Sequência de Bugs e Status ⚠️

**Execução 1 — pipeline RAG:** rodou com sucesso para as 36 perguntas in-scope. `ragas_detailed.json` salvo com respostas, contextos e ground truths. RAGAS completou **152/152 steps**, mas travou em `_print_summary()` com `AttributeError: 'EvaluationResult' object has no attribute 'get'` — `ragas_scores.json` não salvo.

**Fix 1 (commit `f08557b`):** `result.get(metric_name)` → `result[metric_name]`. Adicionada flag `--scores-only` para reutilizar `ragas_detailed.json` sem re-executar pipeline RAG.

**Execução 2 — `--scores-only`:** RAGAS completou **152/152 steps**, mas novo crash:
```
TypeError: float() argument must be a string or a real number, not 'list'
```
Causa: RAGAS 0.4 retorna `result["faithfulness"]` como lista de scores por amostra, não float. A média precisa ser calculada manualmente.

**Fix 2 (commit `4a01170` parcial):** `_get_score()` agora calcula média da lista, filtrando `None`.

**Execução 3 — `--scores-only`:** RAGAS completou **152/152 steps**, mas novo crash:
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2265'
```
Causa: caractere `≥` não suportado pelo encoding CP1252 do terminal Windows.

**Fix 3:** substituído `≥` por `>=` em todas as strings de output.

**Execução 4 — `--scores-only`:** RAGAS completou **152/152 steps**, script chegou ao final sem crash. Porém todos os scores retornaram `nan`:
```
faithfulness           nan  (alvo: >= 0.8)  [FAIL]
answer_relevancy       nan
context_precision      nan  (alvo: >= 0.75)  [FAIL]
context_recall         nan
```

**Causa do `nan`:** o TPD do Groq (100k tokens/24h) estava esgotado pelas execuções anteriores do mesmo dia (`Used ~99.7k`). Quase todos os 152 jobs falharam com `RateLimitError`, e o RAGAS preenche scores falhados com `float('nan')`. A média de uma lista inteiramente `nan` retorna `nan`. O filtro `v is not None` não excluía `float('nan')`.

**Fix 4 (commit `4a01170`):** adicionado filtro `math.isnan(v)` na função `_get_score()`. Também adicionado diagnóstico de quantas amostras foram avaliadas com sucesso por métrica.

**Fix 4 produziu `nan`:** mesmo com nan filtrado, os scores continuaram `nan` nas execuções seguintes porque o TPD estava sempre esgotado de execuções anteriores do mesmo dia.

**Execuções 5–6 — troca de LLM avaliador para 8b:** trocado `llama-3.3-70b-versatile` (100K TPD) por `llama-3.1-8b-instant` (500K TPD) como LLM juiz. Resolveu o TPD, mas descobriu novo limite: **TPM (tokens por minuto) = 6.000** — igual para ambos os modelos. Com `max_workers=4` (padrão), 4 jobs de ~1.200 tokens = 4.800 tokens/min, próximo do limite. Muitos jobs falharam com `RateLimitError: TPM` e outros com `TimeoutError` (~10-16 amostras avaliadas de 38).

**Fix 5–6:** `request_timeout=120` no ChatOpenAI (não resolveu — o timeout do RAGAS executor é independente). Depois: `RunConfig(max_workers=4, timeout=180)` (melhorou timeouts mas TPM continuou problemático).

**Execução 7 — `--scores-only --max-questions 12` (commit `503468a`) ✅:**
- Adicionada flag `--max-questions N` para limitar o subconjunto avaliado
- `RunConfig(max_workers=1, timeout=180)`: processamento sequencial, ~20s/job, bem abaixo do TPM
- 48/48 jobs completaram sem rate limit nem timeout
- Único erro residual: `BadRequestError: 'n' > 1` — esperado, não-fatal para faithfulness

**Primeiros scores válidos — 12 perguntas, modelo juiz `llama-3.1-8b-instant`:**
```
faithfulness           0.389  (alvo: >= 0.80)  [FAIL]  (12/12 amostras)
context_precision      0.600  (alvo: >= 0.75)  [FAIL]  (12/12 amostras)
context_recall         0.689                            (12/12 amostras)
answer_relevancy       N/A    (n > 1 bloqueia metric — 0/12 amostras)
```

**Interpretação dos resultados:**
- `context_recall 0.689`: o retriever cobre ~69% das informações do ground truth. Aceitável para top-k=4.
- `context_precision 0.600`: 60% dos chunks recuperados são relevantes. Abaixo do alvo de 0.75 — indica ruído no retrieval.
- `faithfulness 0.389`: apenas 39% das afirmações da resposta são sustentadas pelos chunks recuperados segundo o juiz 8b. **Número preocupante**, mas com ressalva: o modelo 8b é significativamente menos capaz como juiz que o 70b — pode subestimar a faithfulness por dificuldade em raciocinar sobre alinhamento textual.
- `answer_relevancy N/A`: o RAGAS usa n>1 para gerar questões hipotéticas nesta métrica. Groq não suporta n>1. Métrica não calculável sem mudar de LLM ou configurar o metric.

**Conclusão desta execução:** os scores são reais (não nan, não baseados em 2/38 amostras), mas abaixo dos alvos. O pipeline precisa de ajuste antes de avançar ao piloto. Ver seção PENDÊNCIAS para próximos passos de tuning.

---

#### 2.7.4 Bugs Encontrados na Instalação e Execução do RAGAS ❌

##### `scikit-network` exige Visual C++ Build Tools no Windows

**Sintoma:** `pip install ragas` falhou com `error: Microsoft Visual C++ 14.0 or greater is required`.

**Causa:** `scikit-network` (dependência indireta do RAGAS) tem extensões C que precisam ser compiladas. No Windows, isso exige o Visual C++ Build Tools (~5 GB).

**Solução de contorno:** instalar todas as outras dependências do RAGAS manualmente (`pip install ragas --no-deps` + cada dep individualmente). `scikit-network` não é usada pelas métricas que precisamos (faithfulness, answer_relevancy, context_precision, context_recall).

**Nota para TCC:** na VPS Linux, `pip install ragas` funciona sem problemas — `scikit-network` compila normalmente com gcc. Problema exclusivo do Windows dev.

---

##### RAGAS tenta usar embeddings OpenAI por padrão ❌

**Sintoma:**
```
openai.AuthenticationError: No API key provided... for metric 'answer_relevancy'
```

**Causa:** o RAGAS usa embeddings para calcular `answer_relevancy` (mede similaridade semântica entre resposta e pergunta). Por padrão, tenta `OpenAIEmbeddings` — que exige `OPENAI_API_KEY`.

**Solução:** passar `embeddings=` explicitamente no `evaluate()` com o modelo local:
```python
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper

evaluator_embeddings = LangchainEmbeddingsWrapper(
    HuggingFaceEmbeddings(model_name=settings.embedding_model)
)
result = evaluate(dataset=dataset, metrics=[...], llm=evaluator_llm, embeddings=evaluator_embeddings)
```

**Resultado:** RAGAS passa a usar o mesmo modelo de produção (`paraphrase-multilingual-MiniLM-L12-v2`) sem custo adicional.

---

##### Groq não suporta `n > 1` nas completions ⚠️ (não-fatal)

**Sintoma:**
```
UserWarning: LLM returned 1 generations instead of requested 3. Proceeding with 1 generations.
```

**Causa:** para a métrica `faithfulness`, o RAGAS pede `n=3` completions para estimar variabilidade. A API do Groq rejeita `n > 1` silenciosamente, retornando apenas 1.

**Impacto:** o RAGAS procede com 1 generation. A métrica é calculada com menos amostras — menor robustez estatística. Para uma POC/TCC, é aceitável.

**Alternativa futura:** usar `gpt-4o-mini` (OpenAI) como LLM juiz na avaliação de produção — suporta `n > 1`.

---

##### `EvaluationResult` não tem método `.get()` ❌

**Sintoma:**
```
AttributeError: 'EvaluationResult' object has no attribute 'get'
```

**Contexto:** RAGAS 0.4 mudou a API do objeto de resultado. Versões anteriores retornavam um `dict` com `.get()`. RAGAS 0.4 retorna `EvaluationResult` com acesso por `result["metric_name"]`.

**Impacto:** avaliação completa (152 steps), resultado em memória — mas `ragas_scores.json` não salvo por crash no `_print_summary`.

**Fix:** `result.get(metric_name)` → `result[metric_name]` (com try/except para KeyError).

---

#### 2.7.5 Bugs Adicionais Descobertos nas Execuções 2–4 ❌

##### `result["metric"]` retorna lista, não float ❌

**Sintoma:**
```
TypeError: float() argument must be a string or a real number, not 'list'
```

**Contexto:** RAGAS 0.4 `EvaluationResult` armazena scores por amostra como lista — `result["faithfulness"]` retorna `[0.87, 0.92, 0.76, ...]`. Não há propriedade `.mean` automática.

**Fix:** função `_get_score()` reformulada para calcular média manualmente:
```python
if isinstance(val, list):
    valid = [v for v in val if v is not None and not math.isnan(v)]
    return sum(valid) / len(valid) if valid else None
```

---

##### `float('nan')` em jobs falhados não é filtrado por `v is not None` ❌

**Sintoma:** todos os scores exibidos como `nan` mesmo após fix da lista.

**Causa:** quando um job RAGAS falha (rate limit, timeout), o score daquela amostra é preenchido com `float('nan')`, não `None`. O filtro `v is not None` era True para `nan` — `nan` passa o teste, contamina a média.

**Fix:** adicionado `and not (isinstance(v, float) and math.isnan(v))` ao filtro.

**Aprendizado:** em Python, `float('nan') is not None` é `True`. Qualquer agregação numérica que não filtra explicitamente `nan` propaga silenciosamente o valor indefinido.

---

##### `≥` causa `UnicodeEncodeError` no terminal Windows ❌

**Sintoma:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2265'
```

**Causa:** terminal Windows usa encoding CP1252 por padrão. O caractere `≥` (U+2265) não está no conjunto de caracteres CP1252.

**Fix:** substituído `≥` por `>=` nas strings de output. Alternativa mais robusta (não aplicada para manter simplicidade): `PYTHONUTF8=1` na variável de ambiente ou `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`.

**Nota para TCC:** na VPS Linux com locale UTF-8, esse problema não ocorre. Exclusivo do ambiente Windows dev.

---

### 2.8 Decisão — Trocar LLM Provider para Avaliação RAGAS 📌

**Motivação:** após 7 execuções consecutivas do RAGAS, ficou claro que o Groq free tier é inadequado como LLM juiz de avaliação:

| Limitação | Impacto |
|---|---|
| TPD 100K tokens/dia (70b) | Esgota com pipeline RAG + RAGAS no mesmo dia |
| TPM 6K tokens/min (ambos) | Força processamento sequencial (`max_workers=1`) |
| Não suporta `n > 1` | Bloqueia completamente `answer_relevancy` |
| 8b subestima faithfulness | Score 0.389 provavelmente não reflete qualidade real |

**Conclusão:** o Groq é adequado para o pipeline RAG de produção (baixa latência, gratuito, suficiente para 5 enfermeiras), mas inadequado como LLM juiz do RAGAS — a avaliação exige um modelo mais capaz e com limites de API mais generosos.

**Próximo passo:** buscar alternativa para o LLM juiz da avaliação. Candidatos:
- **OpenAI gpt-4o-mini**: $0,15/1M tokens input — ~$0,05 para 38 perguntas × 4 métricas. Suporta `n > 1`, sem TPM restritivo. O `run_ragas.py` já suporta via `LLM_BASE_URL` vazio + `LLM_API_KEY` OpenAI.
- **Google Gemini Flash**: free tier generoso (1.500 req/dia, 1M tokens/min) — compatível com interface OpenAI via `openai_api_base`.
- **Outro modelo Groq**: `gemma2-9b-it` tem 15K TPM e suporta melhor raciocínio que o 8b instant.

**Impacto no pipeline de produção:** zero. A troca de LLM juiz afeta apenas `eval/run_ragas.py` — o chatbot continua usando Groq/llama em produção.

#### Workaround atual com Groq — `--max-questions 12`

Enquanto não há um LLM juiz melhor disponível, a única forma de obter scores válidos com o Groq free tier é limitar o número de perguntas avaliadas:

```bash
.venv/Scripts/python -m eval.run_ragas --scores-only --max-questions 12
```

**Por que 12 e não 38?** Com `max_workers=1` (sequencial) e ~1.200 tokens por job:
- 12 perguntas × 4 métricas = 48 jobs × ~1.200 tokens = **~57.600 tokens total**
- Tempo estimado: ~15 min, média ~64 tokens/s — abaixo do TPM de 100 tokens/s (6K/min)
- 38 perguntas × 4 métricas = 152 jobs × ~1.200 tokens = **~182.400 tokens total**
- A picos de ~4 jobs simultâneos (mesmo com `max_workers=1`, o executor pode fazer bursts curtos), o TPM de 6K é excedido com facilidade

**Limitação desta abordagem:** 12 perguntas é um subconjunto não-aleatório (primeiras 12 do `ragas_detailed.json`, que são da categoria `esquemas_terapeuticos` e início de `monitoramento`). Os scores obtidos não cobrem todas as categorias do test set — `interacoes_medicamentosas`, `populacoes_especiais`, `diagnostico` etc. ficam de fora. Os resultados são orientativos, não conclusivos para o gate do TCC.

**Recomendação:** usar `--max-questions 12` apenas para desenvolvimento e validação rápida. O gate definitivo (Faithfulness >= 0.80, Context Precision >= 0.75 sobre as 38 perguntas) deve ser executado com o novo LLM provider.

---

### 2.9 Tentativa — Google Gemini Flash como LLM Juiz ❌

**Motivação:** o Groq free tier tem três bloqueadores para o RAGAS (n>1 não suportado, TPM 6K, 8b subestima faithfulness). O Google Gemini Flash tem free tier com 1.500 req/dia e 1M tokens/min, e é compatível com a interface OpenAI via endpoint `/v1beta/openai`.

**Implementação:** adicionados campos `RAGAS_LLM_*` ao `config.py` e ao `.env`. O `run_ragas.py` detecta `settings.ragas_llm_api_key` e usa um LLM juiz dedicado, diferente do LLM de produção. Quando configurado, o `RunConfig` usa `max_workers=4` (paralelismo total).

Variáveis adicionadas ao `.env`:
```env
RAGAS_LLM_PROVIDER=gemini
RAGAS_LLM_API_KEY=AIzaSy...
RAGAS_LLM_MODEL=gemini-2.0-flash-lite
RAGAS_LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
```

**Modelos testados (em ordem):**

| Modelo | Resultado | Erro |
|---|---|---|
| `gemini-2.0-flash` | ❌ | `RESOURCE_EXHAUSTED: limit: 0` — free tier quota = 0 |
| `gemini-1.5-flash` | ❌ | `404 Not Found` — modelo não disponível nesta versão do endpoint |
| `gemini-2.0-flash-lite` | ❌ | `RESOURCE_EXHAUSTED: limit: 0` — mesmo erro |

**Erro completo:**
```
RESOURCE_EXHAUSTED: 429 Resource has been exhausted.
GenerateRequestsPerDayPerProjectPerModel-FreeTier
quota_limit { limit: 0 }
```

**Diagnóstico:** o erro `limit: 0` indica que o projeto Google Cloud associado a esta chave API não tem quota free tier ativa para a API Gemini. Isso ocorre quando:
1. A conta Google não ativou a API Gemini no projeto correto, ou
2. O projeto está em região sem free tier (alguns países não têm acesso), ou
3. A conta nunca concluiu o processo de ativação do Gemini API Studio

**Não é um bug do código** — a configuração está correta. É uma limitação da conta/projeto Google. Para resolver: acessar Google AI Studio (aistudio.google.com), criar um novo projeto, gerar uma nova API key e testar diretamente com `curl`.

**Tentativa 2 — chave do AI Studio + `gemini-flash-latest`:**

A chave do AI Studio funcionou na API nativa (`gemini-flash-latest` → `gemini-3-flash-preview`). Atualizado `.env` para usar esse model name. Resultado:

| Modelo | TPM | **TPD** | n>1 | Conclusão |
|---|---|---|---|---|
| `gemini-2.0-flash` | — | **0** | — | quota zero na conta |
| `gemini-2.0-flash-lite` | — | **0** | — | quota zero na conta |
| `gemini-flash-latest` (`gemini-3-flash-preview`) | 5/min | **20/dia** | ❌ | 20 req/dia → apenas ~1,5 perguntas avaliadas |

**Diagnóstico final:** `gemini-3-flash` é um modelo preview com limites extremamente restritivos (20 req/dia). Para 38 perguntas × 4 métricas = 152 jobs, seriam necessários **8 dias** de quota acumulada. Inviável.

Problemas adicionais identificados:
- `faithfulness` timeout (120s) — modelo preview é mais lento que modelos estáveis
- `n > 1` não suportado — `answer_relevancy` = N/A (igual ao Groq)

**Conclusão definitiva sobre Gemini:** nenhum modelo Gemini acessível com esta chave/conta tem quota free tier suficiente para o RAGAS completo.

**Próxima alternativa — OpenAI gpt-4o-mini:**
Custo estimado: ~$0,05 para 38 perguntas × 4 métricas. Suporta `n > 1` (resolve `answer_relevancy`), sem TPM restritivo, sem TPD limitante. O `run_ragas.py` já suporta sem nenhuma alteração — basta configurar:
```env
RAGAS_LLM_API_KEY=sk-...
RAGAS_LLM_MODEL=gpt-4o-mini
RAGAS_LLM_BASE_URL=   # vazio = usa endpoint padrão OpenAI
```

---

### 2.10 Avaliação Definitiva — gpt-4o-mini como LLM Juiz ✅

**Data:** 2026-03-21

**Objetivo:** primeira avaliação RAGAS completa com juiz capaz (gpt-4o-mini), cobrindo todas as 38 perguntas in-scope.

**Pré-condições:**
- LLM juiz: `gpt-4o-mini` via `RAGAS_LLM_*` no `.env`
- `RAGAS_LLM_BASE_URL` vazio → endpoint padrão OpenAI
- `RunConfig(max_workers=4, timeout=180, max_retries=3)` — sem rate limit restritivo
- 152/152 jobs completados em ~6,5 min

**Descoberta crítica — threshold 0.50 excluía 4 perguntas:**

Antes de obter scores válidos, foi identificado que `retriever_score_threshold=0.50` filtrava completamente 4 perguntas legítimas:

| ID | Categoria | Score máx do retriever |
|---|---|---|
| ET-05 | esquemas_terapeuticos | 0.482 |
| IM-01 | interacoes_medicamentosas | 0.473 |
| IM-03 | interacoes_medicamentosas | 0.466 |
| DI-04 | diagnostico | 0.447 |

Com `contexts=[]`, RAGAS atribuía score zero nessas 4 amostras em todas as métricas, derrubando as médias.

**Decisão:** threshold reduzido de 0.50 para **0.40** em `app/src/config.py`. Justificativa: as perguntas sobre interações medicamentosas e diagnóstico usam terminologia técnica específica que o modelo de embedding multilíngue não captura tão bem quanto perguntas sobre esquemas terapêuticos numericamente específicos. O threshold de 0.40 ainda exige relevância mínima e descarta perguntas completamente fora do escopo.

**Resultados — avaliação completa (38/38 amostras, juiz gpt-4o-mini):**

```
faithfulness           0.375  (alvo: >= 0.80)  [FAIL]  (38/38 amostras)
answer_relevancy       0.310                            (38/38 amostras)
context_precision      0.548  (alvo: >= 0.75)  [FAIL]  (38/38 amostras)
context_recall         0.382                            (38/38 amostras)
```

**Análise dos resultados:**

| Métrica | Score | Interpretação |
|---|---|---|
| `context_recall` 0.382 | ⚠️ baixo | Retriever cobre apenas 38% das informações do ground truth. Com top_k=4 e chunks grandes, documentos com informação distribuída em múltiplas seções têm recall baixo. |
| `faithfulness` 0.375 | ⚠️ baixo | Só 37.5% das afirmações da resposta sustentadas pelos chunks. Correlacionado com o recall baixo — se o contexto não tem a informação, o LLM pode complementar com conhecimento interno. |
| `context_precision` 0.548 | ⚠️ moderado | 54.8% dos chunks recuperados são relevantes. Sem filtro por relevância além do threshold, noise é inevitável para algumas categorias. |
| `answer_relevancy` 0.310 | ❓ suspeito | Métrica projetada para inglês — gpt-4o-mini pode gerar questões sintéticas em inglês ao avaliar respostas em português, causando similaridade cossenoidal baixa no modelo multilíngue. Valor provavelmente subestimado por limitação metodológica. |

**Hipóteses para scores baixos:**

1. **top_k=4 é insuficiente para perguntas multi-documento.** Perguntas sobre interações medicamentosas exigem informação de múltiplas seções de múltiplos protocolos. Com 4 chunks, muita informação relevante fica de fora.

2. **Ground truths muito detalhados vs. respostas focadas.** Os ground truths foram extraídos literalmente dos documentos (seções completas). O pipeline gera respostas mais concisas — context_recall penaliza respostas que não cobrem 100% do ground truth verbatim.

3. **Limitação multilíngue do RAGAS.** O framework foi projetado e validado para inglês. `answer_relevancy` usa LLM para gerar perguntas hipotéticas — se o juiz gera em inglês, a similaridade cossenoidal com perguntas originais em português será artificialmente baixa.

**Próximos passos para melhorar scores:**

1. **Aumentar `top_k` de 4 para 6 ou 8** — recuperar mais chunks por pergunta aumenta recall
2. **Revisar ground truths** — truncar para respostas mais focadas (não seções completas)
3. **Melhorar prompt do LLM** — instruir o LLM a incluir mais detalhes do contexto

**Arquivo de resultados:** `eval/results/ragas_scores.json` (scores definitivos) + `eval/results/ragas_detailed.json` (respostas + contextos de todas as 38 perguntas).

---

### 2.11 Experimento — Contextual Chunking ❌ Descartado

**Data:** 2026-03-21

**Hipótese:** chunks "órfãos" — subseções sem título pai no texto — causam baixo recall porque o embedding não sabe a qual droga/protocolo pertence. Por exemplo: `### Gestantes` sem o contexto `## 3.1 Isoniazida` no texto do chunk faz a busca por "Isoniazida gestante" não encontrar esse chunk.

**Abordagem testada:** prefixar cada chunk com a hierarquia de cabeçalhos pai extraída do documento. Exemplo:

```
## 3.1 Isoniazida > ### Gestantes

### Gestantes
Gestantes com ILTB devem receber isoniazida...
```

**Implementação:** nova função `split_by_sections_contextual()` em `chunker.py` que rastreia o cabeçalho pai durante o split e prefixo no início de cada chunk filho.

**Configurações testadas:**

| Config | top_k | threshold | faithfulness | answer_relevancy | context_precision | context_recall |
|---|---|---|---|---|---|---|
| Baseline (original) | 4 | 0.40 | **0.375** | **0.310** | **0.548** | **0.382** |
| Contextual, top_k=6 | 6 | 0.50 | 0.347 | 0.214 | 0.477 | 0.265 |
| Contextual, top_k=6 | 6 | 0.40 | 0.180 | 0.143 | 0.388 | 0.204 |

**Resultado:** todas as métricas pioraram em ambas as configurações. O contextual chunking **degradou** o pipeline.

**Análise do fracasso:**

O modelo `paraphrase-multilingual-MiniLM-L12-v2` produz embeddings semânticos de 384 dimensões. Ao prefixar o chunk com `## 3.1 Isoniazida > ### Gestantes\n\n`, o vetor resultante é uma média ponderada da semântica do título + semântica do conteúdo real. Para chunks pequenos (< 200 tokens), o título representa 20–40% do texto total — dilui o embedding com strings de navegação estrutural, não com conteúdo clínico.

Modelos como `text-embedding-3-large` (OpenAI) têm 3072 dimensões e são treinados para ignorar noise estrutural — suportam contextual chunking bem. O MiniLM-L12 com 384 dimensões é sensível a qualquer texto adicionado ao chunk.

**Decisão:** revertido para o chunker original. A hipótese de chunks órfãos como causa do baixo recall está **rejeitada** — ou não é o fator dominante neste pipeline.

**Causa provável do baixo recall:** ground truths contêm seções completas do documento (até 800 tokens), enquanto as respostas do LLM são concisas (~200 tokens). O RAGAS `context_recall` mede se os chunks recuperados contêm a informação do ground truth — mas se o ground truth for uma seção completa e a resposta cobrir só parte dela, o score é penalizado.

**Próximo experimento a tentar:** truncar ground truths para respostas focadas (3–5 sentenças) antes de rodar RAGAS novamente.

---

### 2.12 Investigação dos Ground Truths + Bloqueador Groq TPM ⚠️

**Data:** 2026-03-21

**Contexto:** com scores RAGAS abaixo dos gates (faithfulness 0.375, context_recall 0.382), a hipótese levantada foi que os ground truths eram extratos literais de seções completas dos documentos (300-800 tokens), penalizando a concisão das respostas.

**Descoberta:** hipótese **incorreta**. Os ground truths no `eval/test_set.json` já estavam concisamente formatados (13–66 palavras cada), não havia seções completas sendo usadas como referência.

**Análise real por ground truth:**

| ID | Situação |
|---|---|
| ET-07 | Ground truth descreve dose pediátrica para pergunta sobre dose adulta — **corrigido** |
| PE-07 | Source_document errado (GEDIIB) — a info sobre 4R contraindicado em PVHIV está em `recomendacoes-para-o-controle-da-tuberculose.md` — **corrigido** |
| IM-01, IM-03 | Interações rifampicina+contraceptivos e isoniazida+fenitoína: clinicamente corretos, mas a seção 6.3 do Manual não foi extraída na indexação — retrieval sempre retorna 0 chunks com alta similaridade |
| Demais (34/36) | Ground truths já adequados |

**Correções aplicadas em `eval/test_set.json`:**
- ET-07: Ground truth agora descreve dose adulta corretamente ("5 a 10 mg/kg/dia, máx 300 mg/dia") e explica diferença 6H vs 9H
- PE-07: Ground truth agora menciona a contraindicação 4R para PVHIV em PI/integrase; source_document corrigido

**Tentativa de re-execução do pipeline — bloqueada por Groq TPM:**

Após confirmar que Groq estava ativo (teste manual bem-sucedido), o pipeline completo foi iniciado. Apenas ET-01 e ET-02 obtiveram respostas válidas antes do 429 (Rate Limit):

- Groq free tier: **6.000 tokens/minuto** para modelos 70B
- Prompt médio por pergunta: ~1.500 tokens (contexto + instrução + pergunta)
- Com `SLEEP_BETWEEN_CALLS = 2s`, é possível fazer no máximo 4 chamadas antes de exaurir o TPM
- Para 38 perguntas com ~1.500 tokens cada, seria necessário sleep de **~15 segundos** entre chamadas

**Status:** `ragas_scores.json` restaurado para os scores válidos da avaliação com gpt-4o-mini (0.375/0.310/0.548/0.382). O `ragas_detailed.json` atual é inválido (36/38 respostas são mensagens de erro do Groq).

**Causa raiz do baixo context_recall identificada:** a hipótese de ground truths longos está **descartada**. A causa real é a limitação do retriever:
1. IM-01 e IM-03 referenciam conteúdo não extraído na indexação (seção 6.3 do Manual)
2. Perguntas multi-documento (interações medicamentosas) exigem informação distribuída em múltiplos chunks — top_k=4 pode ser insuficiente

**Próximos experimentos:** aumentar `top_k` de 4 para 6–8, ou aumentar `SLEEP_BETWEEN_CALLS` para 15s e re-rodar pipeline com Groq livre de TPM (usar horário de baixo uso).

---

### 2.13 Patch Manual — Interações Medicamentosas + Limite TPD do Groq ⚠️

**Data:** 2026-03-21

**Contexto:** IM-01 ("Rifampicina tem interação com contraceptivos orais?") e IM-03 ("Isoniazida tem interação com fenitoína?") apresentavam context_recall baixo. A hipótese era que a seção 6.3 do Manual (Interações Medicamentosas, páginas 137–141) não havia sido extraída pelo Docling.

**Diagnóstico — Cenário B confirmado:**

O Docling falha com `std::bad_alloc` a partir da página 319 do PDF do Manual do MS. A seção 6.3 (páginas 137–141 do documento PDF mapeadas para páginas 319+ no índice do Docling) estava completamente ausente do `.md` extraído — nenhum conteúdo de interações medicamentosas indexado.

Confirmado rodando Docling novamente: mesmo erro, mesmas páginas afetadas.

**Solução aplicada:**

1. Extração manual com `pypdf` (v6.8.0, já disponível no venv) nas páginas 138–141 do PDF
2. Criação de `docs/protocolos/patch_interacoes_medicamentosas.md` com o conteúdo completo:
   - Tabela: Interações da Isoniazida (11 fármacos)
   - Seção detalhada: Isoniazida e Fenitoína — efeito é **Maior hepatotoxicidade** (não aumento de níveis plasmáticos como estava no GT)
   - Tabela: Interações da Rifampicina (14 fármacos)
   - Seção detalhada: Rifampicina e Contraceptivos Orais
   - Seção detalhada: Rifampicina e Antirretrovirais em PVHIV
   - Tabelas: Interações Etambutol e Pirazinamida
   - Notas clínicas: limiares para suspensão por hepatotoxicidade + piridoxina

3. **Correção IM-03:** ground truth corrigido de "inibe metabolismo da fenitoína, aumentando níveis plasmáticos" para "maior hepatotoxicidade — evitar uso concomitante" (alinhado com o Manual do MS)

4. Re-indexação do ChromaDB: `chroma_db/` deletado, 928 chunks re-indexados incluindo o patch

5. `SLEEP_BETWEEN_CALLS` ajustado de 2s para 15s no `eval/run_ragas.py` (necessário para respeitar TPM do Groq free tier: 6K tok/min com prompts de ~1.500 tok)

**Verificação de indexação:** consulta `"interacoes medicamentosas rifampicina contraceptivos"` retorna `patch_interacoes_medicamentosas.md` como primeiro resultado — conteúdo indexado com sucesso.

**Re-execução do pipeline — bloqueada por TPD (tokens por dia):**

| Chamada | Status | Causa |
|---|---|---|
| ET-01, ET-02, ET-03, ET-05 | ✅ Sucesso | TPD ainda disponível |
| ET-04 e demais (34/38) | ❌ 429 TPD | Limite diário de 100K tokens esgotado por execuções anteriores |

Mensagem de erro: `"tokens per day (TPD): Limit 100000, Used 99184, Requested 1159"`. O orçamento diário havia sido consumido pelas execuções anteriores (2s sleep run + re-runs do dia). Os scores calculados sobre 4/38 respostas válidas (faithfulness 0.086, etc.) **não são representativos** — `ragas_scores.json` restaurado para os valores válidos da avaliação com gpt-4o-mini.

**Estado atual do pipeline (pronto para re-execução):**

| Componente | Status |
|---|---|
| `patch_interacoes_medicamentosas.md` | ✅ Criado e indexado |
| ChromaDB re-indexado (928 chunks) | ✅ |
| IM-03 ground truth corrigido | ✅ |
| `SLEEP_BETWEEN_CALLS = 15s` | ✅ |
| `ragas_scores.json` | ⏳ Mantido nos valores válidos anteriores até re-execução |
| Re-execução completa | ⏳ Aguardando reset do TPD do Groq (~24h) |

**Previsão dos próximos scores (qualitativa):**
- `context_recall`: deve subir (IM-01 e IM-03 agora têm contexto disponível)
- `context_precision`: pode subir levemente (chunks mais relevantes para IM-*)
- `faithfulness` e `answer_relevancy`: sem mudança esperada (dependem da qualidade de resposta do LLM, não do retriever)

---

### 2.14 Auditoria Proativa de Ingestão e Governança de Dados ✅

**Data:** 2026-03-21

**Motivação:** o patch da seção 6.3 (seção 2.13) revelou que a avaliação automatizada (RAGAS) não substitui a validação de integridade do dado bruto. O Docling falhou silenciosamente em páginas com tabelas complexas, e o gap só foi detectado porque perguntas específicas do test set apontaram context_recall zero. Seções críticas não cobertas pelo test set poderiam permanecer ausentes indefinidamente.

**Metodologia:** auditoria baseada no sumário (TOC) extraído com pypdf dos dois PDFs grandes, cruzado com os cabeçalhos markdown (`##`, `###`) dos respectivos `.md` extraídos pelo Docling, seguida de verificação de presença de conteúdo clínico por busca de termos-chave.

**Relatório completo:** [`docs/audit_ingestion.md`](audit_ingestion.md)

---

#### Manual .md — Diagnóstico de Gaps

**PDF:** `Manual de Recomendações para o controle da Tuberculose no Brasil.pdf` (366 páginas)

**Estrutura do .md extraído:**

| Região do .md | Conteúdo | Status |
|---|---|---|
| Posições 0–50k | TOC (sumário em tabela markdown) | ✅ Completo |
| Posições 50k–120k | Parte I: Epidemiologia | ✅ Completo |
| Posições 120k–193k | Parte II: Diagnóstico | ✅ Completo |
| Posições 193k–210k | Parte III: somente seções 4.4.2–4.4.5 (Hepatopatias, Nefropatias, Diabetes, PVHIV) | ⚠️ Parcial |
| Posições 210k–289k | Parte IV–V: Estratégias Programáticas + Bases Organizacionais | ✅ Completo |
| Posições 289k–295k | Anexos (fichas SINAN, TDO) | ✅ Completo |

**Seções ausentes do corpo do .md (confirmado por busca de termos-chave):**

| Seção do PDF | Páginas PDF | Status no .md | Relevância para ILTB | Mitigação |
|---|---|---|---|---|
| Parte III, Seção 1–4.3: Introdução, Bases Farmacológicas, Escolha do Esquema, Esquema Básico (RHZE) | 97–111 | ❌ AUSENTE | Baixa (TB ativa, fora do escopo) | — |
| Parte III, 4.4.1 Gestação (TB ativa) | 111–112 | ❌ AUSENTE | Baixa (TB ativa) | PE questions covered by `recomendacoes-para-o-controle-da-tuberculose.md` |
| Parte III, Seção 5: Seguimento do Tratamento (TB ativa) | 122–126 | ❌ AUSENTE | Baixa (TB ativa) | — |
| Parte III, 6.1 Reações Adversas ao Esquema Básico | 127–129 | ❌ AUSENTE | **Média** (EA questions) | piridoxina/neuropatia presente em `recomendacoes.md` + `patch_interacoes.md` |
| Parte III, 6.2 Reações Adversas com ARV | 135–136 | ❌ AUSENTE | Baixa | Referências parciais presentes |
| **Parte III, 6.3 Interações Medicamentosas** | **137–141** | **✅ PATCHEADO** | **Alta** | `patch_interacoes_medicamentosas.md` |
| Parte III, Seção 7: TB Drogarresistente | 142–161 | Parcial | Muito baixa (fora do escopo) | — |
| **Parte III, Seção 8: Tratamento da ILTB** | **163–169** | **❌ AUSENTE** | **Alta** | `recomendacoes-para-o-controle-da-tuberculose.md` + docs especializados (ver abaixo) |

**Nota sobre a Seção 8 (ILTB):** a ausência é inesperada — as páginas 163–169 estão antes do limiar de `std::bad_alloc` identificado (página 319+). A causa provável é que o Docling falhou em partes intermediárias do documento (possível página com figura complexa) e pulou essas seções no modo de fallback.

**Verificação de qualidade — tabelas nas seções presentes:**
- **Seção 4.4.2 Hepatopatias (pos 193k):** Quadro 24 (condutas frente a hepatopatias) — tabela markdown ✅, TGO/TGP ≥ 5× LSN presente ✅
- **Seção 4.4.3 Nefropatias:** Quadro 25 (cálculo clearance) — presente ✅
- **Seção 4.4.5 PVHIV:** Quadro 26 (rifabutina com IP) — presente ✅
- **Seção 8.1.2 Escore pediátrico:** Quadro 11 — presente ✅

---

#### Auditoria da Cobertura por Outras Fontes

**`recomendacoes-para-o-controle-da-tuberculose.md`** (71K chars — documento principal ILTB da atenção básica):

| Conteúdo | Presente |
|---|---|
| Isoniazida dose (5–10 mg/kg, máx 300mg/dia) | ✅ |
| piridoxina 50 mg/dia para neuropatia | ✅ |
| neuropatia periférica | ✅ |
| gestantes + ILTB | ✅ (7 ocorrências) |
| PVHIV / CD4 / antirretroviral | ✅ (12 ocorrências) |
| PPD / IGRA | ✅ (9 ocorrências) |
| imunossupressores / anti-TNF | ✅ (3 ocorrências) |
| suspensão do tratamento | ✅ (5 ocorrências) |
| hepatotoxicidade | ✅ |
| 3HP (rifapentina) | ✅ |
| 6H / 9H | ❌ (presentes em `af_protocolo_vigilancia_iltb` e `GEDIIB`) |
| 26 Quadros clínicos | ✅ |

**Conclusão:** `recomendacoes-para-o-controle-da-tuberculose.md` cobre a grande maioria do conteúdo clínico necessário para o escopo ILTB, incluindo os itens críticos ausentes do Manual .md. A ausência de "6H/9H" é compensada por `af_protocolo_vigilancia_iltb_2ed_9jun22_ok_web.md` e `GEDIIB_TratamentoTuberculose.md`.

---

#### OMS Módulo 4 — Diagnóstico de Gaps

**PDF:** `9789275728185_por.pdf` (84 páginas — Manual Operacional OMS sobre Atenção e Apoio ao Tratamento)

**Escopo do documento:** atenção centrada na pessoa, suporte social, adesão, modelos de cuidado, cuidados paliativos — **NÃO é documento de protocolo clínico**. Ausência de tabelas de posologia é esperada e não constitui gap.

**Resultado:** todos os 6 capítulos do TOC têm cabeçalhos correspondentes no `.md`. Conteúdo de apoio (tabelas de comunicação, checklists, modelos de cuidado) presente. **Sem gaps identificados.**

---

#### Resumo Executivo

| Documento | Seções no TOC | Presentes no .md | Ausentes | Gaps críticos para ILTB |
|---|---|---|---|---|
| Manual .md | ~80 seções (Parts I–V) | ~65 | ~15 (concentradas em Parte III 4.1–8) | **Seção 8 ILTB** (mitigado), **6.3** (patcheado) |
| OMS Módulo 4 .md | 25 seções | 25 | 0 | Nenhum |

**Gaps identificados que requerem ação:**

| # | Gap | Criticidade | Ação |
|---|---|---|---|
| 1 | Seção 6.3 Interações Medicamentosas (Manual) | Alta | ✅ **Já patcheado** em `patch_interacoes_medicamentosas.md` |
| 2 | Seção 8 Tratamento ILTB (Manual) | Alta | ✅ **Mitigado** por `recomendacoes-para-o-controle-da-tuberculose.md` + docs especializados |
| 3 | Seção 6.1 Reações Adversas (Manual) | Média | ✅ **Mitigado** por piridoxina no `patch_interacoes.md` + `recomendacoes.md` |

**Conclusão:** nenhum patch adicional necessário. A base de dados está suficientemente completa para o escopo ILTB. As questões do test set (EA, MO, PE, IT, ET, IM, DI) têm conteúdo de suporte nas fontes indexadas.

**Decisão de design 📌:** A validação de integridade da base de dados é uma etapa obrigatória do pipeline de ingestão. Em contexto clínico, dado ausente é dado perigoso — o sistema responde com confiança usando informação incompleta. A extração automatizada (Docling) deve ser sempre seguida de auditoria contra o sumário do documento fonte.

---

#### Revisão Manual do OMS .md — Problemas Estruturais (pós-auditoria automatizada)

**Data:** 2026-03-22

A auditoria automatizada (cruzamento TOC × cabeçalhos) verificou completude mas não qualidade do conteúdo. A revisão manual bloco-a-bloco do `9789275728185_por.md` revelou 10 categorias de problemas que a automação não detecta:

| # | Problema | Impacto no RAG | Frequência |
|---|---|---|---|
| 1 | Bullets duplos (`- -`) | Markdown inválido, tokens desperdiçados | ~30 ocorrências |
| 2 | Listas fragmentadas (parágrafos entre itens numerados) | Chunks órfãos, perda de contexto sequencial | ~15 ocorrências |
| 3 | Cabeçalhos de tabela ausentes (dados usados como header) | Modelo confunde dado com metadado | 3 tabelas |
| 4 | Tabelas de coluna única (listas disfarçadas) | Categorias misturadas, contaminação semântica | 2 tabelas |
| 5 | Tabelas com bullets esmagados (`•` na mesma linha) | Perda de separação entre itens clínicos | 2 tabelas |
| 6 | Recomendações OMS com nível de evidência órfão | LLM responde sem informar força da evidência | ~5 ocorrências |
| 7 | Cabeçalhos falsos no meio de listas (`## Alguns exemplos`) | Chunker corta lista ao meio | ~3 ocorrências |
| 8 | Hierarquia achatada (todos `##`, sem `###`/`####`) | Chunker não distingue capítulo de subseção | 112 cabeçalhos |
| 9 | Artefatos de OCR (`Î`, `T abela`, `HIV ,`, `ajudálos`) | Poluição visual na resposta ao usuário | ~50 ocorrências |
| 10 | Notas de rodapé explicativas órfãs | Informação normativa separada do contexto | ~5 ocorrências |

**Decisão 📌 — Pipeline de sanitização em duas camadas:**

Camada 1 (automática): função `sanitize_markdown()` em `app/scripts/extract_pdfs.py` aplica regex para artefatos de OCR (`Î`, `T abela`, bullets duplos, espaços de layout). Executada automaticamente a cada extração.

Camada 2 (manual): engenheiro revisa estrutura de tabelas, hierarquia de cabeçalhos e continuidade de listas. Executada uma vez por documento; os `.md` corrigidos são versionados no git.

A Camada 1 resolve ~40% dos problemas; os 60% restantes são estruturais e exigem intervenção humana informada pelo domínio clínico.

**Resultado da sanitização do OMS .md:**

| Métrica | Antes | Depois |
|---|---|---|
| Linhas totais | 1.422 | 1.174 |
| Cabeçalhos `##` (capítulos) | 112 (todos) | 7 (corretos) |
| Cabeçalhos `###` (subseções) | 0 | 22 |
| Cabeçalhos `####` (sub-subseções) | 0 | 57 |
| Artefatos `Î ` | 76 | 0 |
| Ocorrências `T abela` | 8 | 0 |
| Tags `<!-- image -->` | 4 | 0 |
| Bloco editorial (TOC, copyright, Referências) | presente | removido |

**Tempo investido:** ~3 horas para o documento OMS (84 páginas, 1.421 linhas).

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

**Decisão 📌 (2026-03-21):** movido para Fase 4. O webhook exige HTTPS público com certificado válido — não faz sentido desenvolver antes de ter VPS + Nginx + Certbot rodando. Testar localmente com ngrok é possível mas adiciona complexidade desnecessária para o TCC.

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

**Limitação da CX22:** 4 GB RAM pode ser insuficiente para Docling processar PDFs grandes (ver seção 2.2). Mitigação: pré-processar PDFs localmente (implementado na seção 2.6).

---

## PENDÊNCIAS POR FASE

### Fase 2 (Engenharia de Dados) — quase completa

- [x] **Pré-processar PDFs → `.md` localmente e commitar**: implementado na seção 2.6 — `app/scripts/extract_pdfs.py` + `_resolve_files()` no indexer
- [x] **Fallback por score baixo**: implementado na seção 2.5.2 — filtro por `retriever_score_threshold` + mensagem de fallback HTTP 200
- [x] **Pipeline RAGAS — execução válida com juiz gpt-4o-mini**: avaliação completa (38/38 amostras) concluída — ver seção 2.10
- [x] **Threshold ajustado para 0.40**: 4 perguntas de interações medicamentosas e diagnóstico excluídas com threshold 0.50; corrigido para 0.40 — ver seção 2.10
- [ ] **Gate RAGAS — tuning necessário**: faithfulness 0.375 (alvo 0.80), context_precision 0.548 (alvo 0.75). Contextual chunking descartado (seção 2.11). Ground truths corrigidos em ET-07, PE-07 e IM-03 (seções 2.12–2.13). Patch da seção 6.3 criado e indexado (seção 2.13). Re-run aguardando reset do TPD do Groq (~24h). Próximo passo: `python -m eval.run_ragas` após reset do TPD

### Fase 3 (Backend) — parcialmente completa

- [ ] **Session manager**: histórico de conversa em memória (dict por `session_id`)

### Fase 4 (Piloto Hetzner) — próxima

- [ ] **Segurança Docker + UFW**: bind de portas em `127.0.0.1` no docker-compose.yml — Docker ignora UFW via iptables direto ✅ corrigido em `infra/docker-compose.yml`
- [ ] **Provisionar CX22**: criar conta Hetzner, provisionar servidor Ubuntu 22.04
- [ ] **UFW firewall**: liberar apenas 22 (SSH), 80 (HTTP→HTTPS redirect), 443 (HTTPS)
- [ ] **Nginx + Certbot**: HTTPS obrigatório para webhook Meta
- [ ] **Clonar repo + `docker-compose up`**: deploy inicial
- [ ] **Webhook Meta/WhatsApp**: implementar após Nginx + Certbot estarem rodando (Meta exige HTTPS público para verificação)
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

7. **Revisar código antes de avançar para avaliação formal.** Anti-padrões como embedding duplicado em RAM, filtro de score não implementado e client LLM reinstanciado a cada chamada são invisíveis em testes manuais, mas impactam produção. Uma revisão estruturada (seção 2.5) identificou 6 problemas que teriam complicado o deploy.

8. **Pré-extrair PDFs para Markdown e versionar os `.md`.** Elimina a dependência de Docling (~2 GB de modelos ML) no container de produção, resolve o problema de RAM na VPS e torna o pipeline de ingestão determinístico — o indexer só faz chunking + indexação, sem extração.

9. **Rate limits de APIs gratuitas são um bloqueio real em avaliação.** O Groq free tier (1.5K calls/24h) é suficiente para desenvolvimento e piloto, mas insuficiente para rodar RAGAS (pipeline RAG + LLM juiz = ~190 chamadas). Solução: flag `--scores-only` para separar as duas fases e minimizar chamadas desperdiçadas.

10. **Ground truths devem vir dos documentos reais, não de paráfrases.** Extrair literalmente dos `.md` gerados pelos PDFs do MS garante que o RAGAS avalia contra a fonte primária, não contra interpretações. Isso será importante na defesa do TCC.

11. **Testar a integração com frameworks externos antes de rodar a avaliação completa.** O RAGAS falhou em quatro pontos independentes em execuções consecutivas: API `.get()`, retorno de lista vs float, `nan` não filtrado por `is not None`, e encoding CP1252. Um teste com 2–3 perguntas teria revelado todos sem gastar o TPD diário.

12. **`float('nan')` não é `None` em Python.** Em contextos numéricos com APIs externas que retornam `nan` para jobs falhados, sempre filtrar explicitamente com `math.isnan()`. O filtro `v is not None` é insuficiente.

13. **100k tokens/dia do Groq free tier é insuficiente para pipeline RAG + RAGAS juntos.** 38 perguntas (pipeline) + 152 jobs (avaliação) = ~190 chamadas ao LLM que consomem ~90-100k tokens. Com qualquer re-execução no mesmo dia, o limite é esgotado. Solução definitiva: usar o `--scores-only` em dia separado do pipeline RAG, ou migrar o LLM juiz do RAGAS para OpenAI gpt-4o-mini em produção.

14. **TPM (tokens por minuto) é o limitador real no Groq free tier, não o TPD.** Ambos os modelos (70b e 8b) têm o mesmo limite de 6.000 tokens/minuto. Com processamento concorrente (`max_workers > 1`), o burst de requisições paralelas ultrapassa o TPM mesmo quando o TPD ainda tem margem. Solução: `max_workers=1` (sequencial) + `--max-questions 12` para manter ~200 tokens/min médio.

15. **Modelo LLM menor como juiz RAGAS pode subestimar faithfulness.** O `llama-3.1-8b-instant` retornou faithfulness 0.389, um valor que parece baixo para um pipeline que respondeu 12/12 perguntas corretamente na validação manual. O modelo 8b tem dificuldade em raciocinar sobre alinhamento entre afirmação e contexto — tarefa que exige capacidade de raciocínio mais avançada. Para o gate definitivo do TCC, usar gpt-4o-mini ou outro modelo mais capaz como juiz.

16. **Score threshold muito alto exclui perguntas legítimas de terminologia técnica.** O threshold de 0.50 é adequado para perguntas sobre esquemas terapêuticos (score ~0.75), mas muito restritivo para interações medicamentosas e diagnóstico (score ~0.44–0.48). A terminologia clínica específica (nomes de fármacos, siglas de exames) tem menor similaridade vetorial que termos mais gerais. Para avaliação completa, 0.40 é mais adequado.

17. **Gemini free tier na prática é inadequado para RAGAS.** A chave do AI Studio acessa `gemini-3-flash-preview` (20 req/dia), enquanto modelos estáveis (`gemini-2.0-flash`, `gemini-2.0-flash-lite`) têm `quota: 0` em contas sem histórico de uso. Para qualquer avaliação com mais de ~5 jobs, o free tier Gemini é bloqueador. OpenAI gpt-4o-mini (~$0,05 para o RAGAS completo) é a alternativa viável e definitiva.

18. **Contextual chunking prejudica modelos de embedding com poucas dimensões.** Prefixar chunks com hierarquia de títulos (`## Seção > ### Subseção`) dilui embeddings de modelos com 384 dimensões (MiniLM-L12). O vetor resultante mistura semântica estrutural com semântica clínica, reduzindo a precisão da busca. A técnica funciona bem com modelos de alta dimensionalidade (≥ 1536D) como `text-embedding-3-large`. Para este pipeline, o chunker semântico por cabeçalhos sem prefixo é superior.

19. **Verificar ground truths contra os documentos indexados antes de culpar o retriever.** A hipótese de "ground truths muito longos causando baixo context_recall" foi refutada na seção 2.12 — os ground truths já eram concisamente formatados (13-66 palavras). A causa real foi outra: alguns ground truths referenciam conteúdo não extraído na indexação (seção 6.3 do Manual de Recomendações — tabelas de interações medicamentosas), e outros tinham source_document incorreto. Verificar se o conteúdo do ground truth está nos chunks indexados é o primeiro passo de diagnóstico, antes de investir em refatoração.

20. **Embedding local é decisão de segurança, não apenas de conveniência.** Apesar de limitar técnicas avançadas como contextual chunking, o modelo `MiniLM-L12-v2` local garante que queries clínicas das enfermeiras não saem da infraestrutura controlada antes da busca vetorial — requisito de conformidade com LGPD em contexto hospitalar. Modelos via API (OpenAI, Cohere) exigiriam anonimização prévia das queries, adicionando complexidade e ponto de falha. Migração para modelo local de maior dimensionalidade (`multilingual-e5-base`, 768D) mapeada para Fase 5.

---

22. **Avaliação automatizada (RAGAS) não substitui governança de dados.** O RAGAS mede a qualidade do pipeline RAG assumindo que a base de dados está completa. Se o extrator de PDF falhar silenciosamente em seções críticas (tabelas, imagens, páginas com alta complexidade visual), o RAGAS não detecta o gap — apenas reporta scores baixos sem identificar a causa raiz. Auditoria proativa da base (cruzamento sumário TOC vs. cabeçalhos extraídos + verificação de qualidade de tabelas em seções críticas) é etapa obrigatória antes da avaliação formal. A auditoria da seção 2.14 revelou que a Seção 8 inteira (Tratamento da ILTB, páginas 163–169) estava ausente do Manual .md — um gap que o RAGAS sozinho nunca teria identificado sem questões específicas cobrindo esse conteúdo.

21. **Groq TPD (tokens por dia) é o limitador em múltiplas re-execuções.** O free tier do Groq tem limite de 100.000 tokens/dia para modelos 70B. Com prompts de ~1.500 tokens, são apenas ~66 chamadas por dia. Runs que falham por TPM ainda consomem parte do orçamento diário. Após 2 runs falhos no mesmo dia, o TPD se esgota. Estratégia: monitorar tokens usados antes de iniciar o pipeline, ou usar o Groq apenas em dia com orçamento limpo.

23. **Auditoria automatizada de .md não substitui revisão manual estrutural.** O cruzamento TOC × cabeçalhos detecta seções ausentes, mas não detecta: tabelas partidas por quebra de página, listas com itens fragmentados, categorias misturadas em tabelas de coluna única, hierarquia de cabeçalhos achatada, ou bullets esmagados em células de tabela. Para documentos clínicos destinados a RAG, a revisão manual bloco-a-bloco é obrigatória após a extração automatizada.

24. **Sumários, índices e referências bibliográficas nunca devem ser indexados em RAG.** Sumários contêm metadados de navegação (títulos + números de página), não conhecimento clínico. Se indexados, o retriever retorna "veja página 53" em vez da resposta clínica. Referências bibliográficas poluem o contexto com nomes de autores e datas sem utilidade para o LLM. Ambos devem ser removidos do .md antes da indexação.

25. **Tabelas de coluna única em PDFs são listas disfarçadas.** Quando o Docling extrai tabelas que no PDF original eram listas visuais (ex: lista de medicamentos com bordas), ele gera tabelas markdown de uma coluna. Se categorias diferentes aparecem como linhas da mesma tabela (ex: "Equipamento" seguido de "Apoios sociais" na mesma grade), o modelo de embedding associa todos os itens à primeira categoria. Solução: converter para texto hierárquico com cabeçalhos separados por categoria.

26. **Recomendações da OMS devem manter o nível de evidência colado ao texto.** Quando o Docling fragmenta um item de lista e o metadado "(recomendação condicional, evidências de certeza muito baixa)" fica em parágrafo separado, o chunker pode separá-los. Em contexto clínico, orientar uma conduta sem informar a força da evidência é perigoso. O nível de evidência deve estar na mesma linha/bullet que a recomendação.

---

*Última atualização: 2026-03-22 (sanitização manual OMS .md + função sanitize_markdown() + lições 23–26 — seção 2.14 expandida)*