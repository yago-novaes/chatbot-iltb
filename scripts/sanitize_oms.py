"""
Sanitização do documento OMS Módulo 4 para RAG.
Executar: python scripts/sanitize_oms.py
"""
import re
import sys
sys.stdout.reconfigure(encoding="utf-8")

INPUT = "docs/protocolos/9789275728185_por.md"
OUTPUT = INPUT  # sobrescreve o original

with open(INPUT, encoding="utf-8") as f:
    lines = f.readlines()

# ── TASK 1: remover bloco editorial (linhas 1–125) e Referências (linha 1319+) ──
# Manter apenas linhas 126..1318 (índices 125..1317)
lines = lines[125:1318]   # 0-indexed, inclui L126 (Definições), exclui L1319 (Referências)

content = "".join(lines)

# ── TASK 3: artefatos OCR ──
# Remover <!-- image -->
content = re.sub(r"<!-- image -->\n?", "", content)
# Substituir "Î " (bullet OCR) por "- "
content = content.replace("Î ", "- ")
# Corrigir "T abela" → "Tabela"
content = content.replace("T abela", "Tabela")
# Colapsar múltiplos espaços internos (não no início de linha)
content = re.sub(r"(?m)(?<=\S)  +", " ", content)
# Remover linha de número de página isolada (apenas dígitos)
content = re.sub(r"(?m)^\d{1,3}\n", "", content)
# Remover footnotes isoladas (8 Atkins..., 9 Nishikiori..., 10 Os modelos...)
content = re.sub(r"(?m)^[89]  ?[A-Z][^\n]{5,100}\n", "", content)
content = re.sub(r"(?m)^10    Os modelos[^\n]*\n", "", content)

# ── TASK 2: corrigir hierarquia de cabeçalhos ──

# Função de substituição por mapeamento exato
heading_map = {
    # Capítulos principais (## mantidos ou normalizados)
    r"^## Definições\s*$": "## Definições",
    r"^## 1\.\s+Introdução\s*$": "## 1. Introdução",
    r"^## 2\.\s+Abordagem centrada nas pessoas\s*$": "## 2. Abordagem centrada nas pessoas",
    r"^## 3\.\s+Intervenções de atenção e suporte[^\n]*$": "## 3. Intervenções de atenção e suporte para facilitar a adesão ao tratamento da TB",
    r"^## 4\.\s+Educação em saúde[^\n]*$": "## 4. Educação em saúde e aconselhamento para pessoas afetadas pela tuberculose",
    r"^## 5\s+Modelos[^\n]*$": "## 5. Modelos de atenção",
    r"^## 6\. Cuidados paliativos\s*$": "## 6. Cuidados paliativos",

    # Seções ### (subseções numeradas)
    r"^## Recomendações:\s*$": "### Recomendações:",
    r"^## Recomendação:\s*$": "### Recomendação:",
    r"^## 3\.1\s+Apoio social[^\n]*$": "### 3.1 Apoio social no manejo da TB",
    r"^## 3\.2\s+Administração do tratamento[^\n]*$": "### 3.2 Administração do tratamento e tecnologias digitais de apoio à adesão",
    r"^## 3\.3\s+Seleção de um pacote[^\n]*$": "### 3.3 Seleção de um pacote adequado de atenção e apoio para o paciente",
    r"^## 4\.1\s+Princípios[^\n]*$": "### 4.1 Princípios orientadores para educação em saúde e aconselhamento",
    r"^## 4\.2\s+Habilidades de comunicação[^\n]*$": "### 4.2 Habilidades de comunicação efetiva para oferecer educação em saúde e aconselhamento",
    r"^## 4\.3\s+Aconselhamento para fornecer informações sobre TB[^\n]*$": "### 4.3 Aconselhamento para fornecer informações sobre TB e as responsabilidades das pessoas e comunidades afetadas",
    r"^## 4\.4\s+Aconselhamento para fornecer informações sobre o tratamento[^\n]*$": "### 4.4 Aconselhamento para fornecer informações sobre o tratamento da TB e assegurar a adesão ao tratamento",
    r"^## 4\.5\s+Aconselhamento para fornecer apoio psicológico\s*$": "### 4.5 Aconselhamento para fornecer apoio psicológico",
    r"^## 4\.6\s+Aconselhamento sobre atenção[^\n]*$": "### 4.6 Aconselhamento sobre atenção e suporte nutricional",
    r"^## 4\.7\s+Aconselhamento no final[^\n]*$": "### 4.7 Aconselhamento no final do tratamento da TB e sobre cuidados paliativos",
    r"^## 5\.1\s+Modelos de atenção para todos[^\n]*$": "### 5.1 Modelos de atenção para todos os pacientes com TB",
    r"^## 5\.2\s+Modelos de atenção descentralizada[^\n]*$": "### 5.2 Modelos de atenção descentralizada, integrada e centrada na família à TB para crianças e adolescentes",
    r"^## 5\.3\s+Modelos de prestação[^\n]*$": "### 5.3 Modelos de prestação de serviços para pessoas com TB, HIV e comorbidades",
    r"^## 5\.4\s+Envolvimento do setor privado[^\n]*$": "### 5.4 Envolvimento do setor privado no tratamento da TB",
    r"^## 5\.5\s+TB e emergências[^\n]*$": "### 5.5 TB e emergências de saúde",
    r"^## 6\.1\s+O que são cuidados paliativos[^\n]*$": "### 6.1 O que são cuidados paliativos?",
    r"^## 6\.2\s+Planejamento e implementação[^\n]*$": "### 6.2 Planejamento e implementação de cuidados paliativos para pessoas afetadas pela TB",
    r"^## 6\.3\s+Cuidados de fim de vida[^\n]*$": "### 6.3 Cuidados de fim de vida para pessoas com TB",

    # Sub-subseções #### (numeradas x.y.z)
    r"^## 3\.1\.1\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 3\.1\.2\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 3\.1\.3\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 3\.1\.4\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 3\.2\.1\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 3\.2\.2\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 4\.2\.\d+\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 4\.3\.\d+\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 4\.4\.\d+\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 4\.5\.\d+\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 4\.6\.\d+\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 4\.7\.\d+\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 5\.1\.\d+\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 6\.1\.\d+\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 6\.2\.\d+\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## 6\.3\.\d+\s+[^\n]+$": lambda m: "####" + m.group(0)[2:],

    # Quadros e Tabelas como subseções ####
    r"^## Quadro \d+\.[^\n]+$": lambda m: "####" + m.group(0)[2:],
    r"^## Tabela \d+\.[^\n]+$": lambda m: "####" + m.group(0)[2:],

    # Falsos cabeçalhos → negrito
    r"^## AVALIAR\s*$": "**AVALIAR**",
    r"^## ACONSELHAR\s*$": "**ACONSELHAR**",
    r"^## CONCORDAR\s*$": "**CONCORDAR**",
    r"^## AUXILIAR\s*$": "**AUXILIAR**",
    r"^## PROVIDENCIAR\s*$": "**PROVIDENCIAR**",
    r"^## Alguns exemplos de perguntas:\s*$": "**Alguns exemplos de perguntas:**",
    r"^## Alguns exemplos:\s*$": "**Alguns exemplos:**",
    r"^## Grupo de apoio\s*$": "**Grupo de apoio**",
    r"^## Apoio ao tratamento\s*$": "#### Apoio ao tratamento",
    r"^## Impacto socioeconômico[^\n]*$": "#### Impacto socioeconômico da TB em crianças, adolescentes e famílias",

    # Cabeçalhos numerados dentro de seções (não são seções reais)
    r"^## 1\. Informações objetivas[^\n]*$": "**1. Informações objetivas sobre a TB como doença e seu tratamento**",
    r"^## 2\. Os direitos das pessoas[^\n]*$": "**2. Os direitos das pessoas afetadas pela tuberculose**",
    r"^## 1\. Visita domiciliar[^\n]*$": "**1. Visita domiciliar para interagir com o paciente**",
    r"^## 2\. Avaliação dos motivos[^\n]*$": "**2. Avaliação dos motivos por trás da interrupção do tratamento**",
    r"^## 3\. Conversa sobre as preocupações[^\n]*$": "**3. Conversa sobre as preocupações do paciente que causaram sua não adesão**",
    r"^## 4\. Orientação do paciente[^\n]*$": "**4. Orientação do paciente sobre a necessidade de continuar o tratamento**",
    r"^## 5\. Aconselhamento e apoio[^\n]*$": "**5. Aconselhamento e apoio para que o paciente retome o tratamento rapidamente**",
    r"^## 6\.  Envolvimento  de  agentes[^\n]*$": "**6. Envolvimento de agentes comunitários de saúde, familiares e cuidadores para assegurar a adesão ao tratamento**",
    r"^## 6\. Envolvimento de agentes[^\n]*$": "**6. Envolvimento de agentes comunitários de saúde, familiares e cuidadores para assegurar a adesão ao tratamento**",
    r"^## a\. [^\n]+$": lambda m: "**" + m.group(0)[3:] + "**",
    r"^## b\. [^\n]+$": lambda m: "**" + m.group(0)[3:] + "**",
    r"^## c\. [^\n]+$": lambda m: "**" + m.group(0)[3:] + "**",
    r"^## d\. [^\n]+$": lambda m: "**" + m.group(0)[3:] + "**",
    r"^## e\. [^\n]+$": lambda m: "**" + m.group(0)[3:] + "**",
    r"^## f\. [^\n]+$": lambda m: "**" + m.group(0)[3:] + "**",
}

