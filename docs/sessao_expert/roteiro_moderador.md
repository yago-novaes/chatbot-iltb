# Roteiro do Moderador — Sessão de Avaliação com Especialista

**Documento operacional para o pesquisador conduzir a sessão de ~90 min.**

> _Imprimir e ter à mão, ou manter aberto em segundo monitor. Texto entre aspas é fala-modelo; **destacar** marca lembrete; ⏱ marca cronômetro relativo ao início da sessão (T+00 ... T+90)._

---

## Pré-sessão (checklist — fazer ~30 min antes)

- [ ] **Internet estável** confirmada na máquina que vai hospedar o ngrok
- [ ] **ngrok rodando** com o chatbot acessível na URL pública; testar enviando uma pergunta simples (e.g., ET-01)
- [ ] **Backup local** preparado: caso a internet caia, ter capacidade de rodar o chatbot em `localhost` e a expert acessar via screenshare
- [ ] **TCLE** impresso em 2 vias (1 para a expert, 1 para o arquivo)
- [ ] **Questionário TAM-AIN** impresso (ou Google Form aberto, conforme preferência da expert) + caneta
- [ ] **Planilha de coleta deep-dive** aberta em laptop (pode ser CSV no Excel/Google Sheets) com as 10 questões pré-preenchidas e respostas do chatbot já carregadas
- [ ] **Material de gravação** (smartphone com app de gravação ou OBS) testado, com autorização **pendente** até o TCLE
- [ ] **Lista de perguntas-âncora para a demo** (ET-01 e PE-04) anotadas separadamente
- [ ] **Bloco de notas** (digital ou papel) para anotações verbais durante o deep-dive
- [ ] **Água, pausa programada** ao final do deep-dive (T+65)
- [ ] **Link para a planilha de coleta async** pronto para enviar por e-mail ao final

---

## Bloco 1 — Abertura e TCLE (⏱ T+00 a T+10)

### 1.1 Recepção (1 min)

> _"Olá, {{nome da expert}}! Muito obrigado(a) por aceitar participar. Vamos levar cerca de 90 minutos --- está bom para você confirmar?"_

Aguardar resposta. Se a expert puder dar mais tempo, registrar; se tiver imprevisto, **avisar que pode encurtar a etapa 4 (entrevista)** sem prejudicar o restante.

### 1.2 Apresentação do projeto (~2 min)

> _"Esta sessão faz parte do meu TCC em Engenharia de Produção na UFES, orientado pelos professores Wilian Hisatugu e Renato Moraes. Estou desenvolvendo um **chatbot de apoio clínico para o manejo da ILTB** --- ele responde perguntas sobre os protocolos do MS e da OMS, citando a fonte. A ideia é que enfermeiros da atenção primária possam consultar o sistema durante o atendimento, sem precisar abrir o manual inteiro."_
>
> _"Já avaliei o sistema com métricas automáticas, mas elas têm limites. O objetivo de hoje é capturar o **seu julgamento profissional** sobre essas respostas --- esse é o instrumento mais importante da pesquisa."_

### 1.3 Leitura conjunta dos pontos-chave do TCLE (~5 min)

Entregar o TCLE em 2 vias. Ler em voz alta os tópicos críticos (não precisa ler tudo --- a expert leu antes ou lê em paralelo):

> _"Três pontos importantes do termo:
>
> 1. **Sua participação é voluntária.** Você pode interromper a qualquer momento, sem precisar justificar.
> 2. **Não armazenamos suas consultas no chatbot.** O sistema opera com retenção zero, e os cenários que vamos discutir são fictícios ou genéricos --- nenhum dado de paciente real.
> 3. **Sua identidade fica anonimizada na monografia.** Vou citar apenas perfil resumido (formação, tempo de prática, área genérica), nunca seu nome ou unidade específica."_

### 1.4 Consentimentos granulares (~1 min)

> _"Tem três autorizações separadas, cada uma é opcional. Posso ler:_
>
> _- **Autoriza gravação de áudio** da sessão para revisão posterior das suas observações? Sim ou não?_
> _- **Autoriza gravação de vídeo**? (Geralmente só uso áudio, vídeo é opcional.) Sim ou não?_
> _- **Autoriza a inclusão do seu perfil profissional anonimizado** na monografia? Sim ou não?"_

Marcar os checkboxes na presença da expert. **Se autorizar áudio**, ligar a gravação agora e dizer em voz alta: _"Gravação iniciada em {{horário}}."_

### 1.5 Assinaturas (~1 min)

Você assina como pesquisador; a expert assina ambas as vias. Uma fica com ela.

**Transição** (frase para fechar este bloco):

> _"Pronto, formalidade resolvida. Agora vou te mostrar como o chatbot funciona com duas perguntas, e depois entramos na parte de avaliação."_

