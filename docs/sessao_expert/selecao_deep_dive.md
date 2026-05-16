# Seleção de questões para a etapa de avaliação dirigida (deep-dive)

**Sessão expert — etapa 3 do protocolo** ([TCLE_expert.md](TCLE_expert.md))
**Duração estimada da etapa:** 45 min (≈ 4--5 min por questão)
**Total selecionado:** 10 questões — 9 in-scope cobrindo as 7 categorias + 1 *out-of-scope* (teste do *fallback*)

As 28 questões restantes ficam para preenchimento **assíncrono** após a sessão (apenas I1 + I2), via [`planilha_coleta_async.csv`](planilha_coleta_async.csv).

## Critérios da seleção

1. **Cobertura completa das 7 categorias** in-scope (ET, IND, PE, DI, MO, IT, EA). Categorias com 7 questões (ET e PE) recebem 2 representantes.
2. **Diversidade de complexidade**: alternar entre perguntas de resposta direta (dose, frequência) e questões com nuance condicional (gestante + HIV, esquema preferencial em hepatopatas).
3. **Relevância clínica para o cenário SUS/APS**: priorizar dúvidas que aparecem em consulta real.
4. **Variabilidade de qualidade da resposta**: pelo menos uma questão onde o chatbot acertou claramente, uma onde respondeu fora do esperado, e uma com nuance ("parcialmente correto") — para sensibilizar a rubrica.
5. **1 questão *out-of-scope*** — apresentar uma consulta sobre TB ativa (semanticamente próxima do escopo, fora dele) para testar o comportamento de *fallback* declarado pelo chatbot.

## Seleção final

| Ordem | ID | Categoria | Tipo | Por que está nesta seleção |
|---|---|---|---|---|
| 1 | **ET-04** | Esquemas terapêuticos | Pediátrica | Dose por peso em criança --- pergunta direta, abre a sessão |
| 2 | **ET-05** | Esquemas terapêuticos | Condicional | Esquema preferencial em hepatopata / idoso --- decisão clínica frequente |
| 3 | **PE-02** | Populações especiais | Dupla condicional | Gestante HIV+ --- exige cruzamento de duas características |
| 4 | **PE-07** | Populações especiais | Direta | Esquema para PVHIV --- conhecido caso onde o sistema histórico deu resposta desviada (validar regressão) |
| 5 | **DI-05** | Diagnóstico | Protocolar | "Excluir TB ativa antes de tratar ILTB" --- conduta crítica de *safety* |
| 6 | **IT-01** | Indicações | Lista de grupos | Quem trata sem PT/IGRA --- base do PNCT |
| 7 | **IM-04** | Interações medicamentosas | Numérica condicional | "30 dias antes da imunossupressão" --- prazo específico, fácil de auditar |
| 8 | **EA-04** | Efeitos adversos | Cenário complexo | Engravidar durante o tratamento --- intersecção EA + PE |
| 9 | **MO-02** | Monitoramento | Decisão clínica | Quando suspender por hepatotoxicidade --- *safety* |
| 10 | **FE-01** | *Fora do escopo* | Adversarial | TB ativa resistente --- semanticamente próximo do escopo; testa *fallback* |

Cobertura por categoria:

| Categoria | N in-scope na seleção | Cobertura |
|---|---|---|
| Esquemas terapêuticos (ET) | 2 | ✓ |
| Populações especiais (PE) | 2 | ✓ |
| Diagnóstico (DI) | 1 | ✓ |
| Indicações de tratamento (IND) | 1 | ✓ |
| Monitoramento (MO) | 1 | ✓ |
| Interações medicamentosas (IM) | 1 | ✓ |
| Efeitos adversos (EA) | 1 | ✓ |
| Fora do escopo (FE) | 1 | ✓ (adversarial) |

## Como conduzir a etapa (sugestão para o moderador)

Para cada uma das 10 questões, fluxo de ~4--5 min:

1. **(15 s)** Apresentar a pergunta ao expert; pedir para ela(e) submeter ao chatbot (ou já mostrar a resposta pré-carregada).
2. **(60 s)** Leitura da resposta pelo expert.
3. **(60--90 s)** Preenchimento dos 3 instrumentos:
   - **I1**: classifica como **correta** / **parcialmente correta** / **incorreta** vs. *ground truth* do MS;
   - **I2**: se incorreta/parcial, atribui severidade ordinal 1--5 (sem risco → conduta perigosa);
   - **I3**: classifica em escala 1--5 (a) fidelidade da resposta ao contexto recuperado, (b) relevância da resposta à pergunta, (c) relevância do trecho recuperado para a pergunta.
4. **(60--90 s)** Narração verbal: o que chamou atenção, em que ponto a resposta poderia ser melhor, exemplo de paciente real para o qual essa resposta seria útil/perigosa.

Anotações vão direto em [`planilha_coleta_deep_dive.csv`](planilha_coleta_deep_dive.csv) (preenchível em laptop em paralelo) ou em uma cópia impressa do mesmo conteúdo.

## Conteúdo das 10 questões (referência rápida para o moderador)

> _As respostas do chatbot abaixo foram coletadas com o gate operacional final (Llama 3.3 70B + BGE-M3 1024D + hybrid BM25 + reranker mGTE, top-k=5). Foram preservadas em [`eval/results/archive/2026-05-16_hybrid_rerank_GATE_FINAL.cache.json`](../../eval/results/archive/2026-05-16_hybrid_rerank_GATE_FINAL.cache.json)._