for pattern, replacement in heading_map.items():
    if callable(replacement):
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

# ── TASK 4: Corrigir Tabela 3 (duas partes separadas → unir) ──
# A tabela 3 foi dividida pelo Docling em dois blocos. O segundo bloco começa
# com |---|...| que faz parte da tabela anterior. Juntar removendo a linha em branco entre eles.
# Identificamos pela presença de "|---" depois de uma linha de tabela e linha em branco.
content = re.sub(r"(\|[^\n]+\n)\n(\|---)", r"\1\2", content)

# ── TASK 5: fix estruturais ──
# Remover linhas em branco duplas excessivas (máx 2 linhas em branco consecutivas)
content = re.sub(r"\n{4,}", "\n\n\n", content)

# Garantir que o arquivo começa com ## Definições (sem linha em branco antes)
content = content.lstrip()

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(content)

# ── Verificação final ──
out_lines = content.split("\n")
h2 = [l for l in out_lines if re.match(r"^## [^#]", l)]
h3 = [l for l in out_lines if re.match(r"^### [^#]", l)]
h4 = [l for l in out_lines if re.match(r"^#### [^#]", l)]
img = [l for l in out_lines if "<!-- image -->" in l]
i_art = [l for l in out_lines if "Î " in l]
tabela_err = [l for l in out_lines if "T abela" in l]

print(f"Output lines   : {len(out_lines)}")
print(f"## headings    : {len(h2)}")
print(f"### headings   : {len(h3)}")
print(f"#### headings  : {len(h4)}")
print(f"<!-- image --> : {len(img)}")
print(f"Î artifacts   : {len(i_art)}")
print(f"T abela errors : {len(tabela_err)}")
print("\n## headings:")
for h in h2:
    print(f"  {h}")
print("\n### headings (first 10):")
for h in h3[:10]:
    print(f"  {h}")
