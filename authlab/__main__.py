"""Linha de comando.

    python -m authlab demo                 # executa os cenários incluídos
    python -m authlab demo --open          # idem e abre o índice no navegador
    python -m authlab analyze --input ARQ  # analisa um CSV no formato documentado
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from .config import ConfigError, load_config
from .events import InputError
from .pipeline import analyze, summary_dict, write_outputs
from .report import render_index

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "rules.yaml"
SCENARIOS_DIR = ROOT / "scenarios"


def _print_summary(summary: dict) -> None:
    rec = summary["records"]
    print(f"  Registros: lidos {rec['read']} | válidos {rec['valid']} | "
          f"rejeitados {rec['rejected']} | duplicados removidos {rec['duplicates_removed']} | "
          f"possíveis duplicados mantidos {rec['possible_duplicates_kept']}")
    for rid, s in summary["rules"].items():
        print(f"  {rid}: candidatos {s['candidates']} | elegíveis {s['eligible']} | "
              f"alertas {s['alerts']}")
        print(f"    {s['status']}")


def load_scenarios(directory: Path = SCENARIOS_DIR) -> list[tuple[Path, dict]]:
    items = []
    for meta_path in sorted(directory.glob("*/scenario.json")):
        items.append((meta_path.parent, json.loads(meta_path.read_text(encoding="utf-8"))))
    return items


def compare_expected(summary: dict, expected: dict) -> list[str]:
    diffs = []
    for key, value in expected.get("records", {}).items():
        got = summary["records"].get(key)
        if got != value:
            diffs.append(f"records.{key}: esperado {value}, obtido {got}")
    counts = {"AUTH-001": 0, "AUTH-003": 0}
    for alert_id in summary["alerts"]:
        counts[alert_id.rsplit("-", 1)[0]] += 1
    for rid, value in expected.get("alerts", {}).items():
        if counts.get(rid) != value:
            diffs.append(f"alertas {rid}: esperado {value}, obtido {counts.get(rid)}")
    return diffs


def cmd_demo(args) -> int:
    cfg = load_config(args.config)
    out_root = Path(args.out)
    scenarios = load_scenarios()
    if not scenarios:
        print(f"Nenhum cenário encontrado em {SCENARIOS_DIR}", file=sys.stderr)
        return 2
    index_rows, mismatches = [], 0
    print(f"Configuração: {cfg.source_path}")
    for folder, meta in scenarios:
        result = analyze(folder / meta["input"], cfg, meta["title"], meta["description"])
        out_dir = out_root / folder.name
        paths = write_outputs(result, out_dir)
        summary = summary_dict(result)
        diffs = compare_expected(summary, meta.get("expected", {}))
        check = "conforme o esperado" if not diffs else "DIFERENTE do esperado: " + "; ".join(diffs)
        mismatches += bool(diffs)
        print(f"\n[{folder.name}] {meta['title']}")
        _print_summary(summary)
        print(f"  Conferência: {check}")
        print(f"  Relatório: {paths['report']}")
        index_rows.append((meta["title"], meta["description"],
                           f"{folder.name}/{paths['report'].name}",
                           result.alerts_by_rule(), check))
    index = out_root / "index.html"
    index.write_text(render_index(index_rows), encoding="utf-8")
    print(f"\nÍndice da demonstração: {index}")
    if mismatches:
        print("Observação: diferenças são esperadas se a configuração foi alterada "
              "(exercício de calibração).")
    if args.open:
        webbrowser.open(index.resolve().as_uri())
    return 1 if (mismatches and args.strict) else 0


def cmd_analyze(args) -> int:
    cfg = load_config(args.config)
    result = analyze(args.input, cfg, args.title or "", "")
    paths = write_outputs(result, args.out)
    print(f"Configuração: {cfg.source_path}")
    _print_summary(summary_dict(result))
    print(f"Relatório: {paths['report']}")
    if args.open:
        webbrowser.open(paths["report"].resolve().as_uri())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m authlab",
        description="Laboratório de investigação de autenticação Windows (4624/4625).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="executa os cenários didáticos incluídos")
    demo.add_argument("--config", default=str(DEFAULT_CONFIG), help="arquivo de regras YAML")
    demo.add_argument("--out", default="output/demo", help="pasta de saída (padrão: output/demo)")
    demo.add_argument("--open", action="store_true", help="abre o índice no navegador")
    demo.add_argument("--strict", action="store_true",
                      help="retorna código 1 se algum cenário diferir do esperado")
    demo.set_defaults(func=cmd_demo)

    an = sub.add_parser("analyze", help="analisa um CSV no formato documentado")
    an.add_argument("--input", required=True, help="CSV de entrada (docs/formato-csv.md)")
    an.add_argument("--config", default=str(DEFAULT_CONFIG), help="arquivo de regras YAML")
    an.add_argument("--out", default="output/analysis", help="pasta de saída")
    an.add_argument("--title", help="título exibido no relatório")
    an.add_argument("--open", action="store_true", help="abre o relatório no navegador")
    an.set_defaults(func=cmd_analyze)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ConfigError, InputError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
