# TikTok Market Scout

Tool personal de cercetare de piață **pre-campanie** pentru TikTok Ads.
Înainte de a cheltui buget pe o campanie, îți arată cât de "activă" și
competitivă e o nișă, pe baza reclamelor publice de top afișate de
[TikTok Creative Center](https://ads.tiktok.com/business/creativecenter) —
ca să alegi nișa/unghiul potrivit fără trial-and-error cu bani reali.

**Ce NU face**: nu lansează, nu automatizează și nu gestionează campanii.
Este strict un tool de cercetare/semnal orientativ.

## Ce date folosește

Date publice afișate în secțiunea "Top Ads" din TikTok Creative Center:
titlu reclamă, brand, industrie, obiectiv, durată video, aprecieri —
așa cum sunt vizibile oricui accesează pagina, filtrate pe nișă/țară/obiectiv.

## ⚠️ Notă importantă despre acest build

Acest tool a fost dezvoltat într-un mediu sandbox în care accesul de rețea
către `ads.tiktok.com` era blocat la nivel de politică (organizație/proxy),
deci **pasul 3 din instrucțiuni (explorarea manuală + Network tab) nu a
putut fi executat live** din acest mediu. Structura de request/response din
`src/fetch.py` e bazată pe informații documentate public de comunitate
despre API-ul intern al Creative Center, nu pe verificare directă.

**Înainte să te bazezi pe modul live, tu trebuie să faci pasul manual**:

1. Intră autentificat pe `ads.tiktok.com/business/creativecenter/inspiration/topads`.
2. Aplică filtrele dorite (industrie, țară, obiectiv, interval de date).
3. Deschide DevTools → Network, filtrează după `creative_radar_api` sau
   `top_ads`, și confirmă/actualizează în `src/fetch.py`:
   - URL-ul exact al endpoint-ului
   - Parametrii/payload-ul trimis
   - Header-ele necesare (de regulă un cookie de sesiune)
4. Pune cookie-ul de sesiune în variabila de mediu `TIKTOK_CC_COOKIE`
   (niciodată în cod sau în git).

Detalii complete sunt în docstring-ul de la începutul `src/fetch.py`.

Până faci pasul de mai sus, poți dezvolta și testa tot pipeline-ul
(`analyze.py`, `report.py`) cu date sintetice, folosind `--mock` la `fetch.py`
— vezi secțiunea de testare mai jos.

## Prudență privind ToS

- Ratele de cerere sunt intenționat mici (o cerere la câteva secunde,
  `REQUEST_DELAY_SECONDS` în `fetch.py`), nu extragere masivă.
- Acest tool e pentru **cercetare personală**, nu pentru redistribuire de
  date sau construirea unui produs pe baza lor.
- Respectă termenii de utilizare ai TikTok Creative Center. Dacă API-ul
  cere captcha sau blochează cererile scriptate, nu încerca să ocolești
  protecția — asta e un semnal că trebuie folosită interfața web direct.

## Structură

```
tiktok-market-scout/
├── src/
│   ├── fetch.py          # interoghează Creative Center (sau --mock pentru test)
│   ├── analyze.py        # calculează semnale/scoruri dintr-un fișier brut
│   └── report.py         # generează raport Excel/HTML din unul sau mai multe sumare
├── config/
│   └── niches.example.json
├── samples/               # 2 config-uri gata de test (una activă, una de nișă)
├── output/                # rapoarte generate (ignorat de git)
├── requirements.txt
└── .gitignore
```

## Instalare

```bash
cd tiktok-market-scout
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Cum se rulează

1. Copiază și editează configul pentru nișa ta:

```bash
cp config/niches.example.json config/my_niche.json
# editează niche / country / objective / date_range_days
```

2. Extrage datele:

```bash
# mod live (necesită TIKTOK_CC_COOKIE setat, vezi nota de mai sus)
export TIKTOK_CC_COOKIE="..."
python src/fetch.py --config config/my_niche.json

# sau, pentru testare fără acces live:
python src/fetch.py --config config/my_niche.json --mock
```

3. Analizează rezultatul brut (fișierul afișat de fetch.py):

```bash
python src/analyze.py --input output/home_services_US_20260101T000000Z.json
```

4. Generează raportul comparativ din toate sumarele dorite:

```bash
python src/report.py --input "output/*_summary.json" --format both
```

Rezultatul: `output/raport_comparativ.xlsx` și `output/raport_comparativ.html`,
cu un tabel de forma:

| Nișă | Țară | Nr. reclame de top | Format dominant | Semnal |
|------|------|---------------------|------------------|--------|
| Home Services | US | 45 | 15-30s | Activă, competitivă |
| Insurance | US | 8 | 30-60s | Piață mică, risc mai mare |

## Testare end-to-end (2 nișe, fără acces live)

```bash
python src/fetch.py --config samples/home_services_us.json --mock --mock-count 45
python src/fetch.py --config samples/insurance_us.json --mock --mock-count 8
python src/analyze.py --input output/<fișierul_home_services>.json
python src/analyze.py --input output/<fișierul_insurance>.json
python src/report.py --input "output/*_summary.json"
```

## Semnale calculate

- **Densitate de performeri**: câte reclame de top există în nișă (multe =
  piață activă, dar și competiție mai mare).
- **Distribuție de format**: procent pe bucket-uri de durată (0-15s, 15-30s,
  30-60s, 60s+) și obiectivul dominant.
- **Semnal de saturație**: cota primelor 3 brand-uri din topul reclamelor —
  peste 60% = piață saturată, sub 35% = piață deschisă.

## Ține minte

Tot ce arată acest tool este **semnal orientativ**, nu certitudine — "piața
asta pare activă/inactivă", nu o garanție de succes. Decizia finală rămâne
pe judecata ta.
