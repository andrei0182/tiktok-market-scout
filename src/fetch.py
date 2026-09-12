"""
Interoghează TikTok Creative Center pentru reclamele de top ale unei nișe
și salvează rezultatul brut local, în output/.

IMPORTANT — citește înainte să rulezi în modul live:

TikTok Creative Center (ads.tiktok.com/business/creativecenter) își schimbă
periodic API-ul intern și are protecții anti-bot (cere cookie de sesiune
valid, uneori captcha). Endpoint-ul și parametrii de mai jos sunt cei mai
uzuali documentați de comunitate la momentul scrierii acestui script, dar
NU au putut fi verificați live din mediul în care a fost dezvoltat acest
tool (acces de rețea către ads.tiktok.com a fost blocat la nivel de
politică de organizație). Înainte de a folosi modul live:

  1. Intră manual pe ads.tiktok.com/business/creativecenter/inspiration/topads
     autentificat cu contul tău.
  2. Aplică filtrele dorite (industrie, țară, obiectiv, interval de date).
  3. Deschide DevTools -> Network, filtrează după "creative_radar_api" sau
     "top_ads" și copiază:
       - URL-ul exact al cererii (poate diferi de TOP_ADS_ENDPOINT de mai jos)
       - Payload-ul / query params trimise
       - Header-ele necesare (de obicei un cookie de sesiune)
  4. Actualizează TOP_ADS_ENDPOINT și build_payload() mai jos dacă diferă,
     și pune cookie-ul de sesiune în variabila de mediu TIKTOK_CC_COOKIE
     (niciodată hardcodat în cod sau commis în git).

Fără acest pas, modul live poate returna erori sau date incomplete — asta
e motivul pentru care există --mock: generează date sintetice cu aceeași
formă, ca să poți dezvolta/testa analyze.py și report.py fără să depinzi
de disponibilitatea API-ului extern.
"""

import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

TOP_ADS_ENDPOINT = "https://ads.tiktok.com/creative_radar_api/v1/top_ads/v2/list"
REQUEST_DELAY_SECONDS = 4  # cerere rară, nu extragere masivă — vezi README
PAGE_SIZE = 20
MAX_PAGES = 5  # plafon de siguranță pentru numărul de pagini interogate

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    for required in ("niche", "country", "objective", "date_range_days"):
        if required not in config:
            raise ValueError(f"Config-ul {config_path} nu are câmpul obligatoriu '{required}'")
    return config


def build_headers() -> dict:
    cookie = os.environ.get("TIKTOK_CC_COOKIE", "")
    if not cookie:
        raise RuntimeError(
            "Lipsește TIKTOK_CC_COOKIE. Fă pasul manual de explorare din docstring-ul "
            "acestui fișier și setează cookie-ul de sesiune ca variabilă de mediu, "
            "sau rulează cu --mock pentru date sintetice de test."
        )
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Cookie": cookie,
        "Content-Type": "application/json",
    }


def build_payload(config: dict, page: int) -> dict:
    return {
        "country_code": config["country"],
        "objective": config["objective"],
        "period": config["date_range_days"],
        "page": page,
        "limit": PAGE_SIZE,
        "keyword": config.get("niche"),
        "industry_id": config.get("industry_id"),
    }


def fetch_page(session: requests.Session, headers: dict, config: dict, page: int) -> dict:
    response = session.post(
        TOP_ADS_ENDPOINT,
        headers=headers,
        json=build_payload(config, page),
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def fetch_live(config: dict) -> list:
    headers = build_headers()
    session = requests.Session()
    ads = []
    for page in range(1, MAX_PAGES + 1):
        data = fetch_page(session, headers, config, page)
        items = data.get("data", {}).get("materials", []) or data.get("materials", [])
        if not items:
            break
        ads.extend(items)
        if len(items) < PAGE_SIZE:
            break
        time.sleep(REQUEST_DELAY_SECONDS)
    return ads


def generate_mock_ads(config: dict, count: int) -> list:
    """Date sintetice cu aceeași formă ca răspunsul real, pentru test end-to-end."""
    brand_pool = [f"Brand {letter}" for letter in "ABCDEFGH"]
    objectives = [config["objective"], "Traffic", "Conversions"]
    ads = []
    for i in range(count):
        duration = random.choice([8, 15, 22, 30, 45, 60])
        ads.append(
            {
                "id": f"mock-{config['niche']}-{i}",
                "ad_title": f"{config['niche']} ad #{i}",
                "brand_name": random.choice(brand_pool),
                "industry_key": config["niche"],
                "objective_key": random.choice(objectives),
                "like": random.randint(500, 50000),
                "video_info": {"duration": duration},
            }
        )
    return ads


def save_raw(ads: list, config: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_niche = config["niche"].lower().replace(" ", "_")
    out_path = OUTPUT_DIR / f"{safe_niche}_{config['country']}_{timestamp}.json"
    payload = {
        "fetched_at": timestamp,
        "config": config,
        "ads": ads,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Cale către fișierul JSON de config al nișei")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Generează date sintetice locale în loc să interogheze TikTok (pentru testare)",
    )
    parser.add_argument(
        "--mock-count",
        type=int,
        default=30,
        help="Câte reclame sintetice să genereze în modul --mock (implicit 30)",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.mock:
        ads = generate_mock_ads(config, args.mock_count)
    else:
        ads = fetch_live(config)

    out_path = save_raw(ads, config)
    print(f"Salvat {len(ads)} reclame în {out_path}")


if __name__ == "__main__":
    main()
