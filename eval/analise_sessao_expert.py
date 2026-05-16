"""
Análise da sessão de avaliação humana com especialista — Chatbot ILTB.

Lê as planilhas preenchidas durante e após a sessão e gera os artefatos
para o capítulo de Avaliação da monografia: gráficos em PNG, tabelas em
LaTeX e CSV, e um sumário executivo em Markdown pronto para colar nos
campos \\aluno{...} da seção sec:sessao-expert do main.tex.

Uso:

    # Antes da sessão (modo dry-run com dados sintéticos):
    python -m eval.analise_sessao_expert --dry-run

    # Depois da sessão, com planilhas preenchidas:
    python -m eval.analise_sessao_expert

Inputs (após a sessão):
    docs/sessao_expert/planilha_coleta_deep_dive.csv    (10 questões × I1+I2+I3)
    docs/sessao_expert/planilha_coleta_async.csv        (29 questões × I1+I2)
    docs/sessao_expert/tam_ain_respostas.csv            (28 itens Likert)

Outputs:
    eval/results/expert_session/
      ├── 01_acuracia_por_categoria.png
      ├── 02_severidade_histograma.png
      ├── 03_triade_rag_vs_ragas.png
      ├── 04_tam_ain_dimensoes.png
      ├── tabela_resultados.tex
      ├── tabela_resultados.csv
      └── sumario_executivo.md

Compatível com a estrutura definida em docs/sessao_expert/questionario_tam_ain.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ─── Configuração ─────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SESSAO_DIR = PROJECT_ROOT / "docs" / "sessao_expert"
OUTPUT_DIR = PROJECT_ROOT / "eval" / "results" / "expert_session"
RAGAS_SCORES = PROJECT_ROOT / "eval" / "results" / "ragas_scores.json"

CATEGORIAS_PT = {
    "esquemas_terapeuticos": "Esquemas terapêuticos",
    "indicacoes_tratamento": "Indicações",
    "populacoes_especiais": "Populações especiais",
    "diagnostico": "Diagnóstico",
    "monitoramento": "Monitoramento",
    "interacoes_medicamentosas": "Interações medicamentosas",
    "efeitos_adversos": "Efeitos adversos",
    "fora_do_escopo": "Fora do escopo",
}

# Itens TAM-AIN por dimensão (alinhado a questionario_tam_ain.md)
TAM_AIN_ITENS = {
    "Utilidade Percebida": ["UP1", "UP2", "UP3", "UP4"],
    "Facilidade de Uso": ["FU1", "FU2", "FU3", "FU4"],
    "Alinhamento Ético": ["AE1", "AE2", "AE3", "AE4"],
    "Prontidão Organizacional": ["PO1", "PO2", "PO3", "PO4"],
    "Identidade Profissional": ["IP1", "IP2", "IP3", "IP4"],
    "Infraestrutura Técnica": ["IT1", "IT2", "IT3", "IT4"],
    "Atitude e Intenção": ["AT1", "AT2", "AT3", "AT4"],
}
ITENS_INVERTIDOS = {"IP1", "IP3"}
DIMENSOES_TAM_AIN_ESTENDIDAS = [
    "Alinhamento Ético",
    "Prontidão Organizacional",
    "Identidade Profissional",
    "Infraestrutura Técnica",
]


# ─── Schemas ─────────────────────────────────────────────────────────────────


@dataclass
class ResultadoSessao:
    """Resultado agregado de uma sessão expert."""

    n_avaliadas: int
    n_corretas: int
    n_parciais: int
    n_incorretas: int
    severidade_media: float | None
    triade_fidelidade_media: float | None
    triade_relevancia_resposta_media: float | None
    triade_relevancia_contexto_media: float | None
    tam_ain_por_dimensao: dict[str, float]
    tam_ain_composto: float | None


# ─── Carga das planilhas ──────────────────────────────────────────────────────


def carregar_planilha(path: Path) -> pd.DataFrame:
    """Lê CSV com `;`, UTF-8 BOM."""
    if not path.exists():
        raise FileNotFoundError(f"Planilha não encontrada: {path}")
    return pd.read_csv(path, sep=";", encoding="utf-8-sig")


def carregar_tam_ain(path: Path) -> dict[str, int]:
    """
    Lê respostas TAM-AIN do CSV com colunas: item_id, valor.
    Aceita formato {item_id: valor} ou {ID: valor}.
    Retorna dicionário {item_id: valor_inteiro}.
    """
    if not path.exists():
        raise FileNotFoundError(f"Respostas TAM-AIN não encontradas: {path}")
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    cols = {c.strip().lower(): c for c in df.columns}
    id_col = cols.get("item_id") or cols.get("id") or df.columns[0]
    val_col = cols.get("valor") or cols.get("resposta") or df.columns[1]
    out: dict[str, int] = {}
    for _, row in df.iterrows():
        key = str(row[id_col]).strip().upper()
        try:
            out[key] = int(row[val_col])
        except (ValueError, TypeError):
            continue
    return out


# ─── Análises ─────────────────────────────────────────────────────────────────


def _normalizar_acuracia(valor: str | float) -> str | None:
    """Mapeia variações de texto para {correta, parcial, incorreta}."""
    if pd.isna(valor):
        return None
    v = str(valor).strip().lower()
    if "correta" == v or "ok" == v or v.startswith("correta"):
        return "correta"
    if "parc" in v:
        return "parcial"
    if "incorret" in v or "erro" in v:
        return "incorreta"
    return None


def acuracia_por_categoria(deep_dive: pd.DataFrame, async_df: pd.DataFrame) -> pd.DataFrame:
    """
    Conta acurácia (correta/parcial/incorreta) por categoria,
    somando deep-dive + async. Devolve DataFrame em formato longo.
    """
    full = pd.concat([deep_dive, async_df], ignore_index=True, sort=False)
    col_i1 = next(c for c in full.columns if c.lower().startswith("i1_acuracia"))
    full["_acur"] = full[col_i1].apply(_normalizar_acuracia)
    full = full.dropna(subset=["_acur"])

    grouped = (
        full.groupby(["categoria", "_acur"]).size().unstack(fill_value=0)
    )
    for col in ["correta", "parcial", "incorreta"]:
        if col not in grouped.columns:
            grouped[col] = 0
    grouped["total"] = grouped[["correta", "parcial", "incorreta"]].sum(axis=1)
    grouped["pct_correta"] = (grouped["correta"] / grouped["total"] * 100).round(1)
    return grouped[["correta", "parcial", "incorreta", "total", "pct_correta"]]


def histograma_severidade(deep_dive: pd.DataFrame, async_df: pd.DataFrame) -> pd.Series:
    """Distribuição de severidade 1-5 dos erros."""
    full = pd.concat([deep_dive, async_df], ignore_index=True, sort=False)
    col_i2 = next(c for c in full.columns if c.lower().startswith("i2_severidade"))
    nums = pd.to_numeric(full[col_i2], errors="coerce").dropna()
    return nums.value_counts().sort_index()


def triade_rag(deep_dive: pd.DataFrame) -> dict[str, float]:
    """Médias das 3 sub-notas do I3 (Tríade RAG)."""
    cols = {
        "fidelidade": next(c for c in deep_dive.columns if "i3a" in c.lower()),
        "relevancia_resposta": next(c for c in deep_dive.columns if "i3b" in c.lower()),
        "relevancia_contexto": next(c for c in deep_dive.columns if "i3c" in c.lower()),
    }
    return {
        nome: pd.to_numeric(deep_dive[col], errors="coerce").mean()
        for nome, col in cols.items()
    }


def tam_ain_scores(respostas: dict[str, int]) -> dict[str, float]:
    """Calcula média por dimensão TAM-AIN; inverte IP1 e IP3 (6 - valor)."""
    out: dict[str, float] = {}
    for dimensao, itens in TAM_AIN_ITENS.items():
        valores = []
        for item in itens:
            if item not in respostas:
                continue
            v = respostas[item]
            if item in ITENS_INVERTIDOS:
                v = 6 - v
            valores.append(v)
        if valores:
            out[dimensao] = round(sum(valores) / len(valores), 3)
    return out


def tam_ain_composto(scores_por_dim: dict[str, float]) -> float | None:
    """Composto = média das 4 dimensões estendidas TAM-AIN."""
    vals = [scores_por_dim[d] for d in DIMENSOES_TAM_AIN_ESTENDIDAS if d in scores_por_dim]
    return round(sum(vals) / len(vals), 3) if vals else None


def carregar_ragas_atual() -> dict[str, float] | None:
    """Carrega o último entry do ragas_scores.json (gate final)."""
    if not RAGAS_SCORES.exists():
        return None
    history = json.loads(RAGAS_SCORES.read_text(encoding="utf-8"))
    if not history:
        return None
    return {
        k: v
        for k, v in history[-1].items()
        if k in ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    }


# ─── Gráficos ─────────────────────────────────────────────────────────────────


def grafico_acuracia(grouped: pd.DataFrame, output: Path) -> None:
    """Stacked bar — acurácia por categoria."""
    cats_pt = [CATEGORIAS_PT.get(c, c) for c in grouped.index]
    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = np.zeros(len(grouped))
    cores = {"correta": "#2ca02c", "parcial": "#ff7f0e", "incorreta": "#d62728"}
    for col in ["correta", "parcial", "incorreta"]:
        ax.barh(cats_pt, grouped[col].values, left=bottom, label=col.capitalize(), color=cores[col])
        bottom += grouped[col].values
    ax.set_xlabel("Número de questões")
    ax.set_title("Avaliação humana — acurácia das respostas por categoria")
    ax.legend(loc="lower right")
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    fig.tight_layout()
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)


def grafico_severidade(serie: pd.Series, output: Path) -> None:
    """Histograma de severidade."""
    labels_full = {
        1: "1 — sem risco",
        2: "2 — risco baixo",
        3: "3 — risco moderado",
        4: "4 — risco alto",
        5: "5 — conduta perigosa",
    }
    xs = list(range(1, 6))
    ys = [int(serie.get(i, 0)) for i in xs]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar([labels_full[x] for x in xs], ys, color="#a83232")
    ax.set_ylabel("Número de respostas")
    ax.set_title("Avaliação humana — severidade dos erros (apenas respostas incorretas/parciais)")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)


def grafico_triade_vs_ragas(
    triade_humana: dict[str, float],
    ragas_atual: dict[str, float] | None,
    output: Path,
) -> None:
    """Bar grouped — Tríade humana vs métricas RAGAS automáticas."""
    pares = [
        ("Fidelidade\n(I3a vs faithfulness)", triade_humana.get("fidelidade"), (ragas_atual or {}).get("faithfulness")),
        ("Relevância da resposta\n(I3b vs answer_relevancy)", triade_humana.get("relevancia_resposta"), (ragas_atual or {}).get("answer_relevancy")),
        ("Relevância do contexto\n(I3c vs context_precision)", triade_humana.get("relevancia_contexto"), (ragas_atual or {}).get("context_precision")),
    ]
    labels = [p[0] for p in pares]
    humanos = [p[1] if p[1] is not None else 0 for p in pares]
    # Escala humana é 1-5; RAGAS é 0-1. Normalizar humana para 0-1 (dividir por 5) para comparação visual.
    humanos_norm = [v / 5 for v in humanos]
    ragas = [p[2] if p[2] is not None else 0 for p in pares]

    x = np.arange(len(labels))
    w = 0.35
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x - w / 2, humanos_norm, w, label="Avaliação humana (0–1, normalizado de 1–5)", color="#1f77b4")
    ax.bar(x + w / 2, ragas, w, label="RAGAS automático", color="#9467bd")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score (0–1)")
    ax.set_title("Tríade de qualidade RAG — comparação humano × automático")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    fig.tight_layout()
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)


def grafico_tam_ain(scores: dict[str, float], composto: float | None, output: Path) -> None:
    """Bar — scores TAM-AIN por dimensão + linha do composto."""
    ordem = list(TAM_AIN_ITENS.keys())
    vals = [scores.get(d, np.nan) for d in ordem]
    fig, ax = plt.subplots(figsize=(11, 5))
    cores = ["#1f77b4"] * 2 + ["#ff7f0e"] * 4 + ["#2ca02c"]
    ax.bar(ordem, vals, color=cores)
    ax.set_ylim(0, 5.5)
    ax.set_ylabel("Score médio (escala 1–5)")
    ax.set_title("TAM-AIN — scores por dimensão (avaliação do expert)")
    ax.axhline(y=4, color="gray", linestyle=":", alpha=0.5, label="Limiar de aceitação positiva (≥4)")
    if composto is not None:
        ax.axhline(y=composto, color="red", linestyle="--", alpha=0.7, label=f"Composto TAM-AIN = {composto:.2f}")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    fig.tight_layout()
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ─── Tabelas e sumário ────────────────────────────────────────────────────────


def tabela_resultados(
    resultado: ResultadoSessao,
    ragas_atual: dict[str, float] | None,
    output_tex: Path,
    output_csv: Path,
) -> None:
    """Tabela mestre de comparação humano × RAGAS."""
    rows = [
        ("Questões avaliadas (total)", f"{resultado.n_avaliadas}", "38 (RAGAS, gate final)"),
        ("Corretas (I1)", f"{resultado.n_corretas}", "—"),
        ("Parcialmente corretas (I1)", f"{resultado.n_parciais}", "—"),
        ("Incorretas (I1)", f"{resultado.n_incorretas}", "—"),
        ("Severidade média dos erros (I2)", f"{resultado.severidade_media:.2f}" if resultado.severidade_media is not None else "—", "—"),
        ("Tríade — fidelidade média", f"{resultado.triade_fidelidade_media:.2f}/5" if resultado.triade_fidelidade_media else "—", f"{(ragas_atual or {}).get('faithfulness', '—')} (faithfulness)"),
        ("Tríade — relevância resposta", f"{resultado.triade_relevancia_resposta_media:.2f}/5" if resultado.triade_relevancia_resposta_media else "—", f"{(ragas_atual or {}).get('answer_relevancy', '—')}"),
        ("Tríade — relevância contexto", f"{resultado.triade_relevancia_contexto_media:.2f}/5" if resultado.triade_relevancia_contexto_media else "—", f"{(ragas_atual or {}).get('context_precision', '—')}"),
    ]
    df = pd.DataFrame(rows, columns=["Métrica", "Avaliação humana", "RAGAS automático"])
    df.to_csv(output_csv, sep=";", index=False, encoding="utf-8-sig")

    # LaTeX (formato simples, manual para evitar dependência de tabulate)
    lines = [
        "\\begin{table}[ht]",
        "  \\caption{Comparação entre avaliação automatizada (RAGAS) e avaliação humana (especialista)}",
        "  \\label{tab:sessao-expert-comparacao}",
        "  \\begin{tabularx}{\\textwidth}{@{}Xll@{}}",
        "  \\toprule",
        "  \\textbf{Métrica} & \\textbf{Avaliação humana} & \\textbf{RAGAS automático} \\\\",
        "  \\midrule",
    ]
    for met, hum, rag in rows:
        lines.append(f"  {met} & {hum} & {rag} \\\\")
    lines += [
        "  \\bottomrule",
        "  \\end{tabularx}",
        "  \\caption*{Fonte: Produção do próprio autor.}",
        "\\end{table}",
    ]
    output_tex.write_text("\n".join(lines), encoding="utf-8")


def gerar_sumario(
    resultado: ResultadoSessao,
    grouped: pd.DataFrame,
    severidade: pd.Series,
    ragas_atual: dict[str, float] | None,
    output: Path,
) -> None:
    """Sumário executivo em Markdown — pronto para colar no \\aluno{...} da monografia."""
    pct = resultado.n_corretas / resultado.n_avaliadas * 100 if resultado.n_avaliadas else 0
    sev_max = int(severidade.idxmax()) if not severidade.empty else 0
    sev_max_n = int(severidade.max()) if not severidade.empty else 0

    pior_cat = grouped["pct_correta"].idxmin() if not grouped.empty else "—"
    melhor_cat = grouped["pct_correta"].idxmax() if not grouped.empty else "—"

    composto = resultado.tam_ain_composto

    def _fmt(v: float | None) -> str:
        return f"{v:.2f}" if v is not None else "—"

    ragas_d = ragas_atual or {}
    fid_hum = _fmt(resultado.triade_fidelidade_media)
    rel_resp_hum = _fmt(resultado.triade_relevancia_resposta_media)
    rel_ctx_hum = _fmt(resultado.triade_relevancia_contexto_media)
    fid_auto = ragas_d.get("faithfulness", "—")
    rel_resp_auto = ragas_d.get("answer_relevancy", "—")
    rel_ctx_auto = ragas_d.get("context_precision", "—")

    md = f"""# Sumário executivo — Sessão de avaliação com especialista

