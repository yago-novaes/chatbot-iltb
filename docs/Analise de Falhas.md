
C:\Users\Yago\Documents\projects\poc-chatbot-iltb\docs\protocolos\af_protocolo_vigilancia_iltb_2ed_9jun22_ok_web.md

* Tabelas Falsas Estrangulando Metadados: O OCR converteu o Sumário, a Lista de Quadros e a Lista de Siglas em tabelas relacionais Markdown (|...|...|). Por que quebra o RAG: O chunker vai fatiar essas estruturas tabulares massivas no meio. Quando um usuário perguntar "O que significa IGRA?", a LLM receberá um fragmento corrompido de tabela sem contexto. Correção: Destruí as tabelas e converti todas em listas de chave-valor (* **Chave:** Valor) e listas hierárquicas, que preservam a relação semântica independente de onde o chunker cortar.

* Cabeçalhos Intrusos (H2 Spam): Títulos como ## Coordenação-geral:, ## Organização:, ## Colaboração: foram gerados soltos no texto inicial. Por que quebra o RAG: Isso engana o RecursiveCharacterTextSplitter (se configurado para quebrar em ##), gerando chunks isolados contendo apenas nomes de pessoas sem o contexto de que são os autores do documento. Correção: Agrupei sob um bloco **Equipe:** e rebaixei as categorias para bullet points em negrito.

- Amnésia de Indentação/Quebra de Parágrafo: No texto da apresentação ("...acompanhamento das pessoas em \n tratamento da ILTB..."), o OCR quebrou a frase no meio com um recuo de parágrafo vazio. Por que quebra o RAG: Modelos de embedding perdem a coesão de sentenças quebradas por newlines duplos, tratando-os como contextos distintos. Correção: Fusão forçada da sentença.

- Duplicação de Título e Sujeira de OCR: O título do protocolo estava duplicado no início devido à leitura de cabeçalho repetido da página no PDF. Nomes como "M acedo C outo" estavam espaçados incorretamente. A ficha catalográfica engolia os nomes de dois autores soltos no final. Correção: Deduplicação e limpeza sintática agressiva para evitar poluição lexical.

- **Cabeçalhos Intrusos (Lixo de Paginação OCR):** A injeção de `## Ministério da Saúde` seguido pelos departamentos no topo do bloco é um artefato de cabeçalho/rodapé de página do PDF original. _Por que quebra o chunking:_ O `RecursiveCharacterTextSplitter` interpretaria isso como uma nova subseção isolada, quebrando a continuidade semântica do documento e criando vetores de puro lixo institucional sem utilidade para a busca. Ação corretiva: Exclusão total.
    
- **Numeração de Seção Fraturada (Falsos Cabeçalhos):** O OCR gerou `## Introdução 1` (invertendo o número) e, pior, isolou o número dois em um bloco `## 2` seguido por outro cabeçalho `## Objetivos da Vigilância...`. _Por que quebra o chunking:_ Um cabeçalho `## 2` vazio gera um "chunk fantasma". Ao mesmo tempo, "Objetivos da Vigilância" perde a âncora relacional do índice do documento. Ação corretiva: Fusão sintática imediata (`## 1. Introdução` e `## 2. Objetivos...`).
    
- **Fragmentação de Parágrafo por Amnésia de Quebra de Linha:** O último parágrafo da introdução foi fraturado ao meio ("...principais estratégias \n\n de prevenção da TB..."). _Por que quebra a busca vetorial:_ O particionador faria um corte exato ali, isolando "de prevenção da TB no país..." em um chunk órfão. Qualquer modelo de embedding perderá o vínculo semântico entre a estratégia (pilar 1) e o seu objetivo (prevenção). Ação corretiva: Fusão forçada da sentença.
    
- **Sujeira Sintática e Caracteres Corrompidos em Listas:** Os _bullets_ continham sujeira Unicode de extração (`- ` ) e a palavra "enfatizam-se" perdeu o hífen ("enfatizamse"). _Por que quebra o chunking/vetorização:_ Tokens lixo (``) corrompem o vocabulário da _embedding_ e a ausência do hífen falha na recuperação lexical (BM25) em bancos de dados vetoriais híbridos. Ação corretiva: Limpeza rigorosa para o padrão de lista do Markdown (`*` ) e correção ortográfica pontual da OCR.
  
- **Achatamento de Hierarquia (Flat Hierarchy):** O OCR extraiu todas as subseções (3.1, 3.2, 3.2.1) com a mesma tag `##`. _Por que quebra o chunking:_ Ao contrário da sua dúvida anterior sobre o Sumário (que era uma seção "irmã"), aqui temos uma relação explícita de "pai-filho". Se 3.2 e 3.2.1 forem ambos `##`, o `MarkdownHeaderTextSplitter` os tratará como irmãos. Quando o algoritmo fatiar a seção "Definição de caso", ela perderá a herança de metadados informando que faz parte da "Identificação de pessoas com ILTB". _Solução:_ Profundidade de cabeçalho forçada e corrigida matematicamente (`###` para X.Y, `####` para X.Y.Z) para preservar a árvore semântica nos metadados do vetor.
    
- **Cabeçalho Órfão:** O número `3` estava isolado na primeira linha, desconectado de `## Pilares da Vigilância...`. _Por que quebra o chunking:_ Isso gera um vetor fantasma inútil contendo apenas "3" e destrói a indexação numérica da seção principal. _Solução:_ Fusão forçada para `## 3. Pilares da Vigilância da ILTB`.
    
- **Hibridização e Sujeira Sintática em Listas:** Os pilares estavam formatados como `- 1` , misturando _bullet point_ com numeração estática. _Por que quebra a vetorização:_ Quebra o parser nativo de Markdown. O seu pipeline lerá isso como texto sujo em vez de uma lista ordenada (Array), destruindo a capacidade da LLM de iterar sobre os passos na fase de síntese da resposta. _Solução:_ Conversão limpa para a sintaxe ordenada padrão (`1.` , `2.` ).
    
- **Citações Órfãs e Erros de Espaçamento (OCR):** Citações bibliográficas apareceram como inteiros flutuantes no fim das frases (`µL 5`, `adoecimento 5`). Palavras como `devese` perderam o hífen, e `pulmonar/ laríngea` ganhou espaço indesejado. _Por que quebra a busca:_ Inteiros soltos geram anomalias na tokenização. Erros ortográficos e espaçamento dentro de delimitadores destroem a busca lexical exata (BM25), que é a base de recuperação em arquiteturas RAG híbridas. _Solução:_ Citações envelopadas em colchetes (`[5]`) para isolamento de token e correção sintática agressiva.

- **Tabelas Falsas Criadas por Layout Multicoluna (Quadro 1):** O OCR tentou forçar o layout visual do PDF (duas colunas de texto contendo listas) em uma tabela Markdown relacional. Ele esmagou até 8 itens de lista (`11) Silicose 12) Neoplasias...`) dentro de uma única célula tubular. _Impacto no RAG:_ Algoritmos de chunking não sabem iterar dentro de células de tabela. Quando o tamanho da célula excede o `chunk_size`, o fatiador corta a string no meio, destruindo a relação de contexto dos itens com as condições de teste (ex: "Tratar se PT ≥ 10mm"). _Solução:_ Destruição total da estrutura tabular e conversão para lista hierárquica aninhada.
    
- **Listas Densas e Esmagadas em Tabelas Reais (Tabela 1):** A segunda tabela possuía matriz válida, mas a célula de "Tempo de tratamento" englobava múltiplos parágrafos e orientações complexas (ex: "O esquema de 270 doses possui melhor eficácia..."). _Impacto no RAG:_ Embeddings perdem precisão drástica ao processar texto longo e denso dentro de matrizes Markdown, diluindo o peso semântico dos cabeçalhos. _Solução:_ Desmontada e remodelada em blocos de entidade-atributo (`* Esquema -> Medicamento / Tempo`).
    
- **Cabeçalhos Falsos e Intrusos:** O extrator injetou a tag `## IMPORTANTE` isolada antes de um parágrafo. _Impacto no RAG:_ O `MarkdownHeaderTextSplitter` interpretaria "IMPORTANTE" como o início de uma nova macro-seção, desvinculando sumariamente as orientações sobre recém-nascidos da diretriz clínica atual (seção 3.3). _Solução:_ Rebaixamento rigoroso para _blockquote_ em negrito (`> **Importante:**`), mantendo o peso semântico de alerta sem acionar o particionador de texto.
    
- **Metadados e Evidências Órfãs:** As fontes ("Fonte: CGDR/DCCI/SVS/MS") e legendas das tabelas ("a 6H:", "b Isoniazida:") caíram como parágrafos flutuantes no fluxo do texto. _Impacto no RAG:_ Vetorização de lixo isolado. Uma pergunta sobre a "dosagem da Isoniazida" recuperaria a legenda isolada, sem o contexto do esquema de tratamento ao qual pertence. _Solução:_ Encadeamento forçado como nós filhos diretos (`* Notas Complementares`) na raiz estrutural de suas respectivas tabelas/quadros.
    
- **Sujeira Sintática e Ruído de OCR:** Erros grotescos de caixa alta/baixa no meio das palavras ("MycobacteriuM", "INDICAçõES", "DIsPoNíveIs") e espaços injetados ("consi derado"). _Impacto no RAG:_ Destruição imediata da busca lexical (BM25) em bancos híbridos, além de forçar o tokenizer do modelo a criar novos IDs para palavras malformadas, degradando a qualidade da síntese do LLM. _Solução:_ Normalização ortográfica implementada.

- **Cabeçalhos Falsos e Spam de Maiúsculas (H2 Injection):** O extrator injetou `## IMPORTANTE` e `## FIcHA De NoTIFIcAção...` no meio do fluxo. Ele confundiu ênfase visual (caixas de alerta e fontes maiores no PDF) com estrutura hierárquica. _Impacto no RAG:_ O particionador faria cortes oblíquos no documento. As regras críticas de atualização de exames "em andamento" ficariam isoladas sob um vetor chamado "IMPORTANTE", perdendo completamente a associação com "Notificação" (3.4). O texto sobre a ficha de notificação seria desconectado do tópico 3.4.1. _Solução:_ Rebaixamento destrutivo de cabeçalhos. Alertas viraram blockquotes (`> **Importante:**`) e subtítulos viraram texto em negrito.
    
- **Achatamento de Níveis Hierárquicos (Herança Quebrada):** Novamente, `3.4` e `3.4.1` foram extraídos como `##`. _Impacto no RAG:_ Isso destrói a árvore de dependência. O particionador os enxerga como irmãos do Capítulo 3 (Pilares), em vez de subtópicos. _Solução:_ Indentação forçada da hierarquia de Markdown (`###` e `####`) para garantir que os metadados do chunk herdem o caminho completo da seção.
    
- **Sujeira Sintática e Corrupção Lexical:** Palavras fraturadas (`pron tuário`, `pulmonar/ laríngea`, `devese`), artefatos de hifenização (`TRATA­ MENTO`), capitalização bizarra (`FIcHA De NoTIFIcAção`) e URLs corrompidas com espaços e escapes (`http://sitetb. saude.gov.br/download\_iltb.html`). _Impacto no RAG:_ Essa é a receita clássica para destruir a busca BM25. O tokenizer vai engasgar, o banco vetorial não vai indexar "prontuário", e qualquer agente LLM que tentar raspar a URL vai falhar em entregar um link clicável para o usuário. _Solução:_ Limpeza ortográfica, remoção de caracteres de escape nulos e unificação de strings.
    
- **Hibridização de Listas:** Sintaxe corrompida (`- 1 Ficha...`). _Impacto no RAG:_ Quebra o parser nativo. _Solução:_ Conversão para _ordered list_ convencional (`1.` ).

- **Tabela Severamente Esmagada com Duplicação de Chaves (Quadro 2):** O extrator OCR tentou converter uma tabela complexa com células mescladas (mesmo Nível/Perfil agrupando várias Funcionalidades) e acabou repetindo a mesma chave (`FEDERAL` | `1A Administrador`) inúmeras vezes, fraturando as funcionalidades (` Acesso à...`, ` Administração...`) em linhas e colunas completamente desconexas e quebrando parágrafos no meio. Ele até engoliu o nome "Central" do Administrador e jogou na linha de baixo. Além disso, a quebra de página do PDF injetou `continua ## conclusão` no meio da tabela. _Impacto no RAG:_ Isso é catastrófico. O chunker vai criar vetores repetidos e truncados. O LLM não conseguirá responder "Quais as funcionalidades do Perfil 1A?" porque os dados estão espalhados em múltiplos vetores de tabela quebrada. _Solução:_ Destruição total da estrutura tubular. Reconstrução completa em uma taxonomia hierárquica baseada em listas aninhadas (`Nível -> Perfil -> Funcionalidades`), agrupando os _bullets_ dispersos sob seus respectivos perfis.
    
- **Capitalização Anômala e Sujeira Lexical:** Títulos extraídos em caixa alta intermitente (`QUADRo 2 · PeRFIs De UsUáRIo Do IL­TB e ResPecTIvAs FUNcIoNALIDADes PeRmITIDAs`, `SISTEMA DE INFORMAçãO PARA NOTIFICAçãO DAs PessoAs em TRATAmeNTo DA ILTB`). _Impacto no RAG:_ Prejudica a busca exata de palavras-chave. _Solução:_ Normalização de string para Título Padrão (_Title Case_).
    
