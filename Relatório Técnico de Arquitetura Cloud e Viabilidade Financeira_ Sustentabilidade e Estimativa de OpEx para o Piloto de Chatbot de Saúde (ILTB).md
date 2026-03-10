**Relatório Técnico de Arquitetura Cloud e Viabilidade Financeira: Sustentabilidade e Estimativa de OpEx para o Piloto de Chatbot de Saúde (ILTB)**

**1\. O Paradigma da Eficiência Computacional no Setor de Saúde e a Transformação Digital**

A modernização das interfaces de suporte à decisão clínica no setor de saúde frequentemente esbarra em barreiras orçamentárias tradicionais, destacando-se a premissa de que a infraestrutura em nuvem (*Cloud Computing*) possui custos proibitivos para o setor público ou acadêmico. Este relatório técnico analisa, sob a ótica da engenharia de software e da viabilidade financeira, a implementação de um Chatbot de Saúde baseado na arquitetura *Retrieval-Augmented Generation* (RAG) para o projeto piloto ILTB.

O cenário operacional baseia-se em uma equipe composta por cinco enfermeiros, gerando um volume estimado de 2.200 requisições mensais. Ao mapear o consumo exato de tokens de inferência semântica, os custos de infraestrutura virtualizada e as tarifas de mensageria, a análise demonstra que o teto orçamentário de R$ 8.000,00 garante não apenas os seis meses iniciais do piloto, mas uma sustentabilidade financeira (*Runway*) de múltiplos anos. O documento evidencia que a adoção de um modelo baseado em *Operational Expenditure* (OpEx) confere maior previsibilidade e resiliência em comparação à aquisição tradicional de ativos físicos institucionais (*Capital Expenditure* \- CapEx), cujos custos ocultos de manutenção e depreciação tornam-se gargalos operacionais.

**2\. Arquitetura RAG e Dimensionamento de Inferência em LLMs**

Em ambientes de saúde, onde a precisão clínica é imperativa, o uso de Modelos de Linguagem de Grande Escala (LLMs) puramente generativos (*zero-shot*) apresenta risco de alucinações cognitivas. A arquitetura RAG mitiga esse risco ao buscar informações em um banco de dados vetorial externo (protocolos do Ministério da Saúde) e injetar esse contexto no *prompt* antes da geração da resposta.

Essa dinâmica assegura a fidelidade da informação, mas cria uma assimetria no consumo de processamento: o volume de dados enviado ao modelo (entrada) é significativamente superior ao volume gerado (saída).

**2.1. Dimensionamento do Consumo de Tokens**

Cada uma das 2.200 requisições mensais consome um bloco padronizado estimado em 2.000 tokens de entrada (*System Prompt*, Contexto Recuperado, Histórico e Pergunta) e gera uma resposta média de 500 tokens de saída. O consumo mensal projetado estabelece-se da seguinte forma:

* **Processamento de Entrada:** 2.200 requisições × 2.000 tokens \= 4.400.000 tokens/mês.  
* **Geração de Saída:** 2.200 requisições × 500 tokens \= 1.100.000 tokens/mês.  
* **Volume Total:** 5.500.000 tokens/mês.

**2.2. Análise Comparativa de Precificação: gpt-4o-mini vs. Claude 3 Haiku**

Para estruturar o modelo financeiro de forma conservadora, as cotações originais em dólar (US$) foram convertidas para Real (R$) utilizando uma taxa base de R$ 5,50, acrescida de uma margem de segurança cambial e tributária de 20% (taxa efetiva de R$ 6,60).

* **OpenAI (gpt-4o-mini):** Custo de US$ 0,15 por milhão de tokens de entrada e US$ 0,60 por milhão de tokens de saída.  
* **Anthropic (Claude 3 Haiku):** Custo de US$ 0,25 por milhão de tokens de entrada e US$ 1,25 por milhão de tokens de saída.

| Especificação / Modelo Fundacional | gpt-4o-mini (OpenAI) | Claude 3 Haiku (Anthropic) |
| :---- | :---- | :---- |
| Custo de Entrada (US$ / 1M tokens) | US$ 0,15 | US$ 0,25 |
| Custo de Saída (US$ / 1M tokens) | US$ 0,60 | US$ 1,25 |
| Despesa Mensal Entrada (4.4M tokens) | US$ 0,66 | US$ 1,10 |
| Despesa Mensal Saída (1.1M tokens) | US$ 0,66 | US$ 1,375 |
| Custo Total Mensal (US$) | US$ 1,32 | US$ 2,475 |
| **Custo Total Mensal (R$ c/ margem)** | **R$ 8,71** | **R$ 16,33** |

O modelo gpt-4o-mini consolida-se como a escolha arquitetônica mais eficiente, totalizando um custo operacional de inferência inferior a R$ 9,00 mensais.

**3\. Engenharia de Infraestrutura e Mitigação do *Egress Tax***