> _Texto editorável para colar nos campos `\\aluno{{...}}` das seções
> `Perfil do Especialista` e `Resultados e Análise da Sessão` do capítulo
> de Avaliação da monografia._

## Cobertura

- **Total de questões avaliadas:** {resultado.n_avaliadas} (38 \\textit{{in-scope}} do gate RAGAS + 1 \\textit{{out-of-scope}} adversarial, conforme [`selecao_deep_dive.md`](../../docs/sessao_expert/selecao_deep_dive.md)).
- **Acurácia geral:** {resultado.n_corretas} corretas ({pct:.1f}%),
  {resultado.n_parciais} parcialmente corretas, {resultado.n_incorretas} incorretas.

## Padrão de erros

- **Categoria com maior taxa de acerto:** {CATEGORIAS_PT.get(melhor_cat, melhor_cat)} ({grouped.loc[melhor_cat, 'pct_correta']:.1f}% corretas).
- **Categoria com menor taxa de acerto:** {CATEGORIAS_PT.get(pior_cat, pior_cat)} ({grouped.loc[pior_cat, 'pct_correta']:.1f}% corretas).
- **Severidade modal dos erros:** {sev_max} ({sev_max_n} ocorrências) — escala 1 (sem risco) a 5 (conduta perigosa).

## Tríade RAG — humano × automático

