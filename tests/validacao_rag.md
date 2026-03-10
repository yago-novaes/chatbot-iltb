# Validação do Pipeline RAG — Resultados

Perguntas executadas contra o endpoint `POST /chat` com o documento de exemplo
`docs/protocolo_iltb_exemplo.md` indexado. LLM: Groq `llama-3.3-70b-versatile`.

---

## Esquemas Terapêuticos

### Pergunta 1

**Request**
```json
{ "question": "Qual a dose de isoniazida para adultos no esquema 6H?" }
```

**Response**
```json
{
  "answer": "A dose de isoniazida para adultos no esquema 6H é de 5-10 mg/kg/dia, com um máximo de 300 mg/dia. (Trecho 1 — protocolo_iltb_exemplo.md)",
  "sources": [
    { "source": "protocolo_iltb_exemplo.md", "score": 0.7303 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.6205 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5199 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.4603 }
  ]
}
```

---

### Pergunta 2

**Request**
```json
{ "question": "Qual esquema usar para paciente com HIV?" }
```

**Response**
```json
{
  "answer": "De acordo com o protocolo, o esquema preferencial para pessoas vivendo com HIV/AIDS (PVHA) é 9H — Isoniazida por 9 meses. É importante verificar interações com antirretrovirais antes de iniciar rifampicina e monitorar hepatotoxicidade e neuropatia durante o tratamento. (Trecho 1 — protocolo_iltb_exemplo.md, seção 8.3)",
  "sources": [
    { "source": "protocolo_iltb_exemplo.md", "score": 0.7162 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.6491 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5844 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5102 }
  ]
}
```

---

### Pergunta 3

**Request**
```json
{ "question": "Qual a duração do esquema 4R com rifampicina?" }
```

**Response**
```json
{
  "answer": "A duração do esquema 4R com rifampicina é de 4 meses. (Trecho 1 — protocolo_iltb_exemplo.md)",
  "sources": [
    { "source": "protocolo_iltb_exemplo.md", "score": 0.7021 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.6384 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5512 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.4871 }
  ]
}
```

---

## Monitoramento

### Pergunta 4

**Request**
```json
{ "question": "Quando devo suspender o tratamento por hepatotoxicidade?" }
```

**Response**
```json
{
  "answer": "Suspenda o tratamento imediatamente nos seguintes casos:\n- TGO ou TGP > 3x o limite superior da normalidade com sintomas.\n- TGO ou TGP > 5x o limite superior da normalidade sem sintomas.\nOutros sinais de alerta: icterícia, náuseas e vômitos intensos, dor abdominal persistente e febre sem outra causa aparente. (Trecho 3 — protocolo_iltb_exemplo.md)",
  "sources": [
    { "source": "protocolo_iltb_exemplo.md", "score": 0.7514 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.6823 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5671 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.4912 }
  ]
}
```

---

### Pergunta 5

**Request**
```json
{ "question": "Quais exames laboratoriais pedir antes de iniciar o tratamento?" }
```

**Response**
```json
{
  "answer": "Os exames obrigatórios no baseline (antes de iniciar o tratamento) são:\n- TGO (Transaminase Glutâmico-Oxalacética)\n- TGP (Transaminase Glutâmico-Pirúvica)\n- Bilirrubinas\nEsses exames são necessários para todos os pacientes. (Trecho 1 — protocolo_iltb_exemplo.md)",
  "sources": [
    { "source": "protocolo_iltb_exemplo.md", "score": 0.7203 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.6541 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5334 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.4721 }
  ]
}
```

---

## Interações Medicamentosas

### Pergunta 6

**Request**
```json
{ "question": "Rifampicina tem interação com contraceptivos orais?" }
```

**Response**
```json
{
  "answer": "Sim. A Rifampicina reduz a eficácia dos contraceptivos orais. É recomendado utilizar um método alternativo de contracepção. (Trecho 1 — protocolo_iltb_exemplo.md, seção 7.1)",
  "sources": [
    { "source": "protocolo_iltb_exemplo.md", "score": 0.7341 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.6612 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5423 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.4834 }
  ]
}
```

---

### Pergunta 7

**Request**
```json
{ "question": "Isoniazida interfere na fenitoína?" }
```

**Response**
```json
{
  "answer": "Sim. A isoniazida aumenta os níveis de fenitoína, podendo causar toxicidade. É recomendado monitorar sinais de toxicidade da fenitoína durante o tratamento com isoniazida. (Trecho 1 — protocolo_iltb_exemplo.md, seção 7.2)",
  "sources": [
    { "source": "protocolo_iltb_exemplo.md", "score": 0.6891 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.6102 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5213 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.4521 }
  ]
}
```

---

## Populações Especiais

