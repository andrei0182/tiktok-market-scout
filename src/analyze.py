"""
Calculează semnale simple, comparabile între nișe, dintr-un fișier de date
brute produs de fetch.py.

Semnale:
  - performer_density: câte reclame de top există (nișă cu multe = piață
    activă, dar și competiție mai mare)
  - format_distribution: procentul reclamelor pe durată (video scurt vs
    lung) și pe obiectiv dominant
  - saturation_signal: cât de mult domină primele 2-3 brand-uri topul —
    saturat / moderat / deschis
"""

import argparse
import json
from collections import Counter
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

DURATION_BUCKETS = [
    ("0-15s", 0, 15),
    ("15-30s", 15, 30),
    ("30-60s", 30, 60),
    ("60s+", 60, float("inf")),
]


def load_raw(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def bucket_for_duration(duration: float) -> str:
    for label, lo, hi in DURATION_BUCKETS:
        if lo <= duration < hi:
            return label
    return DURATION_BUCKETS[-1][0]


def format_distribution(ads: list) -> dict:
    total = len(ads)
    if total == 0:
        return {}
    counts = Counter()
    for ad in ads:
        duration = ad.get("video_info", {}).get("duration", 0)
        counts[bucket_for_duration(duration)] += 1
    return {label: round(100 * counts.get(label, 0) / total, 1) for label, _, _ in DURATION_BUCKETS}


def dominant_objective(ads: list) -> str:
    if not ads:
        return "n/a"
    counts = Counter(ad.get("objective_key", "unknown") for ad in ads)
    return counts.most_common(1)[0][0]


def saturation_signal(ads: list) -> dict:
    total = len(ads)
    if total == 0:
        return {"top_brands_share_pct": 0.0, "signal": "fără date"}
    brand_counts = Counter(ad.get("brand_name", "unknown") for ad in ads)
    top_brands = brand_counts.most_common(3)
    top_share = round(100 * sum(c for _, c in top_brands) / total, 1)

    if top_share >= 60:
        signal = "saturată (2-3 brand-uri domină topul)"
    elif top_share >= 35:
        signal = "moderată"
    else:
        signal = "deschisă (top variat, mai multe brand-uri)"

    return {
        "top_brands": [{"brand": b, "count": c} for b, c in top_brands],
        "top_brands_share_pct": top_share,
        "signal": signal,
    }


def dominant_format(distribution: dict) -> str:
    if not distribution:
        return "n/a"
    return max(distribution, key=distribution.get)


def analyze(raw: dict) -> dict:
    ads = raw.get("ads", [])
    config = raw.get("config", {})
    dist = format_distribution(ads)
    sat = saturation_signal(ads)

    return {
        "niche": config.get("niche"),
        "country": config.get("country"),
        "objective": config.get("objective"),
        "performer_density": len(ads),
        "format_distribution_pct": dist,
        "dominant_format": dominant_format(dist),
        "dominant_objective": dominant_objective(ads),
        "saturation": sat,
    }


def save_summary(summary: dict, raw_path: Path) -> Path:
    out_path = raw_path.with_name(raw_path.stem + "_summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return out_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Cale către fișierul JSON brut din output/")
    args = parser.parse_args()

    raw_path = Path(args.input)
    raw = load_raw(raw_path)
    summary = analyze(raw)
    out_path = save_summary(summary, raw_path)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nSalvat sumar în {out_path}")


if __name__ == "__main__":
    main()