| Dimensão | Avaliação humana (1–5) | RAGAS automático (0–1) |
|---|---|---|
| Fidelidade | {fid_hum} | {fid_auto} |
| Relevância da resposta | {rel_resp_hum} | {rel_resp_auto} |
| Relevância do contexto | {rel_ctx_hum} | {rel_ctx_auto} |

## TAM-AIN

| Dimensão | Score (1–5) |
|---|---|
"""
    for dim, val in resultado.tam_ain_por_dimensao.items():
        md += f"| {dim} | {val:.2f} |\n"
    md += f"\n**Score composto TAM-AIN (média das 4 dimensões estendidas):** "
    md += f"{composto:.2f}/5\n" if composto is not None else "—\n"

    if composto is not None:
        if composto < 2.5:
            interp = "Aceitação baixa --- barreiras significativas identificadas."
        elif composto < 3.5:
            interp = "Aceitação ambivalente --- pontos críticos a endereçar antes de implantação."
        elif composto < 4.5:
            interp = "Aceitação positiva --- pequenos ajustes recomendados."
        else:
            interp = "Aceitação alta --- ferramenta vista como pronta no domínio da respondente."
        md += f"\n**Interpretação:** {interp}\n"

    md += """

## Anotações qualitativas relevantes

> _Preencher com 3–5 citações representativas extraídas da coluna
> `comentarios_qualitativos` das planilhas (deep-dive + async) e das
> respostas abertas da Seção 8 do questionário._

