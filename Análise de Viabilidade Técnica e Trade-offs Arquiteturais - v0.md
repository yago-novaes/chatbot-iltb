# **Análise de Viabilidade Técnica e Trade-offs Arquiteturais**

**Projeto:** Chatbot para Gestão do Cuidado em ILTB

Este documento resume as discussões técnicas sobre a implementação do chatbot, considerando as restrições de orçamento (zero para software recorrente), a criticidade dos dados (saúde) e a necessidade de validação científica rigorosa.

## **1\. Trade-offs de Abordagem de Software**

A escolha da "inteligência" do bot impacta diretamente a capacidade de validação científica (Fase 2 do projeto) e a usabilidade.

### **Opção A: Abordagem Determinística (Árvore de Decisão)**

*O "Velho Jeito". Fluxos desenhados manualmente onde o usuário clica em botões.*

* **Prós (Vantagens):**  
  * **Controle Absoluto:** Zero risco de "alucinação" (o bot inventar tratamentos).  
  * **Validação Simples:** O painel de especialistas aprova um texto estático que nunca muda.  
  * **Custo Zero:** Roda em qualquer servidor básico da universidade.  
* **Contras (Desvantagens):**  
  * **Experiência Ruim:** Se o enfermeiro tiver uma dúvida específica fora do menu, o bot trava.  
  * **Manutenção Lenta:** Qualquer nova dúvida exige que um programador desenhe um novo fluxo.  
* **Veredito:** Seguro demais, mas pouco útil para dúvidas complexas de ILTB.

### **Opção B: Abordagem Generativa Pura (LLM via API de Nuvem)**

*Usar GPT-4 ou Claude via API.*

* **Prós (Vantagens):**  
  * **Alta Inteligência:** Entende contextos complexos e nuances da língua portuguesa.  
  * **Rapidez de Implementação:** Não exige configuração de servidores, apenas código de conexão.  
* **Contras (Desvantagens):**  
  * **Risco de Privacidade Crítico:** Enviar dados de saúde (mesmo que anonimizados) para servidores de terceiros (EUA) pode violar o TCLE.  
  * **Custo Variável (OpEx):** Paga-se por mensagem. Se o bot ficar popular, o projeto não tem verba recorrente para pagar a conta.  
  * **Validação Impossível:** Como validar um bot que pode dar uma resposta diferente a cada dia?

### **Opção C: Abordagem Híbrida Local** 

### *Orquestrador de fluxos (Botpress/Typebot) \+ LLM Local (Llama 3).*

* **Prós (Vantagens):**  
  * **Privacidade Total:** Os dados nunca saem da máquina da UFES.  
  * **Custo Fixo (CapEx):** Custo único de hardware, zero custo por mensagem.  
  * **Segurança com Flexibilidade:** Usa fluxos fixos para protocolos perigosos (dosagens) e IA para entender a intenção do usuário.  
* **Contras (Desvantagens):**  
  * **Complexidade Técnica:** Exige configurar hardware, Linux, Docker e Ollama.  
  * **Exigência de Hardware:** Precisa de uma máquina com GPU (Placa de Vídeo) para não ficar lento.

---

## **2\. Trade-offs de Infraestrutura (Onde vai rodar?)**

O maior gargalo identificado é o hardware, já que o orçamento do projeto prevê apenas periféricos (HDs), e não computadores de alto desempenho.

### **Cenário 1: Rodar na Nuvem (Cloud VPS / API)**

* **Trade-off:** Facilidade vs. Custo/Privacidade.  
* **Análise:** É o jeito mais fácil de começar, mas insustentável a longo prazo sem verba de custeio. Além disso, a LGPD e ética em pesquisa de saúde dificultam o uso de nuvens públicas estrangeiras sem contratos corporativos caros.

### **Cenário 2: Rodar Localmente (On-Premise na UFES)**

* **Trade-off:** Privacidade/Custo Zero vs. Hardware Necessário.  
* **Análise:** Resolve o problema ético e financeiro, mas cria um problema logístico: **precisamos de uma máquina capaz.**  
* **Requisito Mínimo de Hardware para LLM Local (Llama 3 8B):**  
  * **GPU:** Nvidia RTX 3060 (12GB VRAM) ou superior.  
  * **RAM:** 16GB a 32GB.  
  * **Armazenamento:** SSD NVMe.  
  * *Sem essa GPU, o chat demorará 20 a 40 segundos para responder, inviabilizando o uso.*

---

## **3\. Síntese para Tomada de Decisão**

Para avançar com a **Opção Híbrida Local**, precisamos mitigar o risco do Hardware:

1. **Validar Recursos Existentes:** Verificar se os laboratórios da UFES ou os grupos de pesquisa parceiros possuem *Workstations* com GPU Nvidia ociosas ou disponíveis para o servidor do projeto.  
2. **Plano B (Low-Code):** Se não houver hardware, teremos que recuar para a **Opção A (Determinística)**, usando IA apenas no desenvolvimento (para ajudar a escrever os fluxos) e não na execução final com o usuário.