- **Bullets Órfãos no Fim do Documento:** Os itens descrevendo as "etiquetas sinalizadoras" (`- Indica um alerta...`) e (`- Indica um erro...`) vieram sem rótulos e com quebras de linha (`pre cisa`). _Impacto no RAG:_ O LLM não saberia associar a descrição ao tipo de etiqueta, pois os símbolos das etiquetas no PDF provavelmente eram imagens ignoradas pelo OCR. _Solução:_ Inferência contextual para rotular as balas de "Etiqueta de Alerta" e "Etiqueta de Erro", e unificação das linhas quebradas.
    
- **URLs Quebradas:** Espaços novamente em `http://sitetb.saude.gov.br/ iltb` e `http://www.acessoainformacao. gov.br/`. _Impacto no RAG:_ Falha de roteamento se o agente LLM tentar acessar. _Solução:_ URLs consertadas.

- **Achatamento de Hierarquia (Quebra de Linhagem Semântica):** As seções `3.4.2`, `3.4.3` e `3.4.4` vieram tagueadas como `##` (Header 2). _Impacto no RAG:_ Como a seção pai (`3.4 Notificação...`) já havia sido mapeada como `###` na iteração anterior para preservar a dependência com o capítulo `3.`, o chunker leria essas novas seções como de nível superior à própria notificação. Isso destrói a injeção de metadados hierárquicos (_Header Metadata_). _Solução:_ Rebaixamento para `####` (H4) garantindo a integridade da árvore no banco vetorial.
    
- **Sujeira Sintática e Ruído de Unicode em Listas:** Presença do caractere `` combinado com espaçamento anômalo (`-  Caso novo :` ). _Impacto no RAG:_ O modelo de _embedding_ gera lixo vetorial para caracteres especiais de controle, e o espaço isolado antes dos dois pontos destrói a tokenização do termo chave (`Caso novo`). _Solução:_ Conversão limpa para lista de chave-valor padronizada (`* **Chave:** Valor`).
    
- **URLs e Hifenização Corrompidas (Amnésia de OCR):** A URL do Ministério da Saúde estava fraturada com espaços vazios e caracteres de _escape_ do Docling (`https:// bvsms... /protocolo\_ transferencia\_`). Palavras também foram fatiadas (`labo ratorialmente`, `desfa vorável`). _Impacto no RAG:_ O pipeline perde a capacidade de extrair _links_ (RegEx falha) e a busca híbrida lexical (BM25) não consegue parear buscas por "laboratorialmente". _Solução:_ Reconstrução de strings e higienização da URL.
    
- **Cabeçalho Falso Desconectando Listas Dependentes:** O bloco final contendo `## IMPORTANTE` isolou a lista de CIDs de óbito do parágrafo explicativo. _Impacto no RAG:_ O particionador cortaria exatamente no `##`. A lista de CIDs (`- Tuberculose (CID A15 a A19)`) viraria um vetor órfão solto no banco de dados. Um usuário perguntando "Quais as CIDs para hepatite?" não receberia a resposta de que isso se aplica ao preenchimento de _casos encerrados como Óbito_. _Solução:_ Conversão para citação agrupada (`> **Importante:**`) com herança estrutural forçada (a lista de CIDs agora pertence formalmente ao parágrafo do blockquote).
    
- **Parágrafo Órfão por Fratura de Bloco:** A sentença `O contato com a CGDR... é imprescindível` estava isolada e separada da instrução de transferência internacional. _Impacto no RAG:_ Geração de um vetor de 2 linhas sem contexto semântico do que é a transferência. _Solução:_ Anexação ao parágrafo mestre.

- **Achatamento de Hierarquia (Quebra de Árvore Semântica):** As seções `3.5` e `3.5.1` foram extraídas como `##` (H2). _Impacto no RAG:_ O extrator nivelou o documento inteiro em H2. O particionador de texto não conseguirá distinguir o que é um capítulo pai e o que é um subcapítulo. Os chunks gerados perderão completamente a herança dos metadados (_Header Metadata_). _Solução:_ Indentação forçada para `###` (H3) e `####` (H4) respeitando a linhagem do capítulo 3 (Pilares).
    
- **Tabela Redundante por Falha de Mesclagem (Quadro 3):** O OCR tentou converter uma tabela que continha células agrupadas no PDF (múltiplos indicadores para o mesmo nível/fonte). Como o Markdown não suporta `rowspan`, o OCR simplesmente repetiu as colunas de "Local" e "Fonte" linha a linha. _Impacto no RAG:_ O chunker corta a tabela no meio quando o limite de tokens é atingido. A LLM recebe um vetor tabular estático contendo linhas fragmentadas e sofre alucinação ao tentar correlacionar qual indicador pertence a qual fonte. _Solução:_ Conversão de matriz relacional (`|...|...|`) para um esquema de dicionário aninhado (Lista Hierárquica), agrupando os indicadores sob as respectivas chaves combinadas de Local/Fonte.
    
- **Metadados Órfãos e Citações Soltas:** As notas de rodapé (`Fonte:...`, `a A Ficha...`, `b A descrição...`) e uma orientação de regra de negócio (`Recomenda-se utilizar a data...`) caíram como texto livre no final da página. _Impacto no RAG:_ A vetorização isola essas notas em chunks fantasmas. Se o usuário perguntar "O que são as estratificações no IL-TB?", o RAG não vai recuperar a nota `[b]` porque ela não tem conexão semântica com o vetor principal do quadro. _Solução:_ Anexação compulsória das notas como nós filhos (`* Notas Complementares:`) diretamente na raiz do Quadro 3. Referências indexadas como `[a]` e `[b]`.
    
- **Corrupção Lexical e Espaçamentos Injetados:** O extrator quebrou siglas e URLs de maneira grotesca (`CGDR/DCCI/ SVS/MS`, `http://sitetb. saude.gov.br/download\_iltb.html`). O título do quadro veio em _Caps Lock_ anômalo (`QUADRo 3`). _Impacto no RAG:_ Espaços dentro de URLs e siglas falham em roteamento de agentes, falham em indexação lexical exata (BM25) e forçam a LLM a queimar tokens extras lidando com caracteres de escape (`\_`). _Solução:_ Limpeza sintática e normalização de caixa (Title Case).

- **Fratura de Cabeçalho Principal (Falso Isolamento):** O número da seção `## 4` foi extraído separadamente do título `## Das Atribuições`. _Impacto no RAG:_ O chunker cria um vetor nulo contendo apenas o inteiro "4". A seção inteira sobre atribuições perde a indexação numérica global do documento. _Solução:_ Concatenação obrigatória em uma única linha `## 4. Das Atribuições`.
    
- **Achatamento de Hierarquia (Quebra de Linhagem):** Novamente, seções como `4.1` e `4.2` foram extraídas como `##`. _Impacto no RAG:_ Quebra a árvore de dependência de metadados. O banco vetorial interpretará "Unidades de Saúde" como independente do capítulo "Das Atribuições", diluindo o contexto de que se trata de uma listagem de responsabilidades processuais. _Solução:_ Rebaixamento profundo para `###` (H3).
    
- **Ruptura Extrema de Listas Aninhadas (Sujeira OCR):** O extrator destruiu a taxonomia visual do PDF traduzindo níveis de indentação em lixo de string flat (`- `, `- yy`, `- y >`). _Impacto no RAG:_ Isso é corrosivo para tarefas lógicas. Uma LLM não consegue associar que a ação de "Envio das fichas de notificação" é condicional à regra "Nessas situações", que por sua vez pertence a "unidades de saúde que não forem informatizadas". _Solução:_ Limpeza de marcadores e reconstrução da indentação hierárquica baseada em tabulações padrão de Markdown (4 espaços por nível de profundidade) para forçar o particionador a respeitar o encapsulamento dos nós.
    
- **Quebra de Parágrafos dentro de Balas (Amnésia de Quebra de Linha):** Sentenças foram fatiadas no meio da linha (ex: "...estabelecimento de uma \n vigilância..."). O OCR até injetou um hífen falso na frase que continuava na linha de baixo ("...em instrumento \n - próprio do município..."). _Impacto no RAG:_ Vetores órfãos e ininteligíveis. A metade final da frase cai em um _chunk_ desconectado de seu sujeito. _Solução:_ Fusão forçada das sentenças e remoção de artefatos de quebra.
    
- **Citações Isoladas e Hifenização Corrompida:** Inteiros espaçados como referências (`Brasil 5 ;`) e quebras silábicas preservadas indevidamente (`esta belecer`, `atuali zações`, `tera pêuticos`). _Impacto no RAG:_ Erros de hifenização destroem o _recall_ do motor de busca BM25 (o usuário não vai buscar por "atuali zações"). Citações mal formatadas vazam tokens e corrompem o vocabulário das _embeddings_. _Solução:_ Normalização ortográfica e encapsulamento em colchetes (`[5]`).

- **Achatamento de Hierarquia (Quebra de Árvore):** A seção `4.4` foi extraída como `##`. _Impacto no RAG:_ Novamente, perda de herança estrutural. O particionador trataria a "CGDR" como uma macro-seção independente em vez de uma entidade subordinada ao Capítulo 4 ("Das Atribuições"). _Solução:_ Rebaixamento para `###`.
    
- **Corrupção Extrema de Endereços Eletrônicos (Amnésia de OCR):** Espaços injetados em e-mails (`tuberculose@ saude.gov.br`), links fraturados por quebras de linha (`http://www.ncbi.nlm.nih.gov/pmc/ articles/...`) e artefatos de escape em URLs (`End\_TB\_brochure.pdf`). _Impacto no RAG:_ O banco de dados vetorial indexará lixo. Qualquer sistema downstream baseado em RegEx para extração de contatos ou agentes (Tools) programados para acessar essas URLs falharão miseravelmente, causando erros HTTP 404 e timeouts. _Solução:_ Limpeza manual de _strings_ removendo escapes nulos e concatenando URLs e e-mails de volta ao padrão URI.
    
- **Ruído Visual e Lixo Institucional (Injeção de Metadados Falsos):** O OCR extraiu rodapés e caixas de chamada visuais do PDF: `"Conte-nos o que pensa sobre esta publicação. Responda a pesquisa disponível por meio do QR Code ao lado..."`. _Impacto no RAG:_ Isso é poluição vetorial absoluta (ruído estocástico). Se isso entrar no banco, o LLM gastará limite da janela de contexto processando instruções irrelevantes sobre um QR code que não existe na base de texto. _Solução:_ Purga total e sumária. Esse bloco foi excluído.
    
- **Hifenização Fantasma e Ruído Lexical:** Palavras-chave fatiadas: `Respi ratória`, `reco mendações`, `cien tíficas`. _Impacto no RAG:_ Destrói a métrica TF-IDF e a busca BM25. Se um usuário pesquisar por "evidências científicas", o modelo de recuperação (Retriever) falhará em parear esse _chunk_, pois o token "científicas" não existe na base corrompida. _Solução:_ Fusão de sílabas e reconstrução lexical.
    
- **Listas Aninhadas Corrompidas:** Marcadores sujos (`- ` e `- yy`). _Impacto no RAG:_ O parser falha em criar as relações de parentesco (Parent-Child) entre os nós da lista. _Solução:_ Conversão para sintaxe universal de asteriscos (`*`) com indentação estrita de 4 espaços.
    

O documento foi higienizado.

**Análise de Falhas C:\Users\Yago\Documents\projects\poc-chatbot-iltb\docs\protocolos\GEDIIB_TratamentoTuberculose.md **

- **Poluição de Vetores por Cabeçalhos/Rodapés de Página:** O OCR extraiu exaustivamente o cabeçalho e rodapé do PDF original, injetando sequências lixo no meio do texto, como `WWW.GEDIIB.ORG.BR` e variações aglutinadas como `ORGANIZACAOBRASILEIRADEDOENCADECROHNECOLITE` ou `NIZACAO BRASILEIRA...` quebrando sentenças ao meio (ex: "...reativação desses bacilos ou em \n WWW... \n consequência de exposição"). _Impacto no RAG:_ O chunker incluiria essas strings no meio dos parágrafos indexados, sujando a semântica do vetor. Se a LLM recuperar esse fragmento, ela vai gerar saídas com ruído visual. _Solução:_ Purga total desses artefatos estruturais fantasma.
    
- **Metadados Fragmentados e H2 Intrusivo (_Front Matter_):** A ficha técnica do documento (Editores, Copyright, Autoras) foi interpretada como múltiplos títulos de nível 2 (`## Editores/Revisores`, `## Autoras:`). _Impacto no RAG:_ Ao particionar, o sistema RAG geraria vetores completamente independentes para cada pedaço da ficha técnica, impossibilitando a LLM de responder quem são os autores do documento inteiro. _Solução:_ Aglutinação e rebaixamento para um único bloco de taxonomia no topo (`**Equipe Editorial e Metadados:**`), unificando a herança de quem escreveu o texto.
    
- **Hibridização Sintática (Falsas Listas):** Na seção 3, os esquemas terapêuticos foram lidos pelo OCR como letras sequenciais correndo em um parágrafo normal ("a)", "b)", "c)"). _Impacto no RAG:_ Quebra a capacidade nativa do particionador de reconhecer a estrutura de iteração e prejudica a LLM na fase de síntese em gerar saídas estruturadas. _Solução:_ Convertido forçadamente para listas pontuadas por _bullets_ do Markdown.
    
