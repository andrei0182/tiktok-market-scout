"""
Generează un raport comparativ (Excel și/sau HTML) din unul sau mai multe
fișiere de sumar produse de analyze.py (*_summary.json).

Exemplu:
    python src/report.py --input output/*_summary.json --format both
"""

import argparse
import glob
import json
from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def load_summaries(patterns: list) -> list:
    paths = []
    for pattern in patterns:
        paths.extend(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"Niciun fișier de sumar găsit pentru: {patterns}")

    summaries = []
    for path in sorted(set(paths)):
        with open(path, "r", encoding="utf-8") as f:
            summaries.append(json.load(f))
    return summaries


def to_dataframe(summaries: list) -> pd.DataFrame:
    rows = []
    for s in summaries:
        rows.append(
            {
                "Nișă": s.get("niche"),
                "Țară": s.get("country"),
                "Nr. reclame de top": s.get("performer_density"),
                "Format dominant": s.get("dominant_format"),
                "Obiectiv dominant": s.get("dominant_objective"),
                "Cotă top 3 brand-uri (%)": s.get("saturation", {}).get("top_brands_share_pct"),
                "Semnal": s.get("saturation", {}).get("signal"),
            }
        )
    return pd.DataFrame(rows)


def write_excel(df: pd.DataFrame, out_path: Path):
    df.to_excel(out_path, index=False)


def write_html(df: pd.DataFrame, out_path: Path):
    html = f"""<!doctype html>
<html lang="ro">
<head>
<meta charset="utf-8">
<title>Raport comparativ nișe TikTok</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 8px 12px; text-align: left; }}
  th {{ background: #f4f4f4; }}
  caption {{ text-align: left; font-size: 0.9rem; color: #666; margin-bottom: 0.5rem; }}
</style>
</head>
<body>
<h1>Raport comparativ nișe TikTok</h1>
<table>
<caption>Semnal orientativ, nu certitudine — decizia finală rămâne pe judecata ta.</caption>
{df.to_html(index=False, border=0)}
</table>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="Unul sau mai multe pattern-uri glob către fișiere *_summary.json",
    )
    parser.add_argument(
        "--format",
        choices=["excel", "html", "both"],
        default="both",
        help="Formatul raportului de generat (implicit: both)",
    )
    parser.add_argument(
        "--output-name",
        default="raport_comparativ",
        help="Numele de bază pentru fișierul de raport (fără extensie)",
    )
    args = parser.parse_args()

    summaries = load_summaries(args.input)
    df = to_dataframe(summaries)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.format in ("excel", "both"):
        excel_path = OUTPUT_DIR / f"{args.output_name}.xlsx"
        write_excel(df, excel_path)
        print(f"Raport Excel salvat în {excel_path}")

    if args.format in ("html", "both"):
        html_path = OUTPUT_DIR / f"{args.output_name}.html"
        write_html(df, html_path)
        print(f"Raport HTML salvat în {html_path}")

    print("\n" + df.to_string(index=False))


if __name__ == "__main__":
    main()
