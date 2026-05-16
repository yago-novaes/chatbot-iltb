# Revisão das Decisões D1–D13 via NotebookLM

**Objetivo:** submeter cada uma das 13 decisões técnicas a três perguntas estruturadas no NotebookLM (com as 19 fontes originais + papers acrescentados em `referencias.bib`) para:

- (a) **Validar** o embasamento bibliográfico atual.
- (b) **Identificar lacunas** — o que ainda falta citar / aprofundar.
- (c) **Reconsiderar** — há alternativa mais bem embasada nas fontes que valha repensar a decisão?

**Como usar:**

1. Copie o bloco de uma decisão por vez para o NotebookLM.
2. Anote a síntese (3–5 linhas) na coluna `Síntese NotebookLM` do diário técnico (seção 2.28, a criar).
3. Marque a decisão como `[VALIDADA]`, `[GAP CONFIRMADO]` ou `[REVISITAR]`.

**Notas de escopo (maio/2026):**

- Piloto com 5 enfermeiras foi substituído por avaliação com 1 expert → D10 e D12 precisam ser re-justificadas sob esse novo formato.
- VPS / WhatsApp foram cancelados → D7 (LGPD) muda de "conformidade em produção" para "boa prática local de tratamento de dados sensíveis".

---

## D1 — Arquitetura RAG

**Decisão:** adotar arquitetura RAG (recuperação + geração) em vez de LLM puro ou fine-tuning.
**Embasamento atual:** lewis2021, gao2024, bang2023 — status **Forte**.

**Perguntas ao NotebookLM:**

1. *Validação:* "Os artigos disponíveis sustentam a escolha de arquitetura RAG (recuperação + geração) sobre fine-tuning de LLM para tarefas de pergunta-resposta sobre protocolos clínicos específicos? Cite os trechos principais que sustentam essa preferência em domínios de baixa frequência terminológica."
2. *Lacuna:* "Há nas fontes alguma comparação empírica direta entre RAG e fine-tuning para corpora pequenos (centenas a milhares de chunks) em domínio médico? Se sim, quais as métricas reportadas?"
3. *Reconsiderar:* "Existem nas fontes argumentos para preferir RAFT (Retrieval-Augmented Fine-Tuning) ou outras arquiteturas híbridas em vez de Naive RAG para o cenário deste TCC (corpus pequeno, domínio médico em português, sem rotulagem)?"

---

## D2 — Embedding: paraphrase-multilingual-MiniLM-L12-v2

**Decisão:** usar MiniLM multilíngue de 384D para indexação semântica.
**Embasamento atual:** reimers2019, boykis2024 — status **Parcial**.
**Acrescentado em referencias.bib:** adaptingLLMsPortuguese2024, generalistEmbeddingsClinical2024, mmteb2025, biobertpt2020.

**Perguntas ao NotebookLM:**

1. *Validação:* "Algum dos artigos avalia especificamente modelos da família SBERT/MiniLM (especialmente o paraphrase-multilingual-MiniLM-L12-v2) para tarefas de recuperação em português ou em textos médicos? Há benchmark publicado?"
2. *Lacuna:* "As fontes mencionam embeddings de maior dimensionalidade (768D, 1024D ou 1536D — e.g., multilingual-e5-base, BGE-M3, text-embedding-3-large) com superioridade documentada sobre MiniLM 384D em domínio clínico ou em português? Quais ganhos quantitativos são reportados?"
3. *Reconsiderar:* "Há nas fontes evidência de que embeddings biomédicos especializados em português (BioBERTpt, PubMedBERT-pt) superem embeddings multilíngues genéricos para recuperação de protocolos clínicos? Vale considerar migração antes da Fase 5?"

---

## D3 — Vector Store: ChromaDB (HNSW)

**Decisão:** usar ChromaDB embarcado, com HNSW como algoritmo ANN.
**Embasamento atual:** malkov2016 (indireto, via HNSW) — status **Parcial**.

**Perguntas ao NotebookLM:**

1. *Validação:* "Os artigos sustentam o uso do HNSW para busca aproximada de vizinhos mais próximos em corpora pequenos (< 10k chunks)? Cite trechos que justifiquem a escolha por critérios de complexidade computacional e robustez."
2. *Lacuna:* "Há comparações nas fontes entre ChromaDB, FAISS, Qdrant ou Pinecone em termos de latência, recall ou facilidade de operação para POCs acadêmicos? Se não, qual o critério recomendado para essa escolha?"
3. *Reconsiderar:* "Para um corpus de 898 chunks e demo via FastAPI+ngrok (sem servidor dedicado), as fontes apontam alguma alternativa mais leve ou mais adequada que ChromaDB? Indexação em memória pura seria suficiente?"