Para orquestrar o RAG e manter o banco de dados vetorial operante (ex: Qdrant, ChromaDB), a arquitetura exige um Servidor Virtual Privado (VPS) com no mínimo 4 vCPUs e 8GB de RAM.

No mercado de nuvem, provedores hiperescalares frequentemente cobram taxas variáveis por tráfego de saída de dados (*Bandwidth Egress*), orbitando a faixa de US$ 0,08 por Gigabyte. Para garantir a previsibilidade financeira e isolar o projeto de picos orçamentários, recomenda-se a adoção do modelo de *Predictable Pricing* (Precificação Previsível), oferecido por provedores como DigitalOcean , Linode/Akamai e Hetzner.

\+3

| Provedor de Cloud (Predictable Pricing) | Especificação da Instância | Mensalidade (US$) | Franquia de Banda Inclusa | Custo Mensal (R$ c/ 20% margem) |
| :---- | :---- | :---- | :---- | :---- |
| **Hetzner Cloud** | CPX31 (AMD 4vCPU / 8GB RAM / 160GB SSD) | \~US$ 18,59 \+1 | 20 TB \+1 | **R$ 122,69** |
| **DigitalOcean** | Basic Droplet (Shared 4vCPU / 8GB RAM / 160GB SSD) | US$ 48,00 | 5 TB | R$ 316,80 |
| **Linode / Akamai** | VM Medium (Shared 4vCPU / 8GB RAM / 160GB SSD) | US$ 48,00 | Variável (1-20TB) | R$ 316,80 |

A adoção da instância CPX31 da Hetzner assegura os recursos computacionais necessários por R$ 122,69 mensais, mitigando proativamente riscos de custos ocultos com rede.

**4\. Mensageria Oficial e Compliance**

Soluções não oficiais de integração com o WhatsApp (como automações de WhatsApp Web) apresentam mensalidades fixas, mas violam os Termos de Serviço da plataforma, expondo o projeto a riscos de banimento e instabilidade operacional.

O atual modelo tarifário da API Oficial do WhatsApp (*WhatsApp Business API*) aboliu as taxas sobre a categoria *Service Conversations* (Conversas de Serviço). Quando o enfermeiro inicia a interação, a plataforma abre uma janela de 24 horas isenta de tarifação para mensagens de formato livre geradas pelo chatbot. Como o chatbot do ILTB opera exclusivamente de forma reativa a questionamentos clínicos, o custo de telecomunicação da operação será de **R$ 0,00**. Adicionalmente, esta abordagem mantém o projeto em conformidade regulatória (*compliance*) com as recentes políticas da Meta para uso de IA.

**5\. Análise Crítica da Infraestrutura Local (*On-Premise*)**

A alternativa de utilizar *hardwares* físicos alocados nas instituições de saúde (*On-Premise*) acarreta custos estruturais frequentemente subestimados.

Para executar inferências locais com latência tolerável (ex: série Llama 3), exige-se uma *Workstation* equipada com processador de alto desempenho (ex: AMD Ryzen 7), no mínimo 32GB de RAM, e placa aceleradora (GPU) com 16GB de VRAM. O custo de aquisição (CapEx) deste equipamento é estipulado na faixa de R$ 7.000,00.

A este investimento soma-se o consumo elétrico contínuo de uma máquina operando ininterruptamente, projetado de forma conservadora em cerca de R$ 216,00 mensais sob o regime tarifário local. Ademais, arquiteturas locais carecem da redundância nativa (SLA de 99,9%) ofertada por data centers em nuvem. Falhas de *hardware* em ambientes acadêmicos e públicos esbarram na complexidade dos processos licitatórios (Lei nº 14.133/2021), podendo resultar em meses de indisponibilidade sistêmica, enquanto instâncias virtuais podem ser restauradas via infraestrutura como código em minutos.

**6\. Comparativo TCO e *Runway* Operacional**

A viabilidade do teto orçamentário de R$ 8.000,00 é comprovada calculando-se o tempo de sobrevida remanescente (*Runway*) do projeto com base no *Burn Rate* (Queima Mensal).

* **Cenário Cloud 1 (Otimizado):** Hetzner (R$ 122,69) \+ GPT-4o-mini (R$ 8,71) \+ API Meta (R$ 0,00) \= **R$ 131,40 / mês**.  
* **Cenário Cloud 2 (Alternativo):** DigitalOcean (R$ 316,80) \+ Claude 3 Haiku (R$ 16,33) \+ API Meta (R$ 0,00) \= **R$ 333,13 / mês**.

| Modalidade Arquitetônica | Investimento Inicial (CapEx) | Custo Operacional Mensal (OpEx/Energia) | Custo Acumulado (12 meses) | Projeção de Runway (Teto R$ 8.000,00) |
| :---- | :---- | :---- | :---- | :---- |
| **Local (*Workstation* Dedicada)** | R$ 7.000,00 | R$ 216,00 | R$ 9.592,00 | **Déficit alcançado no 5º mês** |
| **Nuvem (Cenário \- Otimizado)** | R$ 0,00 | **R$ 131,40** | **R$1.576,80** | **\~60 Meses de Sustentabilidade** |
| **Nuvem (Cenário 2 \- Alternativo)** | R$ 0,00 | R$ 333,13 | R$ 3.997,56 | \~24 Meses de Sustentabilidade |