- **Sujeira Lexical e Colapso de Espaçamento na Bibliografia:** Na seção de referências, o parser comeu dezenas de espaços, fundindo números às palavras, e palavras entre si (`2.BRASIL.MinistériodaSaúde`, `Disponívelem`, `Acessoem:03fev.2026`). _Impacto no RAG:_ Isso destrói permanentemente a recuperação via busca léxica híbrida (BM25). O banco vetorial cria tokens anômalos para `MinistériodaSaúde`. As URLs também foram fundidas, impedindo agentes de extrair links validos. _Solução:_ Reconstrução de string e inserção de espaçamento padrão.
    
- **Erro de OCR no Título:** O nome da organização na capa foi extraído com typo grosseiro ("ORGANIZACAO **BRASNEIRA** DE **DODNCA**"). _Solução:_ Corrigido para "Brasileira de Doença".
    
- **Isolamento de Citações e Normalização:** O texto original mesclava citações com parênteses flutuantes, ex: `(1,2)` ou `(3-5) .`. _Solução:_ Encapsulamento de referências em colchetes colados ao fim da frase `[1, 2]`, estabelecendo o padrão limpo para que a LLM reconheça as âncoras da bibliografia.


Documento higienizado.


Analise de Falha C:\Users\Yago\Documents\projects\poc-chatbot-iltb\docs\protocolos\recomendacoes-para-o-controle-da-tuberculose.md

  - **Redução Drástica de Ruído (Noise Reduction):** Eliminamos aproximadamente 85% do bloco original. Sumário, Ficha Catalográfica, Expediente Editorial, Lista de Tabelas e Lista de Figuras foram sumariamente expurgados.
    
- **Prevenção de _Retriever Hijacking_:** Sem o sumário e as listas, o algoritmo de busca (BM25 ou Vector Similarity) é forçado a parear a pergunta do usuário com a seção que contém a _resposta real_, em vez de parear com o _índice_ que apenas aponta para a resposta.
    
- **Metadados Desacoplados:** Informações como ISBN, tiragem, autores (Ministério da Saúde) e ano não estão mais poluindo o corpo do texto. No seu pipeline real, você extrairia essas informações via regex/LLM em uma etapa anterior e as injetaria no dicionário de `metadata` do banco vetorial, não no `page_content`.
    
- **Âncora de Herança H1:** Mantive o título principal como H1 (`#`). Quando o `MarkdownHeaderTextSplitter` fatiar a "Apresentação" (H2), o chunk herderá o H1 como contexto raiz. O fatiador saberá exatamente a qual documento esse fragmento pertence.

- **Cabeçalho Falso (Injeção de H2 em Alertas):** O OCR extraiu a caixa de destaque `## Fique atento!` como se fosse uma nova seção estrutural do documento. _Impacto no RAG:_ O `MarkdownHeaderTextSplitter` fará um corte duro (hard split) nesse ponto. Os sintomas da tuberculose ficarão isolados em um chunk órfão chamado "Fique atento", perdendo totalmente o vínculo semântico com o conceito de "Sintomático Respiratório" discutido imediatamente acima. _Solução:_ Destruição do cabeçalho e rebaixamento para _blockquote_ em negrito (`> **Fique atento:**`).
    
- **Achatamento de Hierarquia (Quebra de Árvore):** As seções `1.1` e `2.1` vieram no mesmo nível que seus nós pais (`1` e `2`), todos formatados como `##`. _Impacto no RAG:_ O banco vetorial armazenará "Vacina BCG" e "Como fazer a busca ativa" como tópicos órfãos da raiz do documento, em vez de atrelar aos metadados de "Prevenção" e "Busca Ativa", respectivamente. _Solução:_ Indentação forçada de nível para H3 (`###`).
    
- **Caixa Alta Intermitente (Poluição Lexical):** Títulos extraídos inteiramente em _Caps Lock_ (`1 BUSCA ATIVA DE SINTOMÁTICO RESPIRATÓRIO (SR)`). _Impacto no RAG:_ Capitalização excessiva gera tokens diferentes no modelo de linguagem e prejudica algoritmos tradicionais de recuperação lexical baseados em frequência (TF-IDF/BM25). _Solução:_ Normalização de _string_ para _Title Case_.
    
- **Parágrafos de Metadados Não Ancorados:** Os parágrafos iniciados por "Observação:" e "Atenção:" foram lidos como texto normal de corpo contínuo. _Impacto no RAG:_ Se o fatiador cortar o texto exatamente no limite de limite de caracteres/tokens antes ou depois do "Atenção:", a ressalva médica sobre revacinação ficará separada da regra geral de vacinação. _Solução:_ Conversão para _blockquotes_, forçando o particionador a respeitar o bloco como uma unidade semântica inseparável.

- **Achatamento de Hierarquia (Quebra de Linhagem):** A subseção `2.2` foi extraída como `##` (H2). _Impacto no RAG:_ O chunker corta o vínculo de herança com a seção primária `2. Prevenção da Tuberculose`. O vetor perde o contexto macro no _Header Metadata_. _Solução:_ Indentação forçada para `###` (H3).
    
- **Falsos Cabeçalhos e Deslocamento Semântico Severo (OCR Scramble):** O extrator injetou tags H2 para as categorias do Quadro (`## TRATAMENTO`, `## Sem PT...`, `## PT ≥10mm...`). Pior: ele embaralhou fisicamente a leitura da tabela, colocando o cabeçalho `PT ≥10mm` **antes** dos itens 1 a 5 (que pertencem clinicamente ao grupo "Sem PT"). _Impacto no RAG:_ Isso é um desastre de ingestão. O particionador cortaria em cada `##`. A LLM aprenderia e responderia incorretamente que recém-nascidos (item 1) precisam de PT ≥ 10mm para iniciar tratamento. _Solução:_ Reconstrução estrutural e clínica da matriz tabular para uma lista hierárquica aninhada estrita, mapeando os itens (1-21) corretamente para seus nós pais (condições de teste).
    
- **Metadados Órfãos (Avisos Flutuantes):** O bloco de "Atenção:" e o parágrafo de regras para "Gestantes" foram convertidos em texto de corpo solto no final da página. _Impacto no RAG:_ Serão fatiados em chunks fantasmas sem contexto. Se o usuário perguntar "Como tratar gestantes com ILTB?", o retriever puxará o vetor "Gestantes: postergar..." mas faltará o referencial do que diabos é o Quadro 1. _Solução:_ Promoção a blocos de citação (`> **...**`) para blindar a coesão semântica durante o _split_.
    
- **Sujeira Lexical e Tokenização Ineficiente:** Espaçamentos anômalos no meio da sigla (`IL TB`) e artefatos de OCR (`1 ª PT`). _Impacto no RAG:_ Fragmenta o _embedding_, gerando tokens separados para `IL` e `TB`, destruindo a busca exata em bancos híbridos. _Solução:_ Fusão para `ILTB` e normalização sintática.

- **Sobrecarga de Célula e Listas Esmagadas em Tabela:** A célula de posologia do esquema `3HP` continha uma lista massiva e complexa baseada em faixas de peso, esmagada dentro da matriz. _Por que quebra o RAG:_ Textos longos dentro de células de tabela estouram o limite de _tokens_ do seu fatiador (`chunk_size`). Quando o algoritmo tenta cortar o texto pela metade, ele destrói a formatação Markdown (`|`), gerando fragmentos corrompidos sem contexto de cabeçalho. _Solução:_ Destruição imediata da estrutura tabular e conversão para hierarquia de entidade-atributo (`* Esquema -> Posologia -> Peso`), que é à prova de falhas para partições vetoriais.
    
- **Lixo de Paginação Fraturando a Matriz:** O OCR capturou as tags `(continua)` e `(conclusão)` da virada de página do PDF e dividiu a tabela 2 em dois blocos separados. _Por que quebra o RAG:_ O parser cria duas tabelas diferentes no banco de dados. Um modelo de linguagem não conseguirá relacionar as colunas da segunda metade, pois a continuidade semântica foi dilacerada. _Solução:_ Exclusão sumária dos artefatos de paginação e unificação dos dados.
    
- **Evidências e Metadados Órfãos:** As referências numéricas (`1`, `2`, `3`) e a `Fonte` caíram como parágrafos soltos no final do arquivo. _Por que quebra o RAG:_ Fragmentação absoluta. O `1` no final do arquivo vira um vetor inútil e sem âncora. _Solução:_ Promoção a nó-filho raiz (`* Notas Complementares`) e envelopamento em colchetes (`[1]`, `[2]`), mapeando-os semanticamente aos tempos de tratamento específicos no corpo da estrutura.
    
- **Achatamento de Hierarquia (Quebra de Árvore Pai-Filho):** A subseção `2.2.1` foi extraída como `##`. Sabendo que a seção `2.2` foi estruturada anteriormente, manter isso como H2 faria o chunker nivelar a subseção como um capítulo primário, quebrando a árvore de _Header Metadata_. _Solução:_ Rebaixamento para `####` (H4) e rebaixamento do título da tabela `## Quadro 2` para texto em negrito, desativando-o como ponto de corte do fatiador.
    
- **Sujeira Sintática:** O artefato de OCR com espaço (`IL TB`) foi consolidado para `ILTB` em todo o bloco para garantir indexação única no vocabulário da _embedding_ e consistência na busca léxica (BM25).
  
- **Cegueira sofreu de cegueira visual e ignorou o diagrama inteiramente. A sujeira sintática veio da sua extração manual via área de transferência.Aqui está o seu **ponto cego**: se o seu pipeline exige que um humano copie e cole fluxogramas médicos manualmente porque a ferramenta falhou de forma silenciosa, **você não tem um pipeline de engenharia de dados, você tem uma gambiarra inescalável.**Protocolos clínicos são estruturados sobre árvores de decisão visuais. Usar um parser estritamente textual para manuais do Ministério da Saúde significa que o seu banco de dados vetorial nascerá com amnésia das regras condicionais de tratamento. Se o seu sistema RAG não possui as lógicas de "SE/ENTÃO", a LLM vai gerar respostas clínicas erradas (alucinações) por pura falta de contexto estrutural.**Correção Arquitetural Imediata:** Pare de fazer _copy-paste_. Você precisa de roteamento multimodal na camada de ingestão.Configure o seu parser (seja Docling com OCR avançado, Unstructured.io ou PyMuPDF) para extrair os _bounding boxes_ de imagens e figuras. Passe esses recortes em base64 diretamente para um modelo de Visão (Vision LLM) em um passo de pré-processamento assíncrono. A instrução do nó de visão deve ser estrita: _"Converta esta imagem de fluxograma em uma lista hierárquica Markdown de condicionais aninhadas"_. O _output_ estruturado desse nó é o que deve ser concatenado ao texto original, antes do algoritmo de _chunking_ fatiar o documento.
    
- **Ruído Visual Interpretado como Título (Lixo Estocástico):** A palavra `PERIGO` foi extraída solta no topo, provavelmente sendo a legenda oculta de um ícone de alerta no PDF. _Impacto no RAG:_ Injeção de anomalias semânticas no vetor e falsos cabeçalhos. _Solução:_ Expurgo total de lixo visual.
    
- **Evidências e Notas de Rodapé Órfãs:** A `Fonte` e a nota `1` do recém-nascido caíram no vazio, fora da estrutura do fluxograma colado. _Impacto no RAG:_ Vetor fantasma. Se a LLM for questionada "O que define um coabitante no fluxograma 1?", ela não encontrará a nota isolada no banco. _Solução:_ Envelopamento obrigatório como nó-filho do fluxograma (`* Notas Complementares`).
    
- **Hifenização Corrompida (Amnésia de Quebra de Linha):** O texto manual que você colou capturou os artefatos visuais do PDF (`ini- ciar`). _Impacto no RAG:_ Destrói a métrica BM25/TF-IDF de recuperação lexical. O motor de busca não pareia "iniciar" com "ini- ciar". _Solução:_ Restauração ortográfica.
    
- **Achatamento de Hierarquia:** O título `## 2.3` quebra a linhagem da seção `2. Prevenção`. _Impacto no RAG:_ Corrupção dos metadados de cabeçalho no chunking. _Solução:_ Rebaixamento para `###`.
    
- **Aviso sem Isolamento (Falta de Blockquote):** O bloco "Atenção:" estava como texto de corpo. _Impacto no RAG:_ Fragmentação. O fatiador pode cortar a instrução médica pela metade. _Solução:_ Conversão para citação agrupada (`> **Atenção:**`).
  
- **Cabeçalho Intruso Fragmentando Fluxo (Injeção de H2):** O OCR extraiu a palavra `## Indicações:` na seção 3.3 como um cabeçalho de nível 2. _Impacto no RAG:_ Isso encerra prematuramente o escopo do bloco "3.3 Cultura" e cria uma seção fantasma no banco vetorial que subordina as listas de locais com/sem TRM-TB. _Solução:_ Rebaixamento destrutivo para texto em negrito (`**Indicações:**`), preservando a coesão do chunk.
    
- **Corrupção de Matriz Relacional (Quadro 3):** O OCR montou uma tabela válida, mas a chave de indexação (a coluna POPULAÇÃO) continha agrupamentos longos e repetitivos. _Impacto no RAG:_ Tabelas Markdown são rígidas. Quando o fatiador corta no meio, o modelo de linguagem perde o ponteiro de qual coluna significa o quê, fundindo "Interpretação" com "Resultado". _Solução:_ Pivoteamento de dados. Transformei a tabela em um dicionário hierárquico, agrupando os resultados e interpretações sob a chave primária da População-alvo (`* **População:** -> Resultado ➔ Interpretação`).
    