- ...
- ...
- ...

## Material gerado para o capítulo

- `01_acuracia_por_categoria.png`
- `02_severidade_histograma.png`
- `03_triade_rag_vs_ragas.png`
- `04_tam_ain_dimensoes.png`
- `tabela_resultados.tex` (incluir via `\\input{...}`)
"""
    output.write_text(md, encoding="utf-8")


# ─── Dry-run com dados sintéticos ─────────────────────────────────────────────


def gerar_dados_sinteticos(tmpdir: Path) -> tuple[Path, Path, Path]:
    """Cria CSVs sintéticos para testar o pipeline antes da sessão real."""
    rng = np.random.default_rng(42)

    # Deep dive: 10 questões (categorias variadas)
    cats = ["esquemas_terapeuticos", "esquemas_terapeuticos", "populacoes_especiais",
            "populacoes_especiais", "diagnostico", "indicacoes_tratamento",
            "interacoes_medicamentosas", "efeitos_adversos", "monitoramento",
            "fora_do_escopo"]
    qids = ["ET-04", "ET-05", "PE-02", "PE-07", "DI-05", "IT-01", "IM-04", "EA-04", "MO-02", "FE-01"]
    acur = rng.choice(["correta", "correta", "parcial", "incorreta"], size=10)
    sev = [rng.integers(1, 6) if a != "correta" else "" for a in acur]
    dd = pd.DataFrame({
        "ordem": range(1, 11),
        "qid": qids,
        "categoria": cats,
        "pergunta": ["..."] * 10,
        "ground_truth_MS": ["..."] * 10,
        "resposta_chatbot": ["..."] * 10,
        "I1_acuracia (correta/parcial/incorreta)": acur,
        "I1_trecho_conflitante": ["" if a == "correta" else "trecho exemplo" for a in acur],
        "I2_severidade (1-5; NA se correta)": sev,
        "I3a_fidelidade (1-5)": rng.integers(3, 6, size=10),
        "I3b_relevancia_resposta (1-5)": rng.integers(3, 6, size=10),
        "I3c_relevancia_contexto (1-5)": rng.integers(4, 6, size=10),
        "comentarios_qualitativos": ["..."] * 10,
    })

    # Async: 29 questões
    n = 29
    async_acur = rng.choice(["correta", "correta", "correta", "parcial", "incorreta"], size=n)
    async_sev = [rng.integers(1, 6) if a != "correta" else "" for a in async_acur]
    async_cats = rng.choice(
        ["esquemas_terapeuticos", "populacoes_especiais", "diagnostico",
         "indicacoes_tratamento", "interacoes_medicamentosas",
         "efeitos_adversos", "monitoramento"],
        size=n,
    )
    asy = pd.DataFrame({
        "qid": [f"Q{i:02d}" for i in range(n)],
        "categoria": async_cats,
        "pergunta": ["..."] * n,
        "ground_truth_MS": ["..."] * n,
        "resposta_chatbot": ["..."] * n,
        "I1_acuracia (correta/parcial/incorreta)": async_acur,
        "I2_severidade (1-5; NA se correta)": async_sev,
        "comentarios_qualitativos": ["..."] * n,
    })

    # TAM-AIN: 28 itens
    itens = [item for itens_dim in TAM_AIN_ITENS.values() for item in itens_dim]
    valores = rng.integers(3, 6, size=len(itens))
    tam = pd.DataFrame({"item_id": itens, "valor": valores})

    p_dd = tmpdir / "planilha_coleta_deep_dive.csv"
    p_asy = tmpdir / "planilha_coleta_async.csv"
    p_tam = tmpdir / "tam_ain_respostas.csv"
    dd.to_csv(p_dd, sep=";", index=False, encoding="utf-8-sig")
    asy.to_csv(p_asy, sep=";", index=False, encoding="utf-8-sig")
    tam.to_csv(p_tam, sep=";", index=False, encoding="utf-8-sig")
    return p_dd, p_asy, p_tam


# ─── Pipeline principal ───────────────────────────────────────────────────────


def main(dry_run: bool = False) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if dry_run:
        import tempfile

        tmp = Path(tempfile.mkdtemp(prefix="sessao_mock_"))
        print(f"[dry-run] dados sintéticos em {tmp}")
        p_dd, p_asy, p_tam = gerar_dados_sinteticos(tmp)
    else:
        p_dd = SESSAO_DIR / "planilha_coleta_deep_dive.csv"
        p_asy = SESSAO_DIR / "planilha_coleta_async.csv"
        p_tam = SESSAO_DIR / "tam_ain_respostas.csv"
        for p in (p_dd, p_asy, p_tam):
            if not p.exists():
                print(f"ERRO: arquivo esperado não encontrado: {p}")
                print("Use --dry-run para testar o pipeline com dados sintéticos.")
                sys.exit(1)

    dd = carregar_planilha(p_dd)
    asy = carregar_planilha(p_asy)
    tam_respostas = carregar_tam_ain(p_tam)

    # Análises
    grouped = acuracia_por_categoria(dd, asy)
    sev = histograma_severidade(dd, asy)
    triade = triade_rag(dd)
    tam_scores = tam_ain_scores(tam_respostas)
    composto = tam_ain_composto(tam_scores)
    ragas_atual = carregar_ragas_atual()

    n_total = grouped["total"].sum()
    resultado = ResultadoSessao(
        n_avaliadas=int(n_total),
        n_corretas=int(grouped["correta"].sum()),
        n_parciais=int(grouped["parcial"].sum()),
        n_incorretas=int(grouped["incorreta"].sum()),
        severidade_media=(
            float(np.average(np.array(sev.index, dtype=float), weights=np.array(sev.values, dtype=float)))
            if not sev.empty and sev.values.sum() > 0
            else None
        ),
        triade_fidelidade_media=triade.get("fidelidade"),
        triade_relevancia_resposta_media=triade.get("relevancia_resposta"),
        triade_relevancia_contexto_media=triade.get("relevancia_contexto"),
        tam_ain_por_dimensao=tam_scores,
        tam_ain_composto=composto,
    )

    # Gráficos
    grafico_acuracia(grouped, OUTPUT_DIR / "01_acuracia_por_categoria.png")
    grafico_severidade(sev, OUTPUT_DIR / "02_severidade_histograma.png")
    grafico_triade_vs_ragas(triade, ragas_atual, OUTPUT_DIR / "03_triade_rag_vs_ragas.png")
    grafico_tam_ain(tam_scores, composto, OUTPUT_DIR / "04_tam_ain_dimensoes.png")

    # Tabelas
    tabela_resultados(
        resultado,
        ragas_atual,
        OUTPUT_DIR / "tabela_resultados.tex",
        OUTPUT_DIR / "tabela_resultados.csv",
    )

    # Sumário executivo
    gerar_sumario(resultado, grouped, sev, ragas_atual, OUTPUT_DIR / "sumario_executivo.md")

    # Console
    print("\n=== Análise da sessão expert ===")
    print(f"Questões avaliadas: {resultado.n_avaliadas}")
    print(f"  Corretas: {resultado.n_corretas} ({resultado.n_corretas / resultado.n_avaliadas * 100:.1f}%)")
    print(f"  Parciais: {resultado.n_parciais}")
    print(f"  Incorretas: {resultado.n_incorretas}")
    if resultado.severidade_media is not None:
        print(f"Severidade média dos erros: {resultado.severidade_media:.2f}/5")
    print()
    print("Tríade RAG (humano):")
    for k, v in triade.items():
        print(f"  {k}: {v:.2f}/5")
    print()
    print("TAM-AIN por dimensão:")
    for dim, val in tam_scores.items():
        print(f"  {dim}: {val:.2f}/5")
    if composto is not None:
        print(f"  -> Composto (4 dimensoes estendidas): {composto:.2f}/5")
    print()
    print(f"Artefatos salvos em {OUTPUT_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Análise da sessão expert do chatbot ILTB")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Gera dados sintéticos e roda o pipeline para validar (antes da sessão real).",
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)