A destinação dos recursos para aquisição de infraestrutura física esgota o orçamento no momento da compra, tornando a operação insolvente antes do término do piloto. Em contraste, a migração para a Nuvem via OpEx garante a operação contínua da ferramenta por aproximadamente 5 anos, provando a ampla folga orçamentária para a consolidação e expansão da pesquisa.

**7\. Diretrizes Arquiteturais**

Com base na engenharia e matemática apresentadas, estabelecem-se três recomendações técnico-administrativas fundamentais para o sucesso do projeto ILTB:

1. **Transição para *OpEx* em Nuvem:** Eliminar a dependência de infraestrutura física local, garantindo resiliência, redundância e sustentabilidade a longo prazo sem necessidade de renovação de *hardware*.  
2. **Adoção de Modelos de Alta Eficiência (*Predictable Pricing*):** Estruturar o processamento cognitivo via APIs de baixo custo (como gpt-4o-mini) combinadas a provedores de VPS com franquias massivas de dados (como Hetzner Cloud), neutralizando variações de custos com transferência de rede.  
3. **Conformidade Omnicanal Oficial:** Operar estritamente através da API Oficial da Meta, aproveitando a isenção de custos na categoria *Service Conversations* e resguardando a instituição pública de riscos associados a *softwares* não autorizados.

**Referências Bibliográficas**

AKAMAI. *Choose a compute plan \- Akamai TechDocs*. 2026\. Disponível em: [https://techdocs.akamai.com/cloud-computing/docs/how-to-choose-a-compute-instance-plan](https://techdocs.akamai.com/cloud-computing/docs/how-to-choose-a-compute-instance-plan). Acedido a: 24 fev. 2026\.

ANTHROPIC. *Claude 3 Haiku: our fastest model yet*. 2026\. Disponível em: [https://www.anthropic.com/news/claude-3-haiku](https://www.anthropic.com/news/claude-3-haiku). Acedido a: 24 fev. 2026\.

ANTHROPIC. *Plans & Pricing | Claude by Anthropic*. 2026\. Disponível em: [https://www.anthropic.com/pricing](https://www.anthropic.com/pricing). Acedido a: 24 fev. 2026\.

DIGITALOCEAN. *Droplet Pricing | Scalable Cloud Compute*. 2026\. Disponível em: [https://www.digitalocean.com/pricing/droplets](https://www.digitalocean.com/pricing/droplets). Acedido a: 24 fev. 2026\.

GOVERNO DO BRASIL. *EDP ES tem novas tarifas de energia aprovadas pela ANEEL*. Portal Gov.br, 2025\. Disponível em: [https://www.gov.br/aneel/pt-br/assuntos/noticias/2025/edp-es-tem-novas-tarifas-de-energia-aprovadas-pela-aneel](https://www.gov.br/aneel/pt-br/assuntos/noticias/2025/edp-es-tem-novas-tarifas-de-energia-aprovadas-pela-aneel). Acedido a: 24 fev. 2026\.

HETZNER. *Flexible Cloud Hosting Services und VPS Server*. 2026\. Disponível em: [https://www.hetzner.com/cloud](https://www.hetzner.com/cloud). Acedido a: 24 fev. 2026\.

META. *WhatsApp Business Platform Pricing*. Developer Platform. 2026\. Disponível em: [https://business.whatsapp.com/products/platform-pricing](https://business.whatsapp.com/products/platform-pricing). Acedido a: 24 fev. 2026\.

OPENAI. *GPT-4o mini: advancing cost-efficient intelligence*. 2026\. Disponível em: [https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/](https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/). Acedido a: 24 fev. 2026\.

OPENAI. *Pricing | OpenAI API*. 2026\. Disponível em: [https://openai.com/api/pricing/](https://openai.com/api/pricing/). Acedido a: 24 fev. 2026\.

RESPOND.IO. *Not All Chatbots Are Banned: WhatsApp's 2026 AI Policy Explained*. 2026\. Disponível em: [https://respond.io/blog/whatsapp-general-purpose-chatbots-ban](https://respond.io/blog/whatsapp-general-purpose-chatbots-ban). Acedido a: 24 fev. 2026\.

TURN.IO. *WhatsApp's 2026 AI Policy Explained*. 2026\. Disponível em: [https://learn.turn.io/l/en/article/khmn56xu3a-whats-app-s-2026-ai-policy-explained](https://learn.turn.io/l/en/article/khmn56xu3a-whats-app-s-2026-ai-policy-explained). Acedido a: 24 fev. 2026\.