---

## Bloco 2 — Demonstração funcional (⏱ T+10 a T+20)

### 2.1 Abrir a interface (~1 min)

Mostrar a tela do chatbot (ngrok URL ou screenshare). Apontar os elementos:

> _"Esta é a interface. Você digita a pergunta, ele recupera os trechos dos protocolos do MS e gera a resposta citando o documento. Não tem login, não armazena histórico. Vou te mostrar com duas perguntas reais que enfermeiros costumam fazer."_

### 2.2 Pergunta-âncora 1 — ET-01 (resposta clara, ~3 min)

Submeter ao vivo:
> _"Qual a dose de isoniazida no esquema 3HP para adultos?"_

Esperar a resposta aparecer. Ler a resposta junto com a expert. Comentar:

> _"Veja que ele cita os trechos --- aqui o Trecho 1 e o Trecho 2 --- e dá a dose com o critério de peso. Esse é o comportamento esperado."_

### 2.3 Pergunta-âncora 2 — PE-04 (resposta com ressalva clínica, ~3 min)

Submeter:
> _"Qual esquema de tratamento da ILTB deve ser evitado em gestantes?"_

Comentar:

> _"Aqui você vê o sistema lidando com uma pergunta que tem nuance --- contraindicação em gestantes. Repare se ele está dando a informação completa ou se omite algum aspecto. Não estou pedindo sua classificação ainda, só queria que você visse o estilo de resposta."_

### 2.4 Espaço para perguntas livres da expert (~2-3 min)

> _"Antes de começarmos a avaliação propriamente dita, tem algo da interface ou do funcionamento que você queira testar ou perguntar?"_

Se a expert quiser, deixar ela submeter 1-2 perguntas livres. **Não anotar** essas perguntas como parte da avaliação --- são da etapa de demonstração.

**Transição:**

> _"Agora vou submeter 10 perguntas em sequência. Para cada uma, depois que o chatbot responder, vou te pedir três coisas: classificar a acurácia, avaliar a severidade se tiver erro, e dar uma nota para o quanto o trecho recuperado serviu. Vou te guiar."_

---

## Bloco 3 — Avaliação dirigida (deep-dive, ⏱ T+20 a T+65, **~45 min**)

**Material:** [`selecao_deep_dive.md`](selecao_deep_dive.md), [`planilha_coleta_deep_dive.csv`](planilha_coleta_deep_dive.csv).

### Fluxo padrão para cada uma das 10 questões (~4-5 min cada)

#### Passo A — Apresentar (15 s)
> _"Próxima: {{ler a pergunta em voz alta da coluna 'pergunta' da planilha}}. Vou submeter ao chatbot."_

Submeter ao chatbot (ao vivo) **ou** colar a resposta já coletada (consultar coluna `resposta_chatbot`). Mostrar a resposta na tela.

#### Passo B — Leitura (~60 s)

Dar tempo para a expert ler em silêncio. Não preencher nada ainda. Se ela começar a comentar, deixar falar e anotar verbatim no campo `comentarios_qualitativos`.

#### Passo C — Coleta I1 + I2 + I3 (~60-90 s)

> _"Três perguntinhas rápidas:_
>
> _- **Comparando com o protocolo do MS, essa resposta é correta, parcialmente correta ou incorreta?**"_

Preencher `I1_acuracia`. Se parcial/incorreta:

> _"Qual o trecho específico que está em conflito com o protocolo?"_

Preencher `I1_trecho_conflitante`.

> _"- **Qual a severidade desse erro se um(a) enfermeiro(a) seguisse essa resposta na prática?**" --- escala 1 (sem risco) a 5 (conduta perigosa)._

Preencher `I2_severidade` (deixar `NA` se a resposta foi totalmente correta).

> _"- Por último, **três notas de 1 a 5**:_
> _   - A resposta deriva mesmo do trecho recuperado, ou parece inventada?_ (`I3a_fidelidade`)
> _   - A resposta endereça a pergunta que foi feita?_ (`I3b_relevancia_resposta`)
> _   - O trecho recuperado é o trecho certo do protocolo para essa pergunta?_ (`I3c_relevancia_contexto`)"_

Preencher os três campos.

#### Passo D — Narrativa (~60-90 s)

> _"Algum comentário livre sobre essa resposta antes de irmos para a próxima? Por exemplo: você usaria isso na prática? Tem algum aspecto que te preocupa?"_

Anotar literalmente no campo `comentarios_qualitativos`. Quando ela parar de falar, ir para a próxima questão.

### Notas de tempo

