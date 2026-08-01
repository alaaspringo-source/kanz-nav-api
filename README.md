# Kanz NAV Scraper

Scrapes Egyptian mutual fund NAVs from 8 fund manager sources and writes
them to Firestore. Runs on a GitHub Actions cron schedule (twice daily) —
no server, no Docker, no paid rendering proxy.

## Local run
```
pip install -r requirements.txt
export FIREBASE_SERVICE_ACCOUNT_JSON="$(cat serviceAccount.json)"
python run_all.py
```

## Sources
Azimut, CIB — direct JSON APIs.
Beltone, Hermes, AAIM, AFIM, Banque Misr, CI Capital — plain HTML scrape
(all confirmed server-rendered, no JS/headless browser needed).