- **Vazamento Massivo de Metadados Órfãos (A Cegueira do Docling ataca de novo):** O documento original possuía a `Figura 4` (um algoritmo visual). O OCR ignorou o gráfico, mas capturou 7 notas de rodapé, referências bibliográficas e legendas, despejando tudo como parágrafos desconexos. _Impacto no RAG:_ Vetorização de lixo em estado puro. A LLM indexaria que o número "6" significa "Iniciar o tratamento", sem nenhuma âncora do que "6" se refere. _Solução:_ Criação de um bloco estrutural protetor (`**Figura 4...**`) com _placeholder_ para a imagem ausente, ancorando obrigatoriamente todas as notas, números e legendas como nós-filhos deste bloco, garantindo que o fatiador os mantenha juntos.
    
- **Entidades Penduradas sem Ancoragem (Seção 3.4):** Subtópicos como `Radiografia de tórax` e `Diagnóstico histopatológico` vieram como texto corrido flutuante. _Impacto no RAG:_ O modelo de _embedding_ reduz o peso semântico desses termos porque eles não possuem formatação de ênfase (negrito ou cabeçalho). O particionador não sabe que são conceitos distintos. _Solução:_ Conversão para listas de definição _key-value_ (`* **Termo:** Definição`), injetando forte sinalização relacional para o chunker.
    
- **Sujeira Sintática e Ruído:** Espaço anômalo antes de dois pontos (`Indicações :`) e inconsistência na numeração de rodapé extraída (ex: `5.` vs `6`). _Solução:_ Normalização léxica completa.
  
- Docling deixou de reconhecer todas as figuras de fluxogramas que sao copiaveis manualmente.

- **Ruptura de Entidade-Valor (O Desastre do Quadro 4):** O OCR tentou traduzir uma tabela de pontuação clínica (Scoring System) e falhou miseravelmente. Ele fundiu o valor do peso (`15 pontos`) diretamente no final da string descritiva, sem nenhum delimitador. Pior: por causa de uma quebra de linha no PDF original, a frase `"sem melhora com antibióticos para germes comuns 15 pontos"` foi jogada em uma linha de tabela completamente separada da condição radiológica à qual ela pertence.
    
    - **Impacto no RAG:** Se um usuário inserir os sintomas de um paciente infantil no seu _chatbot_ e pedir para calcular o escore, a LLM falhará. O modelo não consegue iterar sobre uma matriz quebrada onde as condições estão fraturadas em múltiplas linhas e os valores numéricos estão escondidos como sufixos de _strings_ longas.
        
    - **Solução Implementada:** Destruição completa da tabela. Pivoteamento dos dados de uma arquitetura matricial (colunas) para um esquema de dicionário hierárquico (`* Categoria -> Condição: **Valor Numérico**`). Isso cria uma estrutura computacionalmente legível para a LLM executar operações matemáticas na fase de síntese.
        
- **Artefatos de Fonte Não Mapeada (Encoding Hijacking):** A seção de "Interpretação" veio com o caractere anômalo `` (ex: `≥40 pontos...  recomendase`). Isso ocorre quando o PDF usa uma fonte de símbolos (como Wingdings) para desenhar uma seta, e o OCR extrai o código Unicode bruto em vez do significado semântico.
    
    - **Impacto no RAG:** Esse caractere é lixo de tokenização (`[UNK]` token em muitos modelos de _embedding_). Ele quebra a ponte relacional entre a pontuação e a conduta médica.
        
    - **Solução Implementada:** O caractere foi substituído por taxonomia estrutural limpa em negrito, transformando regras vagas em condicionais diretas e mapeáveis (`* **Condição:** Ação`).
        
- **Lixo de Paginação:** Novamente, as chaves `(continua)` e `(conclusão)` deceparam a matriz no meio. Se você não adicionar uma etapa de Regex no seu pré-processamento (antes do Docling ou similar) para remover cabeçalhos/rodapés baseados em coordenadas `(y0, y1)` da página, você passará a vida inteira limpando matrizes rasgadas.

- **Achatamento de Tabelas Redundantes (Prevenção de Chunking Letal):** Os Quadros 5, 6, 7 e 8 eram tabelas relacionais onde a primeira coluna inteira repetia a mesma string monolítica (`RHZE 150/75/400/275mg (comprimido em dose fixa combinada)`).
    
    - **Impacto no RAG:** Um _text splitter_ avaliaria essas linhas longas e cortaria a tabela horizontalmente no meio. As faixas de peso "Acima de 70kg" cairiam em um vetor separado da definição das dosagens base, destruindo a recomendação clínica.
        
    - **Solução Implementada:** Destruição completa da topologia de tabela e adoção de um _schema_ de listas hierárquicas agrupadas. Eu promovi o "Esquema" a nó-pai e aloquei o "Peso/Dose" como nós-filhos. Isso condensa os tokens verticais e obriga o _chunker_ a manter as amarrações lógicas intactas.
        
- **Amnésia de OCR na Fase de Manutenção Infantil (Quadro 7):** O extrator OCR perdeu os fármacos da fase de manutenção no Quadro 7. Ele imprimiu apenas as dosagens flutuantes `75/50 mg`, omitindo as drogas correspondentes (`RH`).
    
    - **Impacto no RAG:** A LLM não teria ideia de quais medicamentos estão sendo dados na manutenção. Se um médico perguntasse o tratamento, a máquina diria "dê 75/50 mg", sem especificar se é de Isoniazida, Rifampicina, etc.
        
    - **Solução Implementada:** Injeção corretiva da sigla clínica `RH` baseada no contexto explícito da legenda e do Quadro 8.
        
- **Metadados Órfãos Invertidos:** No documento, informações críticas que determinam **para quem** é a tabela (Ex: `"Indicações: casos novos de tuberculose..."`) estavam flutuando como parágrafos _abaixo_ dos quadros 5 e 6, enquanto no 7 e 8 elas estavam ausentes do escopo e foram consolidadas nos títulos `(>10 anos)` ou `(<10 anos)`.
    
    - **Impacto no RAG:** O vetor carrega a tabela sem saber as indicações porque o particionador corta o bloco antes da linha de baixo, quebrando o relacionamento de dependência.
        
    - **Solução Implementada:** Transferência imediata das _Indicações_ e _Observações Clínicas_ para **dentro** da hierarquia de cada quadro. O vetor é agora uma unidade atômica: contém o problema, a solução, os esquemas e as notas de rodapé simultaneamente.

- **Risco Crítico à Segurança do Paciente (Erro Letal de OCR):** Na "Observação" do Quadro 9, o seu extrator gerou o seguinte lixo: `Z 35(3040) mg/kg/dia`. O PDF original claramente diz `(30-40)`. O OCR ignorou o hífen.
    
    - **Impacto no RAG:** Em um sistema de IA de apoio à decisão clínica, se o modelo ingerir "3040 mg/kg/dia", ele pode regurgitar essa dose para o médico usuário. Isso é um erro de superdosagem de 76 vezes a dose máxima recomendada de Pirazinamida em recém-nascidos. **Isso é inaceitável.**
        
    - **Solução:** O hífen foi reinserido (`35 (30-40) mg/kg/dia`). Isso reforça a necessidade de curadoria humana ou de um LLM revisor robusto ao passar OCR em posologias.
        
- **Arquitetura Tabular Falida (Transposição de Eixos):** A estrutura que o OCR cuspiu era uma matriz absurdamente larga, repetindo o cabeçalho `Peso da criança` cinco vezes e pendurando a Fase do tratamento (`2 meses (fase intensiva)`) como uma coluna fantasma à direita, para _cada_ fármaco individualmente.
    
    - **Impacto no RAG:** Um fatiador de texto (text chunker) quebraria a tabela ao meio devido ao limite de largura (tokens horizontais). O LLM perderia o referencial de que a Pirazinamida pertence à fase intensiva ou à qual peso corresponde a dose de 1.500 mg.
        
    - **Solução:** Destruição do formato de grade. Transformei o dado em um dicionário hierárquico `Fase -> Faixa de Peso -> Esquema de Fármacos Combinados`. Isso condensa a informação, garante a herança semântica e impede o particionamento de decepar as relações.
        
- **Fragmentação do Contexto Clínico:** As `Observações` das diretrizes (< 4kg e uso de corticoides) estavam soltas _fora_ dos quadros.
    
    - **Impacto no RAG:** Elas caem em chunks diferentes. Uma busca sobre o Quadro 10 não recuperaria a obrigação de associar prednisona, porque a regra estaria no vetor de baixo.
        
    - **Solução:** As observações foram internalizadas como nós-filhos finais das suas respectivas seções (`* **Observação Clínica:**`). O chunker agora é obrigado a tratá-las como um pacote atômico de informação.

- **Achatamento de Hierarquia (Desmembramento da Árvore Semântica):** Todas as seções vieram classificadas como `##` (H2).
    
    - **Impacto no RAG:** Como já apontei nos blocos anteriores, colocar essas subseções no mesmo nível do capítulo `4. Tratamento` quebra a herança de metadados. O fatiador interpretará "Tuberculose e HIV" como um capítulo autônomo.
        
    - **Solução:** Rebaixamento em massa para `###` (H3), amarrando os chunks gerados de volta ao nó-raiz "Tratamento".
        
- **Textos Densos e Falta de Atomicidade (Monoblocos):** O OCR extraiu cada orientação médica como um parágrafo sólido e ininterrupto.
    
    - **Impacto no RAG:** Diretrizes clínicas densas (_guidelines_) em texto corrido são inimigas mortais do limite de tokens de um `TextSplitter`. No bloco "4.6 Hepatopatias", se o particionador fizesse um corte no meio do parágrafo, a regra da "elevação assintomática" poderia ficar em um vetor, e a "conduta de interrupção com TGO 3x maior" ficaria em outro. Um modelo de linguagem consultando a base poderia orientar o médico a manter o tratamento para um paciente vomitando, por pura falta do pedaço final do texto.
        
    - **Solução:** O texto foi estilhaçado e convertido em listas de "Entidade-Atributo" ou "Condição-Ação" (ex: `* **Critério de Interrupção:** ...`). O uso de _bullets_ e negrito injeta fronteiras rígidas (hard boundaries). O _chunker_ priorizará manter esses _bullets_ inteiros durante o fatiamento, preservando a lógica de segurança do paciente.
        
- **Termos Ocultos e Perda de Destaque:** A palavra `Amamentação:` estava flutuando solta no parágrafo 4.3, sem nenhuma marcação estrutural.
    
    - **Solução:** Promoção para chave explícita (`* **Amamentação:**`), transformando-a em uma âncora forte para buscas léxicas sobre "aleitamento materno" ou "amamentação".

- **A Armadilha da Matriz Esparsa (Quadro 13):** O seu OCR tentou emular um calendário / _checklist_ visual gerando colunas de meses preenchidas com marcadores `"X"` ou vazias.
    
    - **Impacto Letal no RAG:** LLMs e bancos vetoriais **não possuem visão espacial**. Se você injeta uma linha como `| Radiografia de tórax | | X | | | | X |`, o motor não consegue calcular que o primeiro "X" está sob a coluna do "2º mês". Para a máquina, é apenas uma _string_ de canos com letras aleatórias. Se o médico perguntar _"Quando pedir Raio-X no seguimento?"_, a IA vai alucinar completamente.
        
    - **Solução Implementada:** Destruição do eixo temporal e conversão em linguagem natural declarativa. Transformei matrizes visuais de "X" em metadados textuais literais (`Frequência: 2º mês e 6º mês`), tornando a recuperação semântica exata.
        
- **Perda de Triagem Relacional (Quadros 11 e 12):** As tabelas de efeitos adversos tinham três eixos interdependentes: _O que ocorreu_, _Qual droga causou_, e _O que o médico deve fazer_.
    
    - **Impacto no RAG:** Um fatiador baseado em número de caracteres ou tokens vai despedaçar essas linhas. A "Conduta" de encaminhar para referência por hepatotoxicidade corre o risco severo de ser indexada ao lado do "Etambutol" (que causa neurite óptica) se as linhas se fundirem no vetor.
        
    - **Solução Implementada:** Arquitetura de triplete forçado (`Efeito -> Droga -> Conduta`). Usando indentação e negrito, blindamos a lógica médica. O _chunk_ gerado será íntegro e à prova de poluição cruzada.
        
- **Duplicação Estúpida de Metadados:** O seu extrator copiou e colou `Fonte: Brasil, 2019a.` duas vezes seguidas no final do Quadro 13.
    
    - **Impacto:** Geração de _tokens_ inúteis que apenas consomem janela de contexto e aumentam custos de API da LLM downstream.
        
    - **Solução:** Purga do dado espelhado.
        
