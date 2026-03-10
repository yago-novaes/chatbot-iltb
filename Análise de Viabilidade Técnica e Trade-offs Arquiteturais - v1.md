## **Análise de Viabilidade Técnica e Trade-offs Arquiteturais: Diretrizes para Implementação do Chatbot em ILTB**

**1\. Introdução e Contextualização do Escopo** O presente documento estabelece as diretrizes arquiteturais e metodológicas para o desenvolvimento da ferramenta tecnológica vinculada ao projeto guarda-chuva "Desenvolvimento de Tecnologia para Auxiliar a Gestão do Cuidado em Enfermagem no Tratamento Preventivo da Tuberculose". Embora o projeto matriz defina as bases da pesquisa em saúde coletiva, identificou-se a necessidade de uma revisão crítica rigorosa dos pilares de engenharia de software, orçamento de infraestrutura e métricas de validação de Inteligência Artificial propostos inicialmente. Esta análise fundamenta os trade-offs assumidos para garantir a viabilidade, segurança clínica e adoção da ferramenta.

**2\. Privacidade de Dados e Infraestrutura: A Supressão do Risco "On-Premise"** A premissa inicial de que o uso de infraestrutura em nuvem (Cloud) violaria diretrizes de privacidade (LGPD e Resolução CNS 466/2012 ) baseava-se em um equívoco de design de sistema. A ferramenta conversacional foi concebida para auxiliar a tomada de decisão do profissional de saúde no manejo da Infecção Latente por Tuberculose (ILTB), operando como um oráculo de protocolos clínicos, e não como um Prontuário Eletrônico do Paciente (PEP).

Por definição de escopo e design de interface, é terminantemente vedada e desnecessária a inserção de Informações Pessoalmente Identificáveis (PII) — como nome, CPF ou número de prontuário — nos *prompts* de consulta. Sendo os dados trafegados puramente técnicos (ex: dúvidas sobre dosagens ou reações adversas), o risco de exposição de dados sensíveis de pacientes é nulo. Consequentemente, descarta-se a obrigatoriedade de hospedagem local (On-Premise) em hardwares institucionais, adotando-se uma arquitetura em nuvem (Cloud/API) que garante alta disponibilidade, redundância e menor custo operacional.

**3\. Evolução Arquitetural: Transição de Árvores de Decisão para RAG** A Fase 2 do projeto matriz sugere a utilização da plataforma Botpress , descrevendo o uso de algoritmos que funcionam "gerando textos ou frases específicas, possibilitando a interação conversacional com mensagens prontas e a partir de itens pré-selecionados". Do ponto de vista da engenharia de software atual, esta abordagem não caracteriza Inteligência Artificial Generativa, mas sim um fluxo determinístico baseado em regras (Árvore de Decisão/URA de texto).

Para entregar o suporte cognitivo complexo exigido por protocolos de saúde, este trabalho adota a arquitetura RAG (*Retrieval-Augmented Generation*).

* **Aterramento (Grounding):** Os documentos e manuais do Ministério da Saúde são vetorizados em um banco de dados especializado.  
* **Geração:** Modelos de Linguagem de Grande Escala (LLMs), acessados via API, recuperam o contexto clínico exato do banco de dados antes de formular a resposta.  
  Esta arquitetura elimina o risco inerente de "alucinação" dos LLMs, garantindo que a resposta gerada esteja estritamente ancorada em literatura médica validada.

**4\. Interface do Usuário: Mitigação de Fricção e Adoção** Considerando que a população do estudo é composta por enfermeiros atuantes nos níveis primário e secundário de atenção à saúde, a exigência de acesso via navegadores web (Webchat) ou portais institucionais durante o fluxo de atendimento impõe uma fricção inaceitável, fadando a ferramenta ao subuso. O trade-off arquitetural estabelece que a interface do usuário será nativamente o **WhatsApp**, intermediada por uma API de conexão e um orquestrador em nuvem. A ferramenta deve estar onde o usuário já se encontra.

**5\. Viabilidade Financeira, Estimativa de OpEx e Dimensionamento de Infraestrutura**

Uma análise do orçamento previsto no projeto original, totalizando R$ 38.539,44, revela uma alocação de R$ 3.100,00 para aquisição de equipamento permanente (impressora) e R$ 12.000,00 para taxas de publicação, sem previsão orçamentária detalhada para licenciamento de software, infraestrutura de servidores em nuvem ou consumo de APIs de Inteligência Artificial.

O projeto exige o funcionamento ininterrupto da ferramenta por um período inicial de monitoramento de 6 meses. Para suprir essa lacuna e garantir a resiliência do piloto, este braço tecnológico utilizará um teto orçamentário provisionado de R$ 8.000,00, destinado integralmente às Despesas Operacionais (OpEx). A modelagem financeira a seguir demonstra que este valor é substancialmente superior ao necessário, garantindo não apenas os 6 meses de piloto, mas uma sustentabilidade operacional de longo prazo.

**5.1. Dimensionamento Volumétrico e Custos de Inferência (LLM)**