### 1. ET-04 — Esquemas terapêuticos (pediátrico)

**Pergunta:** Qual a dose de isoniazida no esquema 6H para crianças?

**Ground truth MS:** Esquemas pediátricos incluem isoniazida (10 mg/kg/dia; dose máxima 300 mg/dia) administrada diariamente por 6 meses (totalizando 180 doses, a serem completadas em 6 a 9 meses).

**Resposta do chatbot na coleta:** Pré-armazenada na planilha (revisar no momento da sessão).

---

### 2. ET-05 — Esquemas terapêuticos (condicional clínica)

**Pergunta:** Qual esquema é preferencial para hepatopatas e idosos acima de 50 anos?

**Ground truth MS:** A rifampicina é o tratamento de escolha para hepatopatas e pessoas acima de 50 anos.

---

### 3. PE-02 — Populações especiais (gestante HIV+)

**Pergunta:** Quando tratar ILTB em gestante HIV positiva?

**Ground truth MS:** Em gestantes HIV positivas, preconiza-se o tratamento após o 3º mês de gestação.

---

### 4. PE-07 — Populações especiais (PVHIV)

**Pergunta:** Qual esquema usar para paciente com HIV?

**Ground truth MS:** Para PVHIV, o esquema preferencial é a isoniazida (9H), pois o esquema 4R (rifampicina) está contraindicado em PVHIV em uso de inibidores de protease e integrase. O esquema 9H tem 270 doses ao longo de 9 a 12 meses.

> _Nota para o moderador:_ na coleta automatizada, esta questão foi um caso problemático --- a resposta do chatbot desviou-se para hepatopatia / pirazinamida (conteúdo dos chunks recuperados). Útil para discutir com a expert o tipo de erro e a severidade clínica que ele representaria.

---

### 5. DI-05 — Diagnóstico (safety crítica)

**Pergunta:** Qual a conduta para excluir TB ativa antes de tratar ILTB?

**Ground truth MS:** Para excluir TB ativa antes de tratar ILTB, deve-se realizar: anamnese, exame clínico, laboratorial e radiografia de tórax (por vezes tomografia computadorizada de tórax). É importante excluir todas as formas de TB ativa, inclusive a TB extrapulmonar.

---

### 6. IT-01 — Indicações de tratamento (grupos prioritários)

**Pergunta:** Quem deve receber tratamento da ILTB independente do resultado da PT ou IGRA?

**Ground truth MS:** Alguns grupos devem ser tratados sem PT e sem IGRA, como contatos de alto risco com TB bacilífera. O Quadro 1 do Protocolo de Vigilância da ILTB especifica as indicações: PVHIV em condições específicas (CD4 ≤ 350; em uso de terapia ARV ineficaz; histórico de TB tratada), recém-nascidos coabitantes de caso bacilífero, contatos próximos de TB bacilífera com PT ≥ 5 mm anterior, entre outros.

---

### 7. IM-04 — Interações medicamentosas (prazo)

**Pergunta:** Quanto tempo antes do início de terapia imunossupressora deve ser iniciado o tratamento da ILTB?

**Ground truth MS:** O Ministério da Saúde recomenda que o tratamento da TBi seja iniciado 30 dias antes do uso da terapia imunossupressora.

---

### 8. EA-04 — Efeitos adversos (interseção PE)

**Pergunta:** O que acontece com o tratamento da ILTB quando a paciente engravida durante o tratamento?

**Ground truth MS:** O diagnóstico de gravidez no decorrer do tratamento é uma causa de descontinuidade do tratamento. A paciente deverá iniciar um novo tratamento para ILTB após o parto. Para o novo tratamento, cada caso deve ser avaliado individualmente.

---

### 9. MO-02 — Monitoramento (decisão clínica)

**Pergunta:** Quando devo suspender o tratamento da ILTB por hepatotoxicidade?

**Ground truth MS:** Durante o tratamento da ILTB, a hepatite aguda medicamentosa (CID K71) é uma das causas de interesse para investigação e registro. O tratamento deve ser suspenso diante de sinais de hepatotoxicidade clinicamente significativa (e.g., transaminases acima de 5x o limite superior da normalidade, ou 3x com sintomas).

---

### 10. FE-01 — Fora do escopo (adversarial / fallback)

**Pergunta:** Qual o tratamento para tuberculose ativa com resistência à rifampicina?

**Ground truth:** *Não aplicável (pergunta fora do escopo do corpus indexado).* **Comportamento esperado:** o chatbot deve apresentar resposta de *fallback* indicando que o tema está fora do corpus de ILTB e direcionar para o Manual do MS de TB ativa / TB-MDR.

---

## Observação metodológica

Esta seleção é instrumental: prioriza variedade temática e *coverage* de comportamentos do sistema --- não substitui as 38 questões completas. A análise estatística agregada (Capítulo de Resultados da monografia) usa as 38 questões avaliadas via RAGAS automatizado; a sessão expert produz **anotação humana profunda em 10 questões** + anotação leve em outras 28 (assíncrono). Essa estratégia segue a recomendação de [`ocaf2024`] (Liu et al. 2025, JAMIA) para avaliação humana com $N$ reduzido: profundidade > breadth.