Se em **T+35** ainda não chegou na 4ª questão, **sinalizar** mentalmente: "Tempo apertado, talvez precise reduzir o tempo de narrativa nas próximas." Não cortar a coleta I1+I2+I3, só o passo D (narrativa).

Se em **T+50** ainda na 7ª questão, **decidir**: passar as últimas 2-3 questões para a planilha async (anotar mentalmente quais ficam de fora).

### Pausa breve antes do Bloco 4

> _"Vamos fazer uma pausa de 1 minuto? Quer água?"_

---

## Bloco 4 — Questionário TAM-AIN (⏱ T+65 a T+80, **15 min**)

**Material:** [`questionario_tam_ain.md`](questionario_tam_ain.md).

### 4.1 Instrução (~2 min)

> _"Agora vou te entregar um questionário curto. São 28 afirmações em escala de 1 a 5 --- discordo totalmente até concordo totalmente. Não tem certo ou errado, é sua percepção. Você prefere preencher no papel ou eu te passo um link?"_

Se preencher no papel: entregar a folha + caneta. Você fica em silêncio (ou sai da sala se for remoto, deixando câmera ligada se a expert se sentir confortável).

Se Google Forms: enviar o link no chat.

### 4.2 Tempo de preenchimento (~12 min)

Manter silêncio. **Não direcionar** as respostas. Se a expert pedir esclarecimento sobre algum item, esclarecer o termo (e.g., "o que é APS?") mas não a direção da resposta.

> _Atenção: itens IP1 e IP3 são invertidos --- pode parecer estranho para a expert que ela esteja "concordando" com algo negativo. Não comentar; é proposital da escala._

### 4.3 Encerrar (~1 min)

Quando ela terminar:

> _"Pronto, era isso. Última parte: 10 minutos de conversa aberta. Pode ser?"_

---

## Bloco 5 — Entrevista semi-estruturada (⏱ T+80 a T+90, **10 min**)

**Material:** [`questionario_tam_ain.md`](questionario_tam_ain.md) seção 8.

> _"Não vou te perguntar todas as 10 questões abertas que estão no formulário --- senão a gente passa muito do tempo. Vou pegar as 4 mais importantes para mim agora; se sobrar tempo, faço mais."_

### Pergunta 1 (priorizada) — Conteúdo clínico crítico

> _"Considerando as respostas que avaliamos, **houve alguma que você consideraria perigosa** se um(a) profissional menos experiente seguisse à risca? Qual e por quê?"_

**Probes (perguntas de aprofundamento):**

- Se ela responder algo genérico: _"Você consegue me dar um exemplo específico, com paciente que você atenderia hoje?"_
- Se ela disser "nenhuma me preocupou": _"E inversamente --- alguma resposta te chamou positivamente a atenção? Por quê?"_

### Pergunta 2 (priorizada) — Adoção e fluxo

> _"Imagina o seu dia normal de atendimento na unidade. **Em quais momentos** você imagina que usaria um chatbot como este? E em quais **não usaria**?"_

**Probes:**

- _"Você usaria na frente do paciente, ou apenas antes/depois da consulta?"_
- _"E se o paciente perguntasse 'o que você está consultando?', você se sentiria confortável em responder?"_

### Pergunta 3 (priorizada) — Identidade profissional

> _"O TAM tem uma dimensão sobre 'preservação da identidade profissional'. Pensando na sua trajetória --- **uma ferramenta dessas valoriza ou desvaloriza o trabalho do(a) enfermeiro(a)?** Por quê?"_

**Probes:**

- Se ela disser "valoriza": _"E como você imagina que colegas mais resistentes a tecnologia reagiriam?"_
- Se ela disser "desvaloriza": _"O que precisaria mudar para você mudar de opinião?"_

### Pergunta 4 (priorizada) — Feedback aberto

> _"Tem alguma coisa que **eu não te perguntei** mas que você considera importante eu saber sobre essa ferramenta ou essa sessão?"_

**Probe único:**

- Se ela disser "nada": _"Algum ajuste no formato da sessão, ou algo que você gostaria de ter visto e não viu?"_

### Se sobrar tempo (raro)

Cobrir mais 1-2 perguntas da seção 8 do TAM-AIN, na ordem: 8.1.3 (lacunas no corpus), 8.3.8 (acesso de outros perfis profissionais).

---

## Bloco 6 — Fechamento (⏱ T+90 a T+95, **5 min**)

### 6.1 Explicar a parte assíncrona (~2 min)

> _"Só falta uma coisa --- existe uma planilha com as outras 29 perguntas do meu conjunto de avaliação, que não conseguimos cobrir aqui. Posso te enviar por e-mail? Você responde no seu tempo, em qualquer momento da próxima semana --- estima-se ~30 minutos. É bem mais simples: só duas colunas (acurácia + severidade), sem a tríade."_