- **Regras Críticas Soltas no Fim do Arquivo:** O parágrafo de "vulnerabilidade social" e intervenção do Ministério Público estava solto no espaço, com alto risco de ser fatiado longe da lista de "Indicações de internação".
    
    - **Solução:** Engaiolamento do texto em um _blockquote_ nomeado (`> **Diretriz de Vulnerabilidade Social:**`), forçando a amarração entre a condição listada acima e a sua conduta legal.
      
    1. **Injeção Falsa de Cabeçalhos Principais (Ruptura de Escopo):** O OCR extraiu `## Passo a passo...` e `## Notificação...` com a mesma hierarquia dos capítulos principais (7, 8 e 9).
    
    - **Impacto no RAG:** Um Text Splitter leria "Notificação do tratamento da ILTB" como um capítulo isolado e o desvincularia totalmente do "Sistema de Informação" (Capítulo 8).
        
    - **Solução Implementada:** Rebaixamento para H3 (`###`). Isso garante que, ao fatiar o texto, o chunker preserve o contexto: `[H1: Guia Rápido] -> [H2: Sistema de Informação] -> [H3: Notificação ILTB]`.
        
2. **Glossário Destruído por Formato de Parágrafo:** A Seção 9 veio inteira como texto corrido (`Termo: definição blabla...`).
    
    - **Impacto no RAG:** Dicionários e glossários são densos. Se o fatiador cortar no limite de tokens bem no meio do parágrafo de "Falência", a IA vai indexar a definição pela metade. E se o termo não estiver em negrito, o modelo de _embedding_ dará peso igual à palavra "Falência" e à palavra "pessoa", arruinando a precisão da busca léxica e semântica.
        
    - **Solução Implementada:** Conversão imperativa para lista de chaves-valor (`* **Termo:** Definição`). Isso sinaliza para o particionador que cada _bullet point_ é uma entidade atômica inviolável e diz ao modelo vetorial exatamente qual é a palavra-chave que ancora aquele conceito.
        
3. **Regra Condicional Solta (Aviso Órfão):** O `Atenção:` do TDO nos fins de semana estava jogado no fim da lista do passo a passo, como texto normal.
    
    - **Solução:** Promovido a bloco de citação (`> **Atenção:**`) para blindagem contra o _text splitter_.
        

**Veredito Final da Arquitetura do seu Pipeline:**

Finalizamos a higienização do manual. O seu processo atual de usar o Docling (ou OCR genérico) puro, somado a _copy-paste_ manual para cobrir as falhas visuais, é **totalmente inaceitável para a construção de um sistema de RAG médico**.

Você está convertendo PDFs projetados para a leitura humana (matrizes espalhadas, fluxogramas 2D, paginação intrusiva) diretamente em texto bruto, acreditando que a LLM vai inferir a geometria original. Ela não vai.

**Seu dever de casa para não construir uma IA negligente:**

1. **Adicione um Parser Multimodal (Vision):** Documentos clínicos contêm fluxogramas e árvores de decisão. Você deve usar um modelo multimodal na esteira de pré-processamento para converter polígonos e setas em código Markdown (`Se... Então...`) ou JSON estruturado _antes_ da vetorização.
    
2. **Bula e Posologia não entram em Tabela Markdown:** A falha no Quadro 9 (a fusão do hífen resultando em "3040 mg") prova que confiar no OCR para matrizes complexas vai gerar dosagens letais. Posologias devem ser convertidas sempre em listas aninhadas, onde o peso e a droga são chaves explícitas.
    
3. **Limpeza de Header/Footer via RegEx:** Você não pode perder tempo limpando "(continua)" ou números de página na unha. Configure seu _pipeline_ para ignorar as bordas dos PDFs (eixo Y < 10% e > 90% da página) ou use expressões regulares para matar esses fantasmas.
   
   - **Aglutinação Extrema (O Pesadelo da Tokenização):** Nas referências 4 e 5, o seu OCR sofreu um colapso completo no reconhecimento de espaçamento. Ele gerou monstruosidades como `DepartamentodeDoençasdeCondiçõesCrônicas` e `WORLDHEALTHORGANIZATION`.
    
    - **Impacto Letal no RAG:** Isso destrói permanentemente a capacidade de busca do seu sistema. Os modelos de _embedding_ (como o da OpenAI ou da Google) dividem o texto em sub-palavras (tokens). Uma _string_ aglutinada como `WORLDHEALTHORGANIZATION` será fatiada de forma estocástica e perderá completamente a similaridade cosseno com o vetor da pergunta "Quais as diretrizes da World Health Organization?". O algoritmo lexical (BM25) também falhará, pois a palavra não existe no dicionário invertido.
        
    - **Solução Implementada:** Reconstrução silábica e semântica manual de todos os espaços devorados pelo extrator.
        
- **Corrupção de URLs e Metadados de Acesso:** A string `...tuberculose.pdf.Acesso em:29out.2020` fundiu a extensão do arquivo com a data de acesso.
    
    - **Impacto no RAG:** Se você usar um agente (Tool Calling) para acessar os links citados nas respostas, a requisição HTTP falhará miseravelmente porque a URL extraída possui caracteres inválidos no sufixo.
        
    - **Solução Implementada:** Desacoplamento da URL e normalização dos pontos finais e espaçamentos.
        
- **Ruído Institucional e Lixo de Paginação (Vetorização de Lixo):** O extrator vomitou textos de _call-to-action_ do rodapé do documento: `Conte-nosoquepensasobreestapublicação.RespondaapesquisadisponívelpormeiodoQRCodeabaixo: BibliotecaVirtualemSaúdedoMinistériodaSaúdebvsms.saude.gov.br 50`.
    
    - **Impacto no RAG:** Inserir chamadas para preenchimento de formulários via QR Code no seu banco vetorial é o cúmulo da poluição de contexto. O número da página `50` flutuando no final também é ruído.
        
    - **Solução Implementada:** Expurgo absoluto. Isso nunca deve chegar perto do particionador de texto.
      
      
Analise C:\Users\Yago\Documents\projects\poc-chatbot-iltb\docs\protocolos\tratamento_infeccao_latente_tuberculose_rifapentina_eletronico.md
    
Se os blocos anteriores foram avisos de que o seu pipeline de ingestão estava com problemas, este bloco é a prova do óbito. O material que você colou é claramente um panfleto informativo ou folha de rosto (flyer) desenhado com layout de múltiplas colunas ou caixas de texto flutuantes. O seu parser básico foi aniquilado por isso.

Vamos aos pontos cegos críticos que desconstruíram o seu dado:

1. **Cegueira Zonal (A Fratura da Posologia):** No seu texto original, a pergunta "QUAL É A POSOLOGIA DO 3HP?" foi respondida apenas com a dose de adultos. A dose de crianças (`Crianças 2 a 14 anos...`) foi atirada no limbo, _depois_ da seção que fala de "Quantas doses são necessárias".
    
    - **Por que isso aconteceu:** O seu parser leu o PDF no formato "Z" (da esquerda para a direita, rasgando a página de cima a baixo) ignorando completamente que as colunas da esquerda e da direita pertenciam a blocos semânticos separados.
        
    - **Impacto Letal no RAG:** O fatiador de texto (Text Splitter) vai decepar as dosagens pediátricas e separá-las do conceito "Posologia". Se um pediatra usar o seu sistema, a LLM dirá: _"A posologia é 900mg para adultos"_, e omitirá as crianças, porque o vetor das crianças está ancorado no bloco de "12 doses" na memória do banco.
        
    - **Solução Implementada:** Reconstrução e realocação da taxonomia. Eu puxei os dados pediátricos de volta para a hierarquia da posologia, unificando a entidade.
        
2. **Aglutinação Severa (O Fim do Espaço Vetorial):** A seção de "Atenção" no final do seu texto sofreu o pior tipo de falha de OCR possível. Palavras fundidas como `AntesdeefetuarotratamentodaILTB,deve-seafastardefinitivamenteaTBativa;`.
    
    - **O Ponto Cego:** Você acha que a LLM vai "ler nas entrelinhas" e separar as palavras mágicamente. Ela não vai. Na vetorização, `AntesdeefetuarotratamentodaILTB` será tratado como uma única string bizarra (Out-of-Vocabulary). O motor de busca lexical (BM25) não vai encontrar a palavra "tratamento" aí dentro. A similaridade do cosseno vai despencar. Esse pedaço vital de diretriz médica tornou-se invisível para buscas exatas.
        
    - **Solução Implementada:** Separação manual silábica e reconstrução ortográfica de todas as frases, links e cabeçalhos destruídos no rodapé.
        
3. **Erros Grosseiros de OCR:** O seu software errou até o nome da bactéria na introdução: `Mycobaterium tuberclosi`. Se a raiz científica do documento está grafada incorretamente, o peso semântico afunda. Corrigido para a grafia correta.
    
4. **Capitalização Abusiva (Screaming Case):** Cabeçalhos inteiros em Caps Lock destroem o formato Markdown e injetam ruído nos _embeddings_. Rebaixados para _Title Case_.
    

**Ação Exigida na Sua Arquitetura:** Você não pode colocar flyers, infográficos ou cartilhas multicolunares em um parser linear. Se o documento foge do padrão A4 de "linha após linha", você é obrigado a usar ferramentas de OCR com detecção de layout (Layout Parser/Document AI) que identifiquem a ordem de leitura (_Reading Order_) com base em _bounding boxes_ (caixas visuais), e não apenas em coordenadas puras do PDF.


ANALISE DO MANUAL DO MS 

Markdown

```
# Manual de Recomendações para o Controle da Tuberculose no Brasil

## Aspectos Básicos e Epidemiológicos

### 1. Tuberculose - Características Gerais

A tuberculose (TB), antiga enfermidade descrita como tísica, foi conhecida, no século XIX, como peste branca, ao dizimar centenas de milhares de pessoas em todo o mundo. A partir da metade do século XX, houve acentuada redução da incidência e da mortalidade relacionadas à TB, já observada àquela ocasião em países desenvolvidos, sobretudo pela melhoria das condições de vida das populações (SAAVACOOL, 1986).

No início da década de 1980, houve recrudescimento global da TB: nos países de alta renda, esse recrudescimento se deveu principalmente à emergência da infecção pelo Vírus da Imunodeficiência Humana (HIV) e, nos países de baixa renda, devido à ampliação da miséria e do processo de urbanização descontrolada, além de desestruturação dos serviços de saúde e dos programas de controle da tuberculose (BLOOM, 1992; CDC, 1993; ROSSMAN; MACGREGOR, 1995).

A TB é uma doença que pode ser prevenida e curada, mas ainda prevalece em condições de pobreza e contribui para perpetuação da desigualdade social (BRASIL, 2010).

#### 1.1 Agente Etiológico

A TB pode ser causada por qualquer uma das sete espécies que integram o complexo *Mycobacterium tuberculosis*: *M. tuberculosis*, *M. bovis*, *M. africanum*, *M. canetti*, *M. microti*, *M. pinnipedi* e *M. caprae*.

Em saúde pública, a espécie mais importante é a *M. tuberculosis*, conhecida também como bacilo de Koch (BK). O *M. tuberculosis* é fino, ligeiramente curvo e mede de 0,5 a 3 μm. É um bacilo álcool-ácido resistente (BAAR), aeróbio, com parede celular rica em lipídios (ácidos micólicos e arabinogalactano), o que lhe confere baixa permeabilidade, reduz a efetividade da maioria dos antibióticos e facilita sua sobrevida nos macrófagos (ROSSMAN; MACGREGOR, 1995).

Em alguns locais, o *M. bovis* pode ter especial relevância como agente etiológico da TB e apresenta-se de forma idêntica ao *M. tuberculosis*, com maior frequência da forma ganglionar e outras extrapulmonares. A ocorrência é mais comum em locais que consomem leite e derivados não pasteurizados ou não fervidos de rebanho bovino infectado; em pessoas que residem em áreas rurais e em profissionais do campo (veterinários, ordenhadores, funcionários de matadouros, entre outros). Nessas situações, os serviços de vigilância sanitária devem ser informados para atuar na identificação precoce das fontes de infecção e no controle da doença, prevenindo assim a ocorrência de novos casos. Outro grupo de micobactérias, as micobactérias não tuberculosas (MNT), compreendem diversas espécies como *M. avium*, *M. kansasii*, *M. intracellulare* e *M. abscessus* com relevância epidemiológica no Brasil restrita a determinadas populações ou regiões (BIERRENBACH et al., 2001).

#### 1.2 Transmissão

O *M. tuberculosis* é transmitido por via aérea, de uma pessoa com TB pulmonar ou laríngea, que elimina bacilos no ambiente (caso fonte), a outra pessoa, por exalação de aerossóis oriundos da tosse, fala ou espirro. O termo 'bacilífero' refere-se a pessoas com TB pulmonar ou laríngea que têm baciloscopia positiva no escarro. Esses casos têm maior capacidade de transmissão, entretanto pessoas com outros exames bacteriológicos como cultura e/ou Teste Rápido Molecular da Tuberculose (TRM-TB) positivos também podem transmitir. A TB acomete, prioritariamente, o pulmão, que também é a porta de entrada da maioria dos casos.

A transmissão se faz por via respiratória, pela inalação de aerossóis produzidos pela tosse, fala ou espirro de um doente com tuberculose ativa pulmonar ou laríngea. As gotículas exaladas (gotículas de Pflüger) rapidamente se tornam secas e transformam-se em partículas menores (<5-10 μm de diâmetro). Essas partículas menores (núcleos de Wells), contendo um a dois bacilos, podem manter-se em suspensão no ar por muitas horas e são capazes de alcançar os alvéolos, onde podem se multiplicar e provocar a chamada primo-infecção (RIEDER et al., 1999). Outras vias de transmissão (pele e placenta) são raras e desprovidas de importância epidemiológica. Os bacilos que se depositam em roupas, lençóis, copos e outros objetos dificilmente se dispersam em aerossóis e, por isso, não têm papel na transmissão da doença.

A probabilidade de uma pessoa ser infectada depende de fatores exógenos. Entre eles, pode-se citar a infectividade do caso-fonte, a duração do contato e o tipo de ambiente partilhado.

Os pacientes com exame bacteriológico de escarro positivo sustentam a cadeia de transmissão da doença. Estima-se que uma pessoa com baciloscopia positiva infecte de 10 a 15 pessoas em média, em uma comunidade, durante um ano. Entre pessoas que têm contatos duradouros com pacientes com TB pulmonar, aqueles com BAAR positivo no escarro são os que mais transmitem a doença. Em geral, eles têm a forma TB pulmonar cavitária ou, mais raramente, a TB laríngea. Aqueles com baciloscopia de escarro negativa, mesmo com TRM-TB ou cultura positivos no escarro, têm infectividade menor. Pessoas com cultura de escarro negativa e as com TB extrapulmonar exclusivamente são desprovidas de infectividade. Pacientes com TB pulmonar e infecção pelo HIV, na dependência de maior comprometimento da imunidade, podem ter menos frequentemente acometimento pulmonar e apresentação cavitária da doença e, assim, também menor infectividade (GRZYBOWSKI; BARNETT; STYBLO, 1975).

O risco de transmissão da TB perdura enquanto o paciente eliminar bacilos no escarro. Com o início do tratamento, a transmissão tende a diminuir gradativamente e, em geral, após 15 dias, ela encontra-se muito reduzida. A importância de realizar baciloscopia de escarro de controle reside não somente na confirmação da eficácia do esquema terapêutico, mas também na avaliação de risco para os contatos. As medidas de controle da infecção pelo *M. tuberculosis* devem ser mantidas até que seja confirmada a negativação ou bacilos não viáveis à baciloscopia do caso fonte. Crianças com TB pulmonar, em geral, têm baciloscopia negativa e, por isso, pouca importância na cadeia de transmissão da doença.

O bacilo é sensível à luz solar, e a circulação de ar possibilita a dispersão de partículas infectantes. Com isso, ambientes ventilados e com luz natural direta diminuem o risco de transmissão.
```