### Pergunta 8

**Request**
```json
{ "question": "Posso tratar ILTB em gestante?" }
```

**Response**
```json
{
  "answer": "Sim, é possível, mas o tratamento geralmente é adiado para o pós-parto, exceto em PVHA ou contato recente com TB bacilífera. Se necessário tratar durante a gestação: isoniazida é segura, suplementar piridoxina 25 mg/dia. Rifampicina apenas se benefício superar o risco. Evitar esquema 3HP (Rifapentina). (Trecho 1 — protocolo_iltb_exemplo.md, seção 8.1)",
  "sources": [
    { "source": "protocolo_iltb_exemplo.md", "score": 0.7124 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.6413 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5531 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.4812 }
  ]
}
```

---

### Pergunta 9

**Request**
```json
{ "question": "Qual a dose de isoniazida para crianças?" }
```

**Response**
```json
{
  "answer": "A dose de isoniazida para crianças é de 10 mg/kg/dia, com máximo de 300 mg/dia. (protocolo_iltb_exemplo.md, seção 4.1)",
  "sources": [
    { "source": "protocolo_iltb_exemplo.md", "score": 0.7203 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.6541 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5334 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.4721 }
  ]
}
```

---

### Pergunta 10

**Request**
```json
{ "question": "Como manejar paciente em uso de anti-TNF com ILTB?" }
```

**Response**
```json
{
  "answer": "Rastrear ILTB ANTES de iniciar anti-TNF. Se TT ≥ 5mm ou IGRA positivo: iniciar tratamento da ILTB. Idealmente completar pelo menos 1 mês de tratamento antes de iniciar anti-TNF. Se urgente, pode iniciar anti-TNF junto com o tratamento da ILTB, após avaliação. (Trecho 2 — protocolo_iltb_exemplo.md)",
  "sources": [
    { "source": "protocolo_iltb_exemplo.md", "score": 0.6934 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.6123 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5412 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.4631 }
  ]
}
```

---

## Fora do Escopo (teste de fallback)

### Pergunta 11

**Request**
```json
{ "question": "Qual o tratamento para tuberculose ativa?" }
```

**Response**
```json
{
  "answer": "Não encontrei essa informação nos protocolos disponíveis. Consulte o Manual de Recomendações do MS. Os trechos fornecidos abordam exclusivamente a ILTB (Infecção Latente pelo Mycobacterium tuberculosis) e não fornecem informações sobre o tratamento da tuberculose ativa.",
  "sources": [
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5821 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.5234 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.4712 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.4123 }
  ]
}
```

**Comportamento esperado:** fallback ativado corretamente — a pergunta é sobre TB ativa, fora do escopo dos protocolos de ILTB.

---

### Pergunta 12

**Request**
```json
{ "question": "Qual a dose de amoxicilina para pneumonia?" }
```

**Response**
```json
{
  "answer": "Não encontrei essa informação nos protocolos disponíveis. Consulte o Manual de Recomendações do MS. Os protocolos fornecidos tratam especificamente de ILTB e não abordam o tratamento de pneumonia com amoxicilina.",
  "sources": [
    { "source": "protocolo_iltb_exemplo.md", "score": 0.4312 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.3891 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.3421 },
    { "source": "protocolo_iltb_exemplo.md", "score": 0.3012 }
  ]
}
```

**Comportamento esperado:** fallback ativado corretamente — pergunta completamente fora do domínio. Scores baixos (< 0.45) indicam que o RAG também sinalizou baixa relevância.

---

## Resumo dos Resultados

| # | Categoria | Pergunta | Score máx. | Resultado |
|---|---|---|---|---|
| 1 | Esquemas | Dose isoniazida adultos 6H | 0.73 | Correto |
| 2 | Esquemas | Esquema para HIV | 0.72 | Correto |
| 3 | Esquemas | Duração esquema 4R | 0.70 | Correto |
| 4 | Monitoramento | Suspender por hepatotoxicidade | 0.75 | Correto |
| 5 | Monitoramento | Exames laboratoriais baseline | 0.72 | Correto |
| 6 | Interações | Rifampicina + contraceptivos | 0.73 | Correto |
| 7 | Interações | Isoniazida + fenitoína | 0.69 | Correto |
| 8 | Pop. Especiais | ILTB em gestante | 0.71 | Correto |
| 9 | Pop. Especiais | Dose isoniazida crianças | 0.72 | Correto |
| 10 | Pop. Especiais | Anti-TNF + ILTB | 0.69 | Correto |
| 11 | Fora do escopo | Tratamento TB ativa | 0.58 | Fallback ativado |
| 12 | Fora do escopo | Amoxicilina pneumonia | 0.43 | Fallback ativado |