Confirmar o e-mail dela. Anotar.

> _"É totalmente opcional --- se você não conseguir responder, a parte de hoje já é o coração da pesquisa. Mas se conseguir, ajudaria muito a robustez da minha amostra."_

### 6.2 Próximos passos do TCC (~1 min)

> _"Daqui, vou fechar o capítulo de Avaliação da monografia com o que você produziu hoje, vou cruzar suas notas com as métricas automáticas e ver onde elas divergem --- isso vai compor a discussão. A defesa está prevista para junho."_

### 6.3 Agradecimento e fim da gravação (~1 min)

> _"Muito obrigado, {{nome}}. Sua contribuição foi essencial. Em caso de qualquer dúvida ou se você quiser retirar alguma resposta, é só me mandar uma mensagem."_

**Se houver gravação ativa**, encerrar agora em voz alta: _"Encerrando a gravação em {{horário}}, total {{duração}}."_

### 6.4 Imediatamente após a sessão (não na frente da expert)

- [ ] Salvar a planilha de coleta deep-dive em backup duplicado (Drive + local)
- [ ] Transferir gravação (se houver) para armazenamento seguro
- [ ] Enviar e-mail à expert nas próximas 2 h com:
  - Cópia digital do TCLE assinado (escaneado)
  - Link da planilha async (se ela aceitou)
  - Agradecimento curto

---

## Contingências (consultar se algo der errado)

### Se a expert chegar atrasada (e.g., +15 min)

- Cortar 5 min da demo (Bloco 2 → ~5 min, só ET-01)
- Cortar 2 questões do deep-dive (manter 8 ao invés de 10; selecionar **omitir EA-04 e MO-02**, pois são as menos contrastivas)
- Manter TAM-AIN integral
- Reduzir entrevista para 2 perguntas (manter P1 e P2)

### Se o chatbot/ngrok cair durante a sessão

- Frase de calma: _"Tive um problema técnico aqui rápido --- enquanto eu reinicio, **vamos continuar com a resposta que eu já tenho coletada** dessa pergunta. Está em texto na minha tela."_
- Mostrar a resposta da coluna `resposta_chatbot` da planilha (já está pré-coletada do gate final).
- Em paralelo, tentar reiniciar o ngrok. Se não voltar em 5 min, **completar a sessão inteira usando as respostas pré-coletadas** --- a avaliação não é prejudicada.

### Se a expert quiser interromper antes do tempo

> _"Sem problema nenhum. Tudo o que você já avaliou é valioso. Você quer que eu desconsidere o que já foi coletado, ou posso manter?"_

Respeitar a decisão. Se ela quiser desconsiderar, deletar o CSV preenchido na presença dela. Reafirmar que isso não tem nenhum custo para ela.

### Se ela responder muito sucintamente / fechado

- Usar mais probes da seção "Entrevista" acima
- Trazer exemplos concretos: _"E se um paciente PVHIV de 65 anos chegasse hoje com indicação de iniciar imunossupressor e você precisasse decidir o esquema rapidinho --- como você usaria o chatbot?"_

### Se ela quiser ver mais do código / implementação

- _"Posso te mandar depois um link com o código-fonte ou com a monografia --- prefere?"_ — **não desviar a sessão para discussão técnica.** O foco da sessão é o uso clínico.

---

## Resumo visual do cronômetro

```
T+00 ────────────────────────────────────────────────────── INÍCIO
        Bloco 1 — Abertura + TCLE
T+10 ──────────────────────
        Bloco 2 — Demonstração funcional
T+20 ──────────────────────
        Bloco 3 — Avaliação dirigida (10 questões × ~4.5 min)
T+65 ──────────────────────  ← Pausa de 1 min
        Bloco 4 — Questionário TAM-AIN
T+80 ──────────────────────
        Bloco 5 — Entrevista (4 perguntas priorizadas)
T+90 ──────────────────────  ← FIM
        Bloco 6 — Fechamento (~5 min de cortesia)
T+95 ────────────────────────────────────────────────────── ENCERRAR
```

---

## Após a sessão (próximas 24 h)

1. **Transcrever observações qualitativas** (literais, da gravação ou notas) nos campos `comentarios_qualitativos` do CSV.
2. **Tabular o questionário TAM-AIN** (se foi em papel; já está se foi Form).
3. **Calcular scores por dimensão** (média dos itens; aplicar inversão IP1 e IP3).
4. **Anotar 2-3 impressões qualitativas** do moderador no diário técnico (e.g., "expert demonstrou hesitação em PE-07", "o termo X não foi entendido na primeira leitura").
5. **Esperar a planilha async** (~1 semana após a sessão). Enviar lembrete na D+5 se ainda não tiver chegado.