---

## D4 — LLM: Llama 3.3 70B via Groq

**Decisão:** usar Llama 3.3 70B com Groq como provedor de inferência.
**Embasamento atual:** dubey2024, brown2020, bang2023 — status **Adequado**.
**Acrescentado em referencias.bib:** sabia2_2024, teachingLLMsBrazil2026, llmsMedicalExam2026.

**Perguntas ao NotebookLM:**

1. *Validação:* "Os artigos disponíveis avaliam o desempenho do Llama 3.x (especialmente 70B) em tarefas de raciocínio em português ou em domínio médico? Há comparação com GPT-4 ou Claude em benchmarks clínicos?"
2. *Lacuna:* "Há nas fontes discussão sobre a tendência de modelos abstrativos (Llama, GPT) parafrasearem o contexto recuperado, penalizando métricas RAGAS baseadas em correspondência exata? Isso fundamenta o teto observado de faithfulness 0.515?"
3. *Reconsiderar:* "Os artigos sugerem LLMs alternativos mais adequados a respostas extrativas ou treinados em corpora médicos em português (e.g., Sabiá-2, Gemma médico, BioMistral) que justifiquem revisitar a escolha?"

---

## D5 — Chunking Semântico por Cabeçalhos Markdown

**Decisão:** chunking hierárquico por seções do documento, com buffering e subdivisão.
**Embasamento atual:** gao2024 — status **Parcial**.
**Acrescentado em referencias.bib:** advancedChunkingRAG2025.

**Perguntas ao NotebookLM:**

1. *Validação:* "As fontes sustentam que chunking semântico por fronteiras estruturais do documento (cabeçalhos, seções) supera chunking por tamanho fixo em corpora estruturados (como protocolos clínicos)? Há resultados quantitativos?"
2. *Lacuna:* "Há nas fontes comparações controladas entre Small-to-Big, Sliding Window, DenseX e índice hierárquico para recuperação em texto técnico estruturado? Qual estratégia tem o melhor trade-off recall/precisão?"
3. *Reconsiderar:* "O experimento de chunking contextual (prefixar chunks com hierarquia de cabeçalhos) reduziu RAGAS neste projeto. As fontes explicam essa falha como propriedade dos embeddings de baixa dimensionalidade? Isso já justifica a decisão por não reverter, ou é argumento para migrar embedding antes (D2)?"

---

## D6 — Framework de Avaliação: RAGAS

**Decisão:** usar RAGAS (faithfulness, answer_relevancy, context_precision, context_recall) como avaliador automatizado.
**Embasamento atual:** es2024 — status **Forte**.

**Perguntas ao NotebookLM:**

1. *Validação:* "Os artigos discutem RAGAS como o framework de referência para avaliação reference-free de RAG? Há crítica metodológica relevante (vieses do LLM juiz, sensibilidade a paráfrase, dependência do modelo avaliador)?"
2. *Lacuna:* "As fontes mencionam alternativas a RAGAS (TruLens, ARES, DeepEval, BEIR adaptado) que possam complementar a avaliação? Qual a posição na literatura sobre uso combinado?"
3. *Reconsiderar:* "Para um projeto que avançará para avaliação com 1 expert clínico (e não piloto de 30 dias com 5 enfermeiras), as fontes recomendam manter RAGAS como instrumento primário, ou priorizar avaliação humana qualitativa estruturada (e.g., rubrica de Lin et al., G-Eval)?"

---

## D7 — Conformidade LGPD (GAP CRÍTICO)

**Decisão:** manter pipeline de embeddings 100% local; queries não saem do servidor antes da busca.
**Embasamento atual:** nenhum dos 19 artigos originais — status **GAP CRÍTICO**.
**Acrescentado em referencias.bib:** privacyRAGHealthcare2025, sokPrivacyLLM2026, privacyEHRLLMs2025, lgpdSaude2023, lgpdEnfermagem2022.
**Mudança de escopo:** sem deploy em VPS, LGPD continua relevante como princípio de tratamento de dados sensíveis em ambiente local.

**Perguntas ao NotebookLM:**