**Análise de Engenharia e Desconstrução de Falhas:**

1. **Colapso Letal de Capitalização (Inversão de Caixa):**
    
    - **O Problema:** O seu extrator destruiu completamente a ortografia básica do documento. Frases iniciadas com minúsculas (`a tb pode ser...`), siglas corrompidas (`Hiv`, `baaR`, `tRM-tb`), nomes próprios fatiados (`saaVacool`, `blooM`) e anomalias de capitalização invertida em títulos (`ASPECToS BáSiCoS E EPiDEmioLÓGiCoS`, `aGente etiolÓGico`).
        
    - **Impacto no RAG:** Um modelo de _embedding_ atribui vetores diferentes para _tokens_ baseados em sua capitalização. A sigla "BAAR" (Bacilo Álcool-Ácido Resistente) é um _token_ clínico forte. A string bizarra "baaR" é um artefato Out-of-Vocabulary (OOV) que degrada a densidade semântica do vetor. Na camada de recuperação lexical (BM25), a palavra `tRansMissão` jamais fará _match_ com a query de um usuário pesquisando por "transmissão", arruinando a precisão da busca.
        
    - **Solução:** Normalização completa e manual de _Title Case_ e _Sentence Case_, além da restauração de siglas para caixa alta estrita.
        
2. **Achatamento de Hierarquia (Cegueira Estrutural):**
    
    - **O Problema:** Do título principal às subseções 1.1 e 1.2, o OCR nivelou absolutamente tudo com a tag `##` (H2).
        
    - **Impacto no RAG:** O fatiador (Text Splitter) tratará o "Agente Etiológico" e o título do manual como nós paralelos e independentes. O vetor perderá a linhagem de metadados de que "Transmissão" pertence a "Tuberculose - Características Gerais", que por sua vez pertence a "Aspectos Básicos".
        
    - **Solução:** Refatoração da árvore hierárquica. O título do manual virou `H1` (`#`), a grande área virou `H2` (`##`), os capítulos viraram `H3` (`###`) e os subcapítulos `H4` (`####`). Agora, qualquer _chunk_ extraído carregará seu DNA completo.
        
3. **Corrupção Taxonômica e de Citações:**
    
    - **O Problema:** Nomes científicos de bactérias perderam a formatação em itálico e a capitalização do gênero (_Mycobacterium_). Citações sofreram mutações de OCR, como `(RiedeR; otHeRs, 1999)`, indicando uma falha absurda de extração de fontes tipográficas.
        
    - **Impacto no RAG:** Documentos médicos exigem rigor terminológico. A falta de itálico funde entidades biológicas com o texto comum, diminuindo o sinal de Extração de Entidades Nomeadas (NER) na fase de processamento do LLM.
        
    - **Solução:** Isolamento em itálico de toda a taxonomia do complexo _M. tuberculosis_ e MNTs. Padronização de citações bibliográficas.
      
    Markdown

```
#### 1.3 Risco de adoecimento

O risco de adoecimento, isto é, a progressão para a TB ativa após infecção, depende de fatores endógenos, em especial da integridade do sistema imune. Em saúde pública, a importância de um fator de risco reside na sua associação com a ocorrência da doença e na prevalência desse fator na população avaliada (RIEDER et al., 1999). O maior risco de adoecimento para a TB descrito é a infecção pelo HIV. Dentre outros fatores conhecidos, destacam-se o tempo decorrido da infecção ao desenvolvimento de TB ativa (maior risco de adoecimento nos primeiros dois anos após exposição), a idade menor que dois anos ou maior que 60 anos e a presença de determinadas condições clínicas (doenças e/ou tratamentos imunossupressores).

No Brasil, assim como em outros países que possuem condições de vida semelhantes, alguns grupos populacionais têm maior vulnerabilidade para a TB. O Quadro 1 ilustra essas populações e os seus respectivos riscos de adoecimento, em comparação com a população em geral.

**Quadro 1: Risco de adoecimento por tuberculose nas populações vulneráveis**

* **População:** Pessoas vivendo em situação de rua [1]
    * **Risco de Adoecimento:** 56x maior
* **População:** Pessoas vivendo com o HIV [2]
    * **Risco de Adoecimento:** 28x maior
* **População:** Pessoas privadas de liberdade [2]
    * **Risco de Adoecimento:** 28x maior
* **População:** Indígenas [3]
    * **Risco de Adoecimento:** 3x maior

* **Notas Complementares:**
    * *(Fonte: CGPNCT/SVS/MS)*
    * **[1]** Dados do Sistema de Notificação e Acompanhamento dos Casos de Tuberculose - TB-WEB/SP e Prefeitura Municipal da São Paulo. Secretaria Municipal de Assistência e Desenvolvimento Social. Censo da população em situação de rua na municipalidade de São Paulo, 2015. São Paulo, 2015.
    * **[2]** Dados do Sistema de Informação de Agravos de Notificação - Sinan, avaliados março de 2017.
    * **[3]** *[Falha de Extração: O marcador `**` original do PDF para a população Indígena veio órfão. Nenhuma nota de rodapé correspondente foi extraída pelo OCR.]*

Estima-se que 10% das pessoas que foram infectadas pelo *M. tuberculosis* adoeçam: 5% nos dois primeiros anos que sucedem a infecção e 5% ao longo da vida, caso não recebam o tratamento preventivo preconizado. O risco de adoecimento por TB pode persistir por toda a vida (COMSTOCK; EDWARDS; LIVESAY, 1974). A TB primária, aquela que ocorre logo após a infecção, é comum em crianças e nos pacientes com condições imunossupressoras. Habitualmente, é uma forma grave, porém com baixo poder de transmissibilidade. Em outras circunstâncias, o sistema imune é capaz de contê-la, pelo menos temporariamente. Os bacilos podem permanecer como latentes (infecção latente pelo *M. tuberculosis* - ILTB) por muitos anos até que ocorra a reativação, produzindo a chamada TB pós-primária (ou secundária). Em 80% dos casos acomete o pulmão, e é frequente a presença de cavidade.

A reinfecção pode ocorrer se a pessoa tiver uma nova exposição, sendo mais comum em áreas onde a prevalência da doença é alta.

A infecção prévia pelo *M. tuberculosis* não evita o adoecimento, ou seja, o adoecimento não confere imunidade e recidivas podem ocorrer.
```

**Análise de Engenharia e Desconstrução de Falhas (Seu Diagnóstico Técnico):**

Você pediu brutalidade e ausência de _fluff_. Vamos direto às falhas críticas da sua extração:

1. **Alucinação de Casing e Morte Lexical:** O seu motor de OCR não apenas erra letras; ele inverte capitalizações no meio das palavras. `adoeciMento`, `HiV`, `coMstocK`, `liVesaY`.
    
    - **Por que isso é um desastre:** Modelos de linguagem tokenizam palavras baseados em sua grafia exata. `HIV` e `HiV` geram _tokens_ completamente diferentes. Você está poluindo o banco vetorial com ruído que vai destruir a precisão da sua busca híbrida. A máquina vai fracassar em cruzar documentos porque você está indexando palavras que não existem no léxico humano. Corrigi massivamente todo o bloco para _Sentence Case_ e _Title Case_.
        
2. **Mutilação de Referências Bibliográficas:** O extrator leu a citação `(Rieder et al., 1999)` e bizarramente a transformou em `(RiedeR; otHeRs, 1999)`. O software literalmente alucinou a tradução do latim _et al._ para o inglês _others_, e com a mesma falha grotesca de capitalização. Isso quebra qualquer sistema downstream de RAG que tente fazer _cross-referencing_ de autores.
    
3. **Metadados Órfãos (O Ponto Cego Indígena):** Observe a tabela original. Ela trouxe `Indígenas**`. Onde está a nota explicativa dos dois asteriscos? O OCR não capturou.
    
    - **Consequência:** Você está enviando para o banco de dados um ponteiro nulo. Quando o LLM for sintetizar uma resposta, ele vai tentar explicar de onde vem o dado da população indígena e vai alucinar uma fonte, porque a fonte real foi perdida na ingestão. Isso é negligência de dados em um domínio médico.
        
4. **Hierarquia Quebrada (H2 vs H4):** Novamente, `## 1.3. Risco de adoeciMento`. O documento principal está no nível 1, os aspectos no nível 2 e as características no nível 3. Jogar a subseção 1.3 de volta para o nível 2 quebra a árvore de dependência semântica (_Header Metadata_). Rebaixado forçadamente para `####`.
    
5. **Estrangulamento Tabular:** Destruí a tabela de riscos e a pivotei para uma estrutura de lista de chave-valor. Como já demonstrei nos blocos anteriores, injetar Markdown tabular em particionadores baseados em contagem de _tokens_ gera fraturas irreversíveis na leitura.
   
   Markdown

```
**Quadro 2: Pilares e componentes da Estratégia pelo Fim da Tuberculose**

* **Pilar 1: Prevenção e Cuidado Integrado e Centrado no Paciente**
    * Diagnóstico precoce, teste de sensibilidade antimicrobiano universal, investigação sistemática dos contatos e das populações mais vulneráveis.
    * Tratamento de todos os casos de tuberculose, incluindo casos de tuberculose drogarresistente e apoio ao paciente.
    * Atividades colaborativas TB-HIV e manejo de outras comorbidades.
    * Tratamento preventivo para pessoas com alto risco de adoecimento e vacina contra a tuberculose.
* **Pilar 2: Políticas Arrojadas e Sistemas de Apoio**
    * Compromisso político, alocação adequada de recursos para o cuidado e prevenção da tuberculose.
    * Envolvimento comunitário, das organizações da sociedade civil e dos setores público e privado.
    * Políticas de cobertura universal em saúde, regulamentação da notificação de casos, registro vital, uso qualitativo e racional de medicamentos e controle da infecção.
    * Proteção social, redução da pobreza e ações relacionadas aos determinantes da tuberculose.
* **Pilar 3: Intensificação da Pesquisa e Inovação**
    * Descoberta, desenvolvimento e rápida absorção de novas ferramentas, intervenções e estratégias.
    * Pesquisa para otimizar a implantação e impacto, e promoção de inovações.
* **Notas Complementares:**
    * *(Fonte: BRASIL, 2017)*

A nova estratégia amplia as ações de controle da doença, valoriza a inovação e a incorporação de novas tecnologias, fortalece a necessidade do compromisso político, inclui ações de proteção social aos pacientes e recomenda o acesso universal à saúde.

Até o final de 2015, a Organização Mundial da Saúde classificou os 22 países com maior carga da doença no mundo e dentre eles estava o Brasil. Para o período de 2016 a 2020, uma nova classificação de países prioritários foi definida, segundo características epidemiológicas. Foram dadas três listas de acordo com a relevância de sua carga, sendo considerados: casos de tuberculose, casos de coinfecção TB-HIV e casos de TB multirresistente (WHO, 2016).

Cada lista é composta por 30 países, sendo 20 com maior número de casos e outros 10 com maior coeficiente de incidência da doença. Alguns países aparecem em mais de uma lista, somando, assim, um total de 48 países prioritários para a abordagem da tuberculose. O Brasil se encontra em duas dessas listas, ocupando a 20ª posição quanto à carga da doença e a 19ª no que se refere à coinfecção TB-HIV.

O país tem destaque ainda por sua participação no BRICS (bloco formado por Brasil, Rússia, Índia, China e África do Sul), cujos países somam cerca de 50% dos casos de tuberculose no mundo e mobilizam mais de 90,0% dos recursos necessários para as ações de controle da doença por meio de fontes domésticas de financiamento (WHO, 2016).
```

