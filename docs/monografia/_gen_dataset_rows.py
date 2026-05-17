"""Gera linhas LaTeX do dataset RAGAS para o Apêndice B da monografia."""
import json
from pathlib import Path

CAT_MAP = {
    "esquemas_terapeuticos": "ET",
    "monitoramento": "MO",
    "populacoes_especiais": "PE",
    "diagnostico": "DI",
    "indicacoes_tratamento": "IND",
    "interacoes_medicamentosas": "IT",
    "efeitos_adversos": "EA",
    "fora_do_escopo": "FE",
}


def esc(s) -> str:
    """Escape LaTeX special chars; None/empty → em dash."""
    if s is None or s == "":
        return "---"
    repls = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("^", r"\textasciicircum{}"),
        ("~", r"\textasciitilde{}"),
    ]
    for old, new in repls:
        s = s.replace(old, new)
    return s


def main():
    here = Path(__file__).parent
    with (here.parent.parent / "eval" / "test_set.json").open(encoding="utf-8") as f:
        ds = json.load(f)
    order = ["ET", "IND", "PE", "DI", "MO", "IT", "EA", "FE"]
    ds.sort(key=lambda q: (order.index(CAT_MAP.get(q["category"], "FE")), q["id"]))
    lines = []
    last_idx = len(ds) - 1
    for i, q in enumerate(ds):
        sig = CAT_MAP.get(q["category"], "??")
        qid = q["id"]
        text = esc(q["question"])
        gt = esc(q["ground_truth"])
        # Última linha não inclui \hline: o \bottomrule do \endlastfoot
        # da longtable já fecha a tabela visualmente. Inserir \hline
        # antes do \bottomrule produz linha dupla e pode forçar overflow.
        line_end = "\\\\ \\hline" if i < last_idx else "\\\\"
        lines.append(
            f"\\texttt{{{qid}}} & {sig} & {text} & {gt} {line_end}"
        )
    output = "\n".join(lines)
    (here / "_dataset_rows.tex").write_text(output, encoding="utf-8")
    print(f"Wrote {len(lines)} rows to _dataset_rows.tex")


if __name__ == "__main__":
    main()