1. *Validação:* "Algum dos artigos disponíveis fundamenta a escolha de embeddings locais sobre embeddings via API externa para dados clínicos? Os argumentos invocam LGPD, GDPR, HIPAA ou princípios gerais de proteção de dados?"
2. *Lacuna:* "Há nas fontes recomendações específicas para LGPD em sistemas de IA aplicados à saúde no Brasil (CFM, ANS, resoluções)? Sobre tratamento de dados sensíveis em prompts de LLM, há literatura sobre redação de informação sensível antes do envio ao LLM?"
3. *Reconsiderar:* "Mesmo sem deploy em produção (sem VPS, sem WhatsApp), a literatura sustenta que sessões de demo com expert e dados não-anonimizados exigem alguma mitigação adicional (Termo de Consentimento? Anonimização ex-ante?)? O que a literatura recomenda para POCs acadêmicas em saúde?"

---

## D8 — Metodologia DSRM

**Decisão:** estruturar o TCC pela Design Science Research Methodology (Peffers et al. 2007).
**Embasamento atual:** peffers2007 — status **Forte**.

**Perguntas ao NotebookLM:**

1. *Validação:* "Os artigos confirmam DSRM como metodologia padrão para TCCs/dissertações que desenvolvem artefatos computacionais? Há aderência ao formato 6-fases (identificação do problema, objetivos, design, demonstração, avaliação, comunicação) em trabalhos análogos da área de IA em saúde?"
2. *Lacuna:* "Existem alternativas metodológicas mais recentes (Action Design Research — ADR, ou DSRM revisado pós-2015) que as fontes recomendem em vez do DSRM clássico para sistemas baseados em IA?"
3. *Reconsiderar:* "Com a mudança de piloto (5 enfermeiras × 30 dias) para avaliação com 1 expert, a fase de 'Demonstração' do DSRM ainda é robustamente atendida, ou as fontes recomendam complementar com outro instrumento (estudo de caso, ATC — Action-Theoretical Case Study)?"

---

## D9 — Contexto Epidemiológico ILTB/TB

**Decisão:** justificar relevância clínica do problema com base em WHO, MS e literatura brasileira.
**Embasamento atual:** who2018, who2023, brasil2022, artigo_perfil — status **Forte**.

**Perguntas ao NotebookLM:**

1. *Validação:* "As fontes consolidam o argumento epidemiológico de que ILTB é etapa crítica para eliminação da TB ativa no Brasil? Os dados de incidência, prevalência e cobertura de tratamento são suficientes para uma seção de 'Justificativa' de TCC?"
2. *Lacuna:* "Há nas fontes literatura específica sobre barreiras operacionais no manejo da ILTB pela enfermagem brasileira (esquemas 6H, 3HP, 4R; rastreio em PVHIV; contactantes domiciliares)?"
3. *Reconsiderar:* "Os documentos da WHO/MS citados estão na versão mais recente disponível? Há atualização de protocolo posterior a brasil2022 que mudaria recomendações de primeira linha?"

---

## D10 — Público-Alvo (REVISITAR sob novo escopo)

**Decisão original:** chatbot voltado a enfermeiras da APS no SUS; piloto com 5 enfermeiras + SUS.
**Decisão revisada (maio/2026):** avaliação com 1 expert (enfermeiro/a especialista em ILTB) em sessão estruturada.
**Embasamento atual:** brooke1996 (SUS) — status **Parcial**.
**Acrescentado em referencias.bib:** nursingTAM2024, ocaf2024.

**Perguntas ao NotebookLM:**

1. *Validação:* "Algum dos artigos avalia percepção de enfermeiros sobre chatbots/LLMs como suporte à decisão clínica? Há modelos teóricos validados (TAM, UTAUT, OCAF) aplicados especificamente à enfermagem em saúde pública?"
2. *Lacuna:* "Sobre **avaliação com 1 expert** (em vez de piloto multi-usuário), as fontes recomendam instrumentos específicos (think-aloud protocol, heuristic evaluation Nielsen, cognitive walkthrough)? Qual estrutura de sessão é defensável metodologicamente para um TCC?"
3. *Reconsiderar:* "O System Usability Scale (SUS) faz sentido com N=1? Ou é preferível substituir por rubrica qualitativa (eficácia, segurança, alinhamento ao protocolo MS, riscos clínicos), conforme literatura de avaliação de IA em saúde?"

---

## D11 — Busca Híbrida como Trabalho Futuro