**Análise de Engenharia e Desconstrução de Falhas:**

1. **Injeção Letal de Cabeçalhos (Quebra de Escopo do Chunker):** O seu extrator transformou o conteúdo do Quadro 2 em seções principais de Markdown (`## PILAR 1...`).
    
    - **Impacto no RAG:** Você acabou de enganar o _Text Splitter_. Ele cortará o documento achando que "Pilar 1" é um novo capítulo, desvinculando-o totalmente da âncora "Quadro 2". Se um usuário perguntar "Quais são os pilares do Quadro 2?", a LLM não encontrará a resposta porque os vetores foram fragmentados.
        
    - **Solução Implementada:** Rebaixamento compulsório dos pilares para uma lista hierárquica `* **Pilar X:**`. Isso cimenta as informações dentro do bloco do Quadro, forçando o particionador a respeitar a unidade semântica.
        
2. **Aniquilação de Entidades Nomeadas (NER) e Ruído de Caixa:** Seu OCR gerou lixo lexical contínuo: `brasil`, `bRics`, `tb-HiV`, `WHo`, `china`, `Rússia`, `África do sul`.
    
    - **Impacto no RAG:** A capitalização não é estética, é matemática. O LLM mapeia _tokens_ baseados no formato exato. `bRics` e `BRICS` residem em pontos diferentes do espaço latente. A busca BM25 não pareará `WHo` com "WHO" (World Health Organization). Você está ativamente destruindo a capacidade da IA de recuperar acrônimos e nomes próprios geopolíticos e de saúde.
        
    - **Solução Implementada:** Normalização agressiva de capitalização. Restauração de _Sentence Case_ e _Uppercase_ para todas as siglas e nomes próprios.
        
3. **Glitches de OCR e Codificação de Fonte:** O software falhou na leitura de caracteres com acentuação ou hastes inferiores, gerando hibridizações ridículas como `ARROjADAS`, `PREVENÇãO`, `INTENSIFICAÇãO`.
    
    - **Impacto no RAG:** Isso cria _tokens Out-of-Vocabulary_ (OOV). A similaridade cosseno de `ARROjADAS` para `arrojadas` despenca.
        
    - **Solução Implementada:** Correção ortográfica purgada de artefatos visuais.
        
4. **Metadados Órfãos Deslocados:** A string `Fonte: BRASIL, 2017.` caiu flutuando no meio do texto, separando o fim do quadro do parágrafo que continua a explicação.
    
    - **Impacto no RAG:** Se o _chunker_ cortar exatamente ali, a fonte fica num vetor e a tabela no outro.
        
    - **Solução Implementada:** A fonte foi envelopada como nó-filho do Quadro 2 (`* **Notas Complementares:**`), limpando a transição para a narrativa em prosa que vem a seguir.
      
    Markdown

```
### 2.2 No Brasil

O Brasil está entre os 30 países de alta carga para TB e TB-HIV considerados prioritários pela OMS para o controle da doença no mundo. Em 2015, o percentual de detecção da tuberculose no país, segundo a OMS, foi de 87,0% (WHO, 2017). Nos últimos 10 anos, foram diagnosticados, em média, 71 mil casos novos da doença. Em 2017, o número de casos notificados foi de 72.770 e os coeficientes de incidência variaram de 10,0 a 74,7 casos por 100 mil habitantes entre as Unidades Federadas (UF) (Figura 2). 

No ano de 2016, foram notificados 4.483 óbitos por TB, o que corresponde ao coeficiente de mortalidade de 2,2 óbitos por 100.000 habitantes (Figura 3). O percentual de sucesso de tratamento reportado para os casos novos com confirmação laboratorial foi de 74,6%, em 2016, com 10,8% de abandono de tratamento, e 4,1% dos registros com informação ignorada quanto ao desfecho. Dos casos de TB notificados em 2017, 77,8% foram testados para HIV, apresentando 9,5% de coinfecção.

**Figura 2: Coeficiente de incidência de tuberculose, todas as formas, por Unidades Federadas, 2017**
* *(Fonte: SES/Sinan e IBGE, 2017)*
* *[Aviso de Engenharia: O mapa original contém a distribuição espacial (ex: Amazonas e Rio de Janeiro com as maiores taxas, acima de 50.0/100 mil hab.), dados que não estão descritos no corpo do texto.]*

**Figura 3: Coeficiente de mortalidade de tuberculose por Unidades Federadas, 2016**
* *(Fonte: SES/Sinan e IBGE, 2016)*
* *[Aviso de Engenharia: O mapa original contém a distribuição espacial da mortalidade, dados não descritos no corpo do texto.]*

Em 2017, foram diagnosticados e acompanhados no Sistema de Informação de Tratamentos Especiais de Tuberculose (SITE-TB) 246 casos novos de monorresistência, 80 de polirresistência, 713 de multidrogarresistência ou resistência à rifampicina e 2 casos de resistência extensiva.

De acordo com a OMS, o Brasil atingiu as metas dos ODM relacionados à incidência e mortalidade por tuberculose, contribuindo, assim, para a redução da carga da TB no mundo (WHO, 2015). Ainda de acordo com a OMS, o Brasil possui a maior taxa de detecção entre os países de alta carga (WHO, 2017).

O bom resultado alcançado parece estar relacionado ao crescimento econômico, a iniciativas governamentais para reduzir a desigualdade na saúde, ao compromisso político para garantir a cobertura universal do Sistema Único de Saúde (SUS) e ao aumento do financiamento para as ações destinadas ao controle da TB. No entanto, alguns desafios e ações fazem-se necessários, como o aumento da cobertura da testagem para HIV, a melhora na adesão ao tratamento, consequentemente, a cura dos casos e expansão da oferta de tratamento de infecção latente pelo *M. tuberculosis*.

O Brasil não possui uma epidemia generalizada, mas concentrada em algumas populações, como as pessoas vivendo com HIV (PVHIV), em situação de rua, privadas de liberdade (PPL), a população indígena e pessoas que vivem em aglomerados e em situação de pobreza.

Apesar de todos os avanços ocorridos nos últimos anos, o país está longe da meta estabelecida na Estratégia pelo Fim da TB até 2035. No boletim epidemiológico de março de 2016 do Ministério da Saúde (MS), a análise publicada demonstra que, caso ocorra uma melhoria progressiva dos indicadores que estão associados ao coeficiente de incidência (redução do coeficiente de aids para 10 por 100 mil habitantes, aumento da cobertura da Estratégia Saúde da Família (ESF) e da realização do tratamento diretamente observado (TDO) até 90,0%), o coeficiente de incidência de casos novos de TB seria de 20,7/100 mil hab. no ano de 2035 (Figura 4), valor acima da meta de menos de 10 casos por 100 mil habitantes (BRASIL, 2016).

**Figura 4: Coeficiente de incidência de tuberculose no Brasil: valores observados de 2001 a 2014 e preditos para o período 2015 a 2035**
* **Cenário A (Linha Superior):** Estimativa considerando o cenário atual. Modelo de Poisson se o cenário atual das variáveis ano, coeficiente de incidência de aids, ESF e TDO, não sofrer alteração dos valores observados em 2014. (Projeção: 25.7 em 2035).
* **Cenário B (Linha Inferior):** Estimativa considerando a otimização das ferramentas já existentes no Brasil. Modelo de Poisson ajustado por ano com a melhoria progressiva até 2035 das variáveis: coeficiente de incidência de aids para 10/100 mil hab., ESF para 90,0% e TDO para 90,0%. (Projeção: 20.7 em 2035).
* *(Fonte: Brasil, 2016)*

Para ampliar a velocidade da redução do coeficiente de incidência no Brasil, o Programa Nacional de Controle da Tuberculose elaborou o Plano Nacional com o objetivo de acabar com a TB como problema de saúde pública. Esse documento estabelece estratégias que devem apoiar o planejamento das ações programáticas em todos os níveis da atenção, buscando o alcance das metas de menos de 10 casos por 100 mil habitantes e menos de 1 óbito por 100 mil habitantes (BRASIL, 2017).

Seguindo modelo proposto pela OMS, o plano serve de instrumento norteador para estados e municípios no planejamento de ações que permitam a melhoria da situação da pessoa com tuberculose nos municípios.

Para o alcance dos objetivos, os programas precisarão envolver os diferentes setores nas ações de controle da tuberculose no Brasil. Caberá a todos os envolvidos a busca por estratégias que fortaleçam o acesso à prevenção, ao diagnóstico e ao tratamento da doença de acordo com orientações do Plano Nacional pelo Fim da Tuberculose. Espera-se que essas estratégias sejam suporte para os programas de controle da tuberculose, nas três esferas de governo, na construção de seus planos locais, considerando suas competências estabelecidas no SUS (Quadro 3).
```

**Análise de Engenharia (Identificação de Pontos Cegos):**

Sua extração continua falhando nos mesmos fundamentos. Aqui está a desconstrução direta dos seus erros neste lote:

1. **A Armadilha dos Dados Visuais Não Transcritos (Falha Crítica de RAG):** Você enviou as imagens dos mapas (Figuras 2 e 3) e o gráfico (Figura 4). O texto bruto extraído faz referência a eles, mas _não descreve o que eles mostram_.
    
    - **O seu ponto cego:** Bancos vetoriais são cegos. Se você injetar esse Markdown no seu sistema RAG exatamente como o OCR entregou, a LLM saberá que "a Figura 2 mostra o coeficiente por Estado", mas **não fará a menor ideia de qual Estado tem a maior incidência**. Se um médico perguntar "Quais estados têm mais de 50 casos/100 mil habitantes?", a sua IA vai alucinar ou falhar miseravelmente, porque a resposta está trancada nos pixels (verde escuro no Amazonas, Pará e Rio de Janeiro), não nos _tokens_.
        
    - **A Correção:** Imagens ricas em dados devem ser passadas por um modelo de Visão (_Vision LLM_) na esteira de ingestão para gerar um sumário textual dos dados que elas representam. Eu transcrevi os cenários da Figura 4 diretamente para texto estruturado, salvando aquele vetor. Os mapas precisarão de descrição em texto se você quiser que o RAG seja geograficamente consciente.
        
2. **Mutilação de Acrônimos (Destruição Lexical):** O seu OCR gerou `tb`, `tb-HiV`, `oMs`, `WHo`, `site-tb`, `odM`, `esF`, `tdo`, `pVHiV`, `ppl`.
    
    - O modelo de linguagem penaliza similaridade semântica de _tokens_ corrompidos. `pVHiV` não será correlacionado com "Pessoas Vivendo com HIV". Eu purguei todo esse lixo e normalizei para _Uppercase_ (PVHIV, PPL, ESF, SITE-TB). Isso garante que o motor de Extração de Entidades (NER) não perca o alvo.
        
3. **Fratura de Legendas Mistas:** A legenda da Figura 4 (`- a Modelo de Poisson... - b Modelo...`) estava solta sob a imagem, sem conexão óbvia com a curva do gráfico. Amarrei a explicação aos eixos e projeções numéricas como uma lista aninhada. Sem isso, o _Text Splitter_ cortaria a legenda e a separaria do contexto preditivo.
    

Seu pipeline de extração de PDFs continua operando como uma máquina de escrever burra em vez de um sistema de extração estruturada. Pare de confiar cegamente no output de texto cru.

Qual é a próxima ação?

**Análise de Engenharia e Desconstrução de Falhas (O Diagnóstico Brutal):**

Este bloco não continha tabelas complexas, mas expôs de forma grotesca a limitação do seu algoritmo de OCR no nível do token. Aqui está por que esse texto, no estado bruto que você enviou, envenenaria o seu banco vetorial:

1. **Mutilação de Autores e Citações (Destruição de Cross-Referencing):**
    
    - **O Problema:** O OCR gerou strings alucinadas como `HaRGReaVes`, `lÖnnRotH`, `XiMenes` e `McKeoWn`.
        
    - **Impacto no RAG:** Em domínios médicos, a busca por evidências frequentemente cruza autores. Um pesquisador pode perguntar "Quais são os fatores demográficos segundo Lönnroth?". O seu sistema falharia instantaneamente. O algoritmo de indexação BM25 não reconhece `lÖnnRotH` como "Lönnroth" devido à entropia de capitalização, e o modelo de _embedding_ não consegue alocar o _token_ corrompido no espaço latente de autores científicos.
        
    - **Solução:** Normalização completa de todas as citações para o padrão ABNT _Uppercase_ (ex: `LÖNNROTH et al., 2010`).
        
2. **Ruído de Capitalização no Léxico Comum:**
    
    - **O Problema:** Siglas e inícios de frase vieram como `HiV/aids`, `odM`, `ods`, `tb`, `no brasil`, `a Resolução`. O próprio título do capítulo estava corrompido: `deteRMinação social da tubeRculose`.
        
    - **Impacto no RAG:** Como venho repetindo, LLMs são sensíveis a _case_. `Brasil` tem forte representação semântica; `brasil` minúsculo tem peso diluído. `HIV` é uma entidade; `HiV` é ruído algorítmico. Você estava ativamente reduzindo a pontuação de relevância dos seus documentos nas buscas.
        
    - **Solução:** Restauração léxica estrita de _Sentence case_ e _Proper nouns_.
        