O cenário operacional do estudo piloto prevê o uso diário por 5 enfermeiros. Estimando um uso intensivo de 2.200 requisições mensais, e considerando a arquitetura RAG — que injeta documentos de contexto no prompt —, projeta-se um consumo mensal de 4.400.000 tokens de entrada (*input*) e 1.100.000 tokens de saída (*output*).

Utilizando o modelo otimizado **gpt-4o-mini** da OpenAI, precificado a US$ 0,15 por milhão de tokens de entrada e US$ 0,60 por milhão de tokens de saída (OPENAI, 2026), o custo de inferência cognitiva gerado pelo chatbot é extremamente baixo. Aplicando uma taxa de câmbio conservadora com margem de segurança de 20% (US$ 1 \= R$ 6,60), o custo mensal de Inteligência Artificial projetado é de **R$ 8,71**.

**5.2. Infraestrutura de Nuvem e Governança de Dados**

Para orquestrar o sistema e hospedar o banco de dados vetorial, faz-se necessária uma Máquina Virtual (VPS) com no mínimo 4 vCPUs e 8GB de RAM. Para evitar custos ocultos de transferência de dados (*Egress Tax*) comuns em provedores hiperescalares, a arquitetura adotará provedores de precificação previsível (*Predictable Pricing*).

A instância CPX31 da Hetzner Cloud (HETZNER, 2026), fisicamente alocada na Alemanha, atende a todos os requisitos técnicos pelo valor aproximado de € 16,49 mensais (cerca de **R$ 122,69**), incluindo 20 Terabytes de transferência de dados. Cabe ressaltar que a hospedagem em território europeu resguarda o projeto juridicamente, visto que a União Europeia opera sob a GDPR, legislação reconhecida pelo Brasil como conferindo grau de proteção de dados adequado e equivalente à LGPD, conforme o Art. 33, I, da Lei nº 13.709/2018. Ademais, reforça-se que dados sensíveis de pacientes não transitam no prompt.

**5.3. Mensageria Oficial e Isenção Tarifária**

O projeto utilizará a API Oficial do WhatsApp (*WhatsApp Business API*), abandonando soluções não oficiais que violam os Termos de Serviço da plataforma. Conforme a política tarifária atualizada da Meta (META, 2026), mensagens da categoria *Service Conversations* (Conversas de Serviço) — ou seja, aquelas iniciadas pelo usuário (enfermeiro) para suporte ou consulta, e respondidas dentro de uma janela de 24 horas — são **isentas de tarifação**. Como o chatbot do ILTB é uma ferramenta reativa de consulta clínica, o custo de telecomunicação mensal será de **R$ 0,00**.

**5.4. Comparativo TCO (Total Cost of Ownership) e Runway Financeiro**

A tabela abaixo contrasta o Custo Total de Propriedade de uma solução em Nuvem (OpEx) frente à alternativa de aquisição de Hardware Local (CapEx), frequentemente cogitada em ambientes acadêmicos. Uma Workstation mínima para inferência local de LLMs (ex: GPU RTX 4060 Ti 16GB, 32GB RAM) exige um desembolso inicial médio de R$ 7.000,00, somado ao custo contínuo de energia elétrica dissipada (estimado conservadoramente em R$ 216,00 mensais).

| Modalidade Arquitetônica | Custo Inicial (CapEx) | Custo Operacional Mensal (OpEx / Energia) | Custo Total (1º Ano) | Runway com Teto de R$ 8.000,00 |
| :---- | :---- | :---- | :---- | :---- |
| **Infraestrutura Local (On-Premise)** | R$ 7.000,00 (Aquisição de Workstation) | R$ 216,00 (Consumo Elétrico) | R$ 9.592,00 | **Insolvente em \< 5 meses** |
| **Infraestrutura em Nuvem (VPS \+ LLM \+ API Meta)** | R$ 0,00 | **R$ 131,40** (Servidor \+ API LLM) | R$ 1.576,80 | **\~ 60 Meses de Sustentabilidade** |

A análise consolida que a alocação do orçamento via OpEx em infraestrutura de nuvem, além de prover tolerância a falhas (SLA de 99,9%) impossível de ser replicada em hardwares alocados fisicamente em laboratórios universitários, garante um tempo de sobrevida (*Runway*) superior a **60 meses**. O montante de R$ 8.000,00 assegura ampla cobertura orçamentária não apenas para os 6 meses do estudo piloto, mas garante escalabilidade imediata para futuras implantações do projeto no Sistema Único de Saúde (SUS).

**Referências da Seção:**

* HETZNER. *VPS Hosting Plans / CPX31*. Disponível em: [https://www.hetzner.com/cloud/](https://www.hetzner.com/cloud/). Acesso em: fev. 2026\.  
* META. *WhatsApp Business Platform Pricing*. Developer Platform. Disponível em: [https://business.whatsapp.com/products/platform-pricing](https://business.whatsapp.com/products/platform-pricing). Acesso em: fev. 2026\.  
* OPENAI. *Pricing: GPT-4o mini*. Disponível em: [https://openai.com/api/pricing/](https://openai.com/api/pricing/). Acesso em: fev. 2026\.