**Decisão:** registrar busca híbrida (RRF, SPLADE, ColBERT) como trabalho futuro pós-TCC.
**Embasamento atual:** cormack2009, formal2021, khattab2020 — status **Adequado**.

**Perguntas ao NotebookLM:**

1. *Validação:* "As fontes sustentam que busca híbrida (densa + esparsa) supera busca apenas densa em corpora com terminologia técnica de baixa frequência (siglas, nomes de fármacos)? Há ganho quantitativo reportado?"
2. *Lacuna:* "Entre RRF (simples, sem parâmetros), SPLADE (esparso neural) e ColBERT (interação tardia), qual a recomendação para corpora pequenos (< 1000 chunks) em português médico? Há comparações nas fontes?"
3. *Reconsiderar:* "Diante do encerramento da Fase 5 (sem VPS) e do gate de faithfulness não atingido, vale antecipar a implementação de busca híbrida ainda no escopo do TCC, ou mantê-la como trabalho futuro é decisão metodologicamente defensável?"

---

## D12 — Kappa de Cohen para Avaliação (REVISITAR sob novo escopo)

**Decisão original:** usar Kappa de Cohen para concordância entre as 5 enfermeiras do piloto.
**Decisão revisada (maio/2026):** com **N=1 expert**, Kappa inter-rater perde aplicabilidade direta.
**Embasamento atual:** landis1977 — status **Adequado para 2+ raters**.

**Perguntas ao NotebookLM:**

1. *Validação:* "Os artigos sustentam Kappa de Cohen como instrumento para concordância entre múltiplos avaliadores? Há requisitos mínimos de N para estabilidade do estimador?"
2. *Lacuna:* "Para avaliação com **1 expert único**, as fontes recomendam quais instrumentos quantitativos (concordância intra-avaliador via re-teste, percentual de acerto contra gabarito de referência, taxa de erro clínico)?"
3. *Reconsiderar:* "Vale **descartar Kappa** do TCC (já que não há piloto multi-rater) e substituir por: (a) rubrica clínica binária (correto/incorreto) contra ground truth do MS, (b) classificação de severidade de erros (Likert ou ordinal), (c) métricas mistas? Qual a abordagem mais bem fundamentada nas fontes?"

---

## D13 — LLMs em Contexto Clínico e Risco de Alucinação

**Decisão:** discutir risco de alucinação e propriedades de LLMs em saúde.
**Embasamento atual:** bang2023, brown2020 — status **Parcial**.
**Acrescentado em referencias.bib:** llmsMedicalExam2026, teachingLLMsBrazil2026, clinicalNERPortuguese2026, SHTI2023.

**Perguntas ao NotebookLM:**

1. *Validação:* "Os artigos discutem taxas e tipologia de alucinação em LLMs aplicados a domínio clínico? Há diferenciação entre alucinação de conteúdo (factual) e de citação (referência inventada)?"
2. *Lacuna:* "Há nas fontes evidência específica de degradação de LLMs em consultas clínicas em português comparadas ao inglês? E sobre LLMs especializados em saúde (Med-PaLM, Meditron, ClinicalGPT) — quais são as evidências de superioridade ou paridade contra LLMs generalistas via RAG?"
3. *Reconsiderar:* "Diante de faithfulness 0.515 e ausência de teste contra LLM clínico em português, as fontes sustentam ampliar a avaliação para incluir comparação contra um modelo de referência (e.g., GPT-4 + RAG, Sabiá-2-Med + RAG) como ablação metodológica antes da defesa?"

---

## Próximos passos após receber as sínteses

1. Para cada decisão, **classificar** em uma de três categorias:
   - `[VALIDADA]` — embasamento suficiente; pode escrever a seção da monografia.
   - `[GAP CONFIRMADO]` — buscar literatura adicional fora do NotebookLM (Google Scholar, papersflow MCP).
   - `[REVISITAR]` — alternativa documentada nas fontes que justifica reabrir a decisão; registrar nova ADR no diário.

2. Consolidar resultados em **nova seção do diário técnico** (proposta: seção 2.28 — "Revisão Bibliográfica D1–D13 via NotebookLM, maio/2026").

3. **Atualizar `referencias.bib`** com referências adicionais que o NotebookLM citar mas que ainda não estejam no arquivo.

4. **Reescrever as seções** do `relatorio_avanco.tex` (e, mais à frente, da monografia) para decisões que mudaram de status.