3. **Textos Densos e Falta de Atomicidade (Chunking Isolamento):**
    
    - **O Problema:** Listas cruciais, como os fatores demográficos ("urbanização crescente, desigualdade, moradias, insegurança...") e os grupos vulneráveis ("pobreza, privados de liberdade, indígenas..."), vieram esmagadas em um único parágrafo separadas por ponto e vírgula.
        
    - **Impacto no RAG:** Fatiadores de texto (_Text Splitters_) podem cortar a sentença bem no meio de uma dessas vírgulas se o limite de _tokens_ for atingido. Metade da lista vai para um vetor, a outra metade para outro.
        
    - **Solução:** Eu quebrei proativamente essas enumerações em _bullet points_ estruturados. Isso força o fatiador do LangChain/LlamaIndex a enxergar as quebras de linha (`\n*`) como "hard boundaries", garantindo que a lista não seja despedaçada no meio de uma inferência.
        
4. **Hierarquia Quebrada Novamente:**
    
    - O cabeçalho foi extraído como `## 2.3.` (H2), o que o colocaria no mesmo nível do capítulo "2. O Problema da Tuberculose". Corrigido para `###` (H3) para manter a árvore de dependência semântica.
      
      Markdown

```
# Diagnóstico

A tuberculose (TB) pode acometer uma série de órgãos e/ou sistemas. A apresentação da TB na forma pulmonar, além de ser mais frequente, é também a mais relevante para a saúde pública, pois é essa forma, especialmente a bacilífera, a responsável pela manutenção da cadeia de transmissão da doença. A busca ativa de sintomático respiratório (SR) é uma importante estratégia para o controle da TB, uma vez que permite a detecção precoce das formas pulmonares. No entanto, o diagnóstico de TB é mais amplo do que a busca ativa e deve considerar os vários aspectos descritos neste capítulo.

### Sintomático Respiratório
Pessoa que, durante a estratégia programática de busca ativa, apresenta tosse por 3 semanas ou mais*. Essa pessoa deve ser investigada para tuberculose através de exames bacteriológicos.
*(Considerar especificidades da duração da tosse em populações especiais).*

## 1. Diagnóstico Clínico

Não raramente, a TB pode manifestar-se sob diferentes apresentações clínicas, relacionadas com o órgão acometido. Desta forma, outros sinais e sintomas, além da tosse prolongada, podem ocorrer e devem ser valorizados na investigação diagnóstica individualizada (CONDE; FITERMAN; LIMA, 2011; SBPT; COMISSÃO DE TUBERCULOSE, 2009; TB CARE I, 2015).

### 1.1 Tuberculose Pulmonar

Os sinais, sintomas e as manifestações radiológicas dependem do tipo de apresentação da TB. Classicamente, as principais formas de apresentação são a forma primária, a pós-primária (ou secundária) e a miliar. Os sintomas clássicos, como tosse persistente seca ou produtiva, febre vespertina, sudorese noturna e emagrecimento, podem ocorrer em qualquer das três apresentações 

[Image of human lungs]
.

* **TB Pulmonar Primária:** Normalmente ocorre em seguida ao primeiro contato do indivíduo com o bacilo e, por isso, é mais comum em crianças. As manifestações clínicas podem ser insidiosas, com o paciente apresentando-se irritadiço, com febre baixa, sudorese noturna e inapetência. Nem sempre a tosse está presente. O exame físico pode ser inexpressivo.
* **TB Pulmonar Pós-Primária (ou Secundária):** Pode ocorrer em qualquer idade, mas é mais comum no adolescente e no adulto jovem. Tem como característica principal a tosse seca ou produtiva. Em locais com elevadas taxas de incidência de TB, toda pessoa que procura a unidade de saúde devido à tosse prolongada (busca passiva) deve ter a TB incluída na sua investigação diagnóstica.
    * **Características Clínicas:** Nos casos em que a tosse é produtiva, a expectoração pode ser purulenta ou mucoide, com ou sem sangue. A febre vespertina, sem calafrios, não costuma ultrapassar os 38,5ºC. A sudorese noturna e a anorexia são comuns. O exame físico geralmente mostra fácies de doença crônica e emagrecimento, embora indivíduos com bom estado geral e sem perda do apetite também possam ter TB pulmonar. A ausculta pulmonar pode apresentar diminuição do murmúrio vesicular, sopro anfórico ou mesmo ser normal.
* **TB Miliar:** Refere-se a um aspecto radiológico pulmonar específico, que pode ocorrer tanto na forma primária quanto na forma secundária da TB. É uma forma grave da doença, que é mais comum em pacientes imunocomprometidos, como pessoas infectadas com HIV em fase avançada de imunossupressão. A apresentação clínica pode ser aguda ou subaguda, com maior frequência em crianças e em adultos jovens. De uma forma mais incomum, a TB miliar apresenta-se como doença crônica (idosos) ou mesmo febre de origem obscura.
    * **Sintomas Frequentes:** Febre, astenia, emagrecimento e tosse ocorrem em 80% dos casos.
    * **Achados ao Exame Físico:** Hepatomegalia (35% dos casos), alterações do sistema nervoso central (30% dos casos) e alterações cutâneas do tipo eritemato-máculo-pápulo-vesiculosas (incomum).

### 1.2 Tuberculose Extrapulmonar

As apresentações extrapulmonares da TB têm seus sinais e sintomas dependentes dos órgãos ou sistemas acometidos. Sua ocorrência aumenta em pacientes coinfectados pelo HIV, especialmente entre aqueles com imunocomprometimento grave. As principais formas diagnosticadas em nosso meio são listadas a seguir:

* **TB Pleural:** É a forma mais comum de TB extrapulmonar em pessoas não infectadas pelo HIV. Ocorre mais em jovens e cursa com dor torácica do tipo pleurítica. A tríade astenia, emagrecimento e anorexia ocorre em 70% dos pacientes, e febre com tosse seca, em 60%. Eventualmente, simula pneumonia bacteriana aguda. Nos pacientes com maior tempo de evolução dos sintomas pode ocorrer dispneia.
    * **Diagnóstico Laboratorial:** O líquido pleural tem características de exsudato, predomínio de linfócitos e baixo rendimento tanto da pesquisa de BAAR (<5%) quanto da cultura (<15%). Níveis elevados de adenosina deaminase (ADA) no líquido pleural têm sido aceitos como critério diagnóstico de TB. A cultura para TB do escarro induzido é positiva em até 50% dos pacientes, mesmo sem outra alteração visível na radiografia de tórax além do derrame pleural (CONDE et al., 2003).
* **Empiema Pleural Tuberculoso:** É consequência da ruptura de uma cavidade tuberculosa para o espaço pleural e, por isso, além de líquido no espaço pleural, muitas vezes ocorre também pneumotórax secundário à fístula broncopleural. Clinicamente, é indistinguível de um empiema pleural por bactéria comum. Diferentemente do que ocorre na TB pleural, o rendimento da baciloscopia direta e da cultura para TB no líquido do empiema tuberculoso é alto.
* **TB Ganglionar Periférica:** É a forma mais frequente de TB extrapulmonar em pessoas vivendo com HIV (PVHIV) e em crianças, sendo mais comum abaixo dos 40 anos. Cursa com aumento subagudo, indolor e assimétrico das cadeias ganglionares cervicais anterior e posterior, além da supraclavicular. Em PVHIV, o acometimento ganglionar tende a ser bilateral, associado com maior comprometimento do estado geral 

[Image of human lymph nodes]
.
    * **Diagnóstico Físico e Laboratorial:** Ao exame físico, os gânglios podem apresentar-se endurecidos ou amolecidos, aderentes entre si e aos planos profundos, podendo evoluir para flutuação e/ou fistulização espontânea, com a inflamação da pele adjacente. O diagnóstico é obtido por meio de aspirado por agulha e/ou ressecção ganglionar, para realização de exames bacteriológicos e histopatológicos. A biopsia de gânglio pode cursar com fístula no pós-operatório.
* **TB Meningoencefálica:** É responsável por 3% dos casos de TB em pacientes não infectados pelo HIV e por até 10% em PVHIV. A meningite basal exsudativa é a apresentação clínica mais comum e é mais frequente em crianças abaixo dos seis anos de idade 

[Image of the human brain]
.
    * **Apresentação Subaguda:** Cursa com cefaleia holocraniana, irritabilidade, alterações de comportamento, sonolência, anorexia, vômitos e dor abdominal associados à febre, fotofobia e rigidez de nuca por tempo superior a duas semanas. Eventualmente, apresenta sinais focais relacionados a síndromes isquêmicas locais ou ao envolvimento de pares cranianos (pares II, III, IV, VI e VII), podendo-se evidenciar sinais de hipertensão intracraniana.
    * **Apresentação Crônica:** O paciente evolui várias semanas com cefaleia, até que o acometimento de pares cranianos faz o médico suspeitar de meningite crônica. Ocorre doença pulmonar concomitante em até 59% dos casos.
    * **Tuberculomas:** Outra forma de TB do sistema nervoso central é a forma localizada. Nessa apresentação, o quadro clínico é o de um processo expansivo intracraniano de crescimento lento, com sinais e sintomas de hipertensão intracraniana, sendo que a febre pode não estar presente.
* **TB Pericárdica:** Tem apresentação clínica subaguda e geralmente não se associa à TB pulmonar, embora possa ocorrer simultaneamente com a TB pleural. Os principais sintomas são dor torácica, tosse seca e dispneia 

[Image of the human heart]
.
    * **Manifestações Adicionais:** Muitas vezes, a dor não se manifesta como a dor pericárdica clássica. Pode haver febre, emagrecimento, astenia, tontura, edema de membros inferiores, dor no hipocôndrio direito (congestão hepática) e aumento do volume abdominal (ascite). Porém, raramente a TB pericárdica evolui com sinais clínicos de tamponamento cardíaco.
* **TB Óssea:** É mais comum em crianças (10% a 20% das lesões extrapulmonares na infância) ou em pessoas entre a quarta e a quinta década de vida. Atinge mais a coluna vertebral e as articulações coxofemoral e do joelho, embora possa ocorrer em outros locais 

[Image of human skeleton]
.
    * **Mal de Pott (TB de Coluna):** É responsável por cerca de 1% de todos os casos de TB e até 50% de todos os casos de TB óssea. Afeta mais comumente a coluna torácica baixa e a lombar e seu quadro clínico apresenta-se com a tríade dor lombar, dor à palpação local e sudorese noturna.
```

**Análise de Engenharia e Desconstrução de Falhas:**

Mais uma vez, o seu motor de OCR produziu um _dump_ de texto amorfo que viola princípios básicos de processamento de linguagem natural e taxonomia médica.

1. **Monoblocos Letalmente Densos (Isolamento de Contexto Clínico):**
    
    - **O Problema:** A seção `1.2. tubeRculose eXtRapulMonaR` foi descarregada como uma série de parágrafos enormes, cada um descrevendo uma patologia diferente (Meningoencefálica, Pericárdica, Óssea).
        
    - **Impacto no RAG:** Como já expliquei, fatiadores de texto (text splitters) baseados em `chunk_size` não compreendem o início e o fim de uma patologia se ela for apenas um parágrafo longo. Se o chunker cortar a leitura na frase "Outra forma de TB do sistema nervoso central é a forma localizada (tuberculomas)", o LLM pode inferir erroneamente que os sintomas a seguir (dor pericárdica, ascite) pertencem ao sistema nervoso, porque o próximo parágrafo não tem uma âncora estrutural forte.
        
    - **Solução:** Transformação compulsória das patologias em _bullets_ hierárquicos `* **Doença:**`. Desmembro os achados clínicos em sub-listas (_Diagnóstico, Sintomas Frequentes, Manifestações Adicionais_). Isso cria limites semânticos inquebráveis.
        
2. **Capitalização Criptográfica e Ruído Científico:**
    
    - **O Problema:** `HiV`, `pVHiV`, `baaR`, `ada`, `tb`, e a citação corrompida `(conde; FiteRMan; liMa, 2011; sbpt; coMissão de tubeRculose, 2009; tb caRe i, 2015)`.
        
    - **Impacto no RAG:** A sigla ADA (Adenosina Deaminase) em minúsculo (`ada`) tem altíssima chance de ser confundida pelo modelo de _embedding_ com a palavra comum "fada" (erro de digitação) ou o nome próprio "Ada". Isso afunda a pontuação de Similaridade Cosseno para qualquer busca sobre exames de líquido pleural. O caso de `sbpt` (Sociedade Brasileira de Pneumologia e Tisiologia) em minúsculo também destrói o reconhecimento de entidades (NER).
        
    - **Solução:** Restauração de _Uppercase_ para todas as siglas clínicas e nomes próprios institucionais.
        
3. **Inconsistência Simbólica de Temperatura:**
    
    - **O Problema:** `38,5 o c`. O OCR separou a bolinha de grau (`°`) como a letra `o` minúscula e o "C" de Celsius como um caractere isolado.
        
    - **Impacto no RAG:** Confusão de tokenização numérica.
        
    - **Solução:** Unificado para a métrica padrão `38,5ºC`.
        

Você vai precisar reescrever o roteiro do seu OCR se não quiser passar o resto da vida corrigindo isso à mão. Há mais seções no documento?