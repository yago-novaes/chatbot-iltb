# Auditoria de Integridade da Base de Documentos

> **Data:** 2026-03-21
> **Escopo:** dois PDFs grandes — Manual do MS (366 págs.) e OMS Módulo 4 (84 págs.)
> **Método:** cruzamento TOC extraído via pypdf × cabeçalhos markdown do `.md` gerado pelo Docling + verificação de presença de conteúdo clínico por busca de termos-chave
> **Contexto:** Ver seção `2.14` do [diário técnico](diario-tecnico.md) para motivação e decisões associadas.

---

## 1. Manual de Recomendações para o Controle da Tuberculose no Brasil

**Arquivo:** `docs/protocolos/Manual de Recomendações para o controle da Tuberculose no Brasil.md`
**PDF fonte:** 366 páginas — 2ª edição atualizada, 2019, Ministério da Saúde

### 1.1 Estrutura do .md extraído

| Região (chars) | Conteúdo | Status |
|---|---|---|
| 0 – 50k | TOC (sumário convertido em tabela markdown) | ✅ Completo |
| 50k – 120k | Parte I: Aspectos Básicos e Epidemiológicos | ✅ Completo |
| 120k – 193k | Parte II: Diagnóstico (seções 1–9) | ✅ Completo |
| 193k – 210k | Parte III: **somente** seções 4.4.2–4.4.5 (Hepatopatias, Nefropatias, Diabetes, PVHIV) | ⚠️ Parcial |
| 210k – 289k | Partes IV–V: Estratégias Programáticas + Bases Organizacionais | ✅ Completo |
| 289k – 295k | Anexos (fichas SINAN, TDO) | ✅ Presente |

### 1.2 Seções da Parte III ausentes no .md

| Seção | Páginas PDF | Status | Relevância ILTB | Mitigação |
|---|---|---|---|---|
| 1–4.3 — Introdução, Bases Farmacológicas, Esquema Básico (RHZE) | 97–111 | ❌ AUSENTE | Baixa (TB ativa, fora do escopo) | — |
| 4.4.1 — Gestação (TB ativa) | 111–112 | ❌ AUSENTE | Baixa (TB ativa) | `recomendacoes-para-o-controle-da-tuberculose.md` |
| 5 — Seguimento do Tratamento (TB ativa) | 122–126 | ❌ AUSENTE | Baixa (TB ativa) | — |
| 6.1 — Reações Adversas ao Esquema Básico | 127–129 | ❌ AUSENTE | Média (EA questions) | piridoxina em `patch_interacoes.md` + `recomendacoes.md` |
| 6.2 — Reações Adversas com ARV | 135–136 | ❌ AUSENTE | Baixa | Referências parciais presentes |
| **6.3 — Interações Medicamentosas** | **137–141** | **✅ PATCHEADO** | **Alta** | `patch_interacoes_medicamentosas.md` |
| 7 — TB Drogarresistente | 142–161 | Parcial | Muito baixa (fora do escopo) | — |
| **8 — Tratamento da ILTB** | **163–169** | **❌ AUSENTE** | **Alta** | `recomendacoes-para-o-controle-da-tuberculose.md` + docs especializados |

> **Nota sobre a Seção 8:** a ausência é inesperada — as páginas 163–169 estão antes do limiar de `std::bad_alloc` documentado (página 319+). A causa provável é falha do Docling em página intermediária com figura complexa, pulando seções no modo de fallback de texto nativo.

### 1.3 Qualidade de tabelas nas seções presentes

| Seção | Quadro | Tipo de Conteúdo | Qualidade |
|---|---|---|---|
| 4.4.2 Hepatopatias | Quadro 24 | Condutas frente a hepatopatias (TGO/TGP × LSN) | ✅ Tabela markdown estruturada |
| 4.4.3 Nefropatias | Quadro 25 | Fórmula clearance de creatinina | ✅ Presente |
| 4.4.5 PVHIV | Quadro 26 | Rifabutina com inibidor de protease | ✅ Presente |
| 8.1.2 Diagnóstico pediátrico | Quadro 11 | Sistema de escore TB pediátrico | ✅ Presente |
| 10.3 SITE-TB | Quadros 52–54 | Tipos de entrada e encerramento | ✅ Presente |

---

## 2. OMS Módulo 4 — Atenção e Apoio ao Tratamento da TB

**Arquivo:** `docs/protocolos/9789275728185_por.md`
**PDF fonte:** 84 páginas — Manual Operacional OMS, tradução OPAS, 2024

### 2.1 Escopo do documento

Documento de **atenção centrada na pessoa**: suporte social, comunicação em saúde, tecnologias digitais de adesão, modelos de cuidado, cuidados paliativos. **Não é documento de protocolo clínico** — ausência de tabelas de posologia é esperada e não constitui gap.

### 2.2 Cobertura do TOC

Todos os 6 capítulos do TOC têm seções correspondentes no `.md`:

| Capítulo | Status |
|---|---|
| 1. Introdução | ✅ |
| 2. Abordagem centrada nas pessoas | ✅ |
| 3. Intervenções de atenção e suporte (3.1–3.3) | ✅ |
| 4. Educação em saúde e aconselhamento (4.1–4.7) | ✅ |
| 5. Modelos de atenção (5.1–5.5) | ✅ |
| 6. Cuidados paliativos (6.1–6.3) | ✅ |

**Resultado: sem gaps identificados.**

---

## 3. Cobertura por Outras Fontes (gaps do Manual mitigados)

### `recomendacoes-para-o-controle-da-tuberculose.md` (71K chars)

Documento principal ILTB da atenção básica do MS. Cobre os itens críticos ausentes do Manual .md:

| Conteúdo clínico | Presente |
|---|---|
| Isoniazida dose (5–10 mg/kg, máx 300 mg/dia) | ✅ |
| Piridoxina 50 mg/dia (prevenção neuropatia periférica) | ✅ |
| Neuropatia periférica | ✅ |
| Gestantes + ILTB | ✅ (7 ocorrências) |
| PVHIV / CD4 / antirretroviral | ✅ (12 ocorrências) |
| PPD / IGRA | ✅ (9 ocorrências) |
| Imunossupressores / anti-TNF | ✅ (3 ocorrências) |
| Critérios de suspensão do tratamento | ✅ (5 ocorrências) |
| Hepatotoxicidade | ✅ |
| 3HP (rifapentina + isoniazida semanal) | ✅ |
| 6H / 9H | ❌ — em `af_protocolo_vigilancia_iltb_2ed_9jun22_ok_web.md` e `GEDIIB_TratamentoTuberculose.md` |
| 26 Quadros clínicos numerados | ✅ |

### Distribuição de conteúdo por documento

| Conteúdo | Fonte primária |
|---|---|
| 3HP (doses, duração, 12 doses) | `tratamento_infeccao_latente_tuberculose_rifapentina_eletronico.md` |
| 6H / 9H (esquemas, doses adulto/criança) | `af_protocolo_vigilancia_iltb_2ed_9jun22_ok_web.md`, `GEDIIB_TratamentoTuberculose.md` |
| 4R (rifampicina 4 meses) | `GEDIIB_TratamentoTuberculose.md`, `recomendacoes-para-o-controle-da-tuberculose.md` |
| Interações medicamentosas (rifampicina, isoniazida) | `patch_interacoes_medicamentosas.md` ← patch criado em 2026-03-21 |
| Populações especiais (gestantes, PVHIV, anti-TNF) | `recomendacoes-para-o-controle-da-tuberculose.md` |
| Diagnóstico (PPD/IGRA, pontos de corte) | Manual .md Parte II (presente) + `recomendacoes.md` |
| Hepatotoxicidade / suspensão | Manual .md Parte III 4.4.2 (presente) + `recomendacoes.md` + patch |
| Piridoxina / neuropatia periférica | `patch_interacoes_medicamentosas.md` + `recomendacoes.md` |

---

## 4. Resumo Executivo

| Documento | Seções TOC | Presentes | Ausentes | Gaps críticos para ILTB |
|---|---|---|---|---|
| Manual .md | ~80 | ~65 | ~15 (concentradas em Parte III) | Seção 8 ILTB (mitigado), 6.3 (patcheado) |
| OMS Módulo 4 .md | 25 | 25 | 0 | Nenhum |

### Ações tomadas

| # | Gap | Criticidade | Status |
|---|---|---|---|
| 1 | Seção 6.3 Interações Medicamentosas | Alta | ✅ Patcheado — `docs/protocolos/patch_interacoes_medicamentosas.md` |
| 2 | Seção 8 Tratamento da ILTB | Alta | ✅ Mitigado — conteúdo em `recomendacoes-para-o-controle-da-tuberculose.md` + docs especializados |
| 3 | Seção 6.1 Reações Adversas | Média | ✅ Mitigado — piridoxina em `patch_interacoes.md` + `recomendacoes.md` |

### Conclusão

**Nenhum patch adicional necessário.** A base de dados está suficientemente completa para o escopo ILTB. Todas as categorias do test set (ET, MO, IM, PE, DI, IT, EA) têm conteúdo indexado de suporte.

---

## 5. Metodologia

```python
# Extração do TOC
from pypdf import PdfReader
reader = PdfReader("docs/protocolos/<nome>.pdf")
for i in range(15):  # primeiras páginas têm o sumário
    text = reader.pages[i].extract_text()
    # buscar por "sumário", "índice", numeração de seções

# Extração de cabeçalhos do .md
with open("docs/protocolos/<nome>.md", encoding="utf-8") as f:
    lines = f.readlines()
headers = [l for l in lines if l.startswith("#")]

# Verificação de conteúdo clínico
import re
with open("docs/protocolos/<nome>.md", encoding="utf-8") as f:
    content = f.read()
matches = re.findall(r"piridoxina|neuropatia|gestante|PVHIV", content, re.IGNORECASE)
```

> A auditoria foi executada inteiramente com ferramentas locais (pypdf + regex). Zero tokens de API consumidos.
