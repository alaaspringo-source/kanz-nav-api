"""
Kanz NAV scraper — run-once entrypoint.

Runs all 8 fund manager scrapers, merges results, and writes them to
Firestore. Designed to be invoked by a GitHub Actions cron job twice a day —
no server, no scheduler process, no ScraperAPI/Playwright dependency.

Local test:
    export FIREBASE_SERVICE_ACCOUNT_JSON="$(cat path/to/serviceAccount.json)"
    python run_all.py
"""
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore

from scrapers import aaim, afim, azimut, beltone, bm, ci_capital, cib, hermes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_all")


def get_all_navs() -> list[dict]:
    all_funds = []

    scrapers = [
        ("Azimut", azimut.scrape),
        ("CIB", cib.scrape),
        ("Beltone", beltone.scrape),
        ("Hermes", hermes.scrape),
        ("Banque Misr", bm.scrape),
        ("AFIM", afim.scrape),
        ("AAIM", aaim.scrape),
        ("CI Capital", ci_capital.scrape),
    ]

    for name, fn in scrapers:
        try:
            logger.info(f"Starting {name}...")
            data = fn()
            for item in data:
                item.setdefault("manager", name)
            all_funds.extend(data)
            logger.info(f"{name} returned {len(data)} funds.")
        except Exception as e:
            logger.error(f"{name} failed — {e}")
        time.sleep(2)  # be polite to source sites

    return all_funds


def init_firestore():
    """Auth from a service account JSON passed via env var (GitHub secret)."""
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not raw:
        logger.error("FIREBASE_SERVICE_ACCOUNT_JSON env var not set.")
        sys.exit(1)

    cred_dict = json.loads(raw)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    return firestore.client()


def write_to_firestore(db, funds: list[dict]):
    """Writes each fund to nav/{ticker} and a metadata doc with last-run info.

    Funds with no usable ticker (UNC) fall back to a slug of their name so
    they don't collide/overwrite each other under a shared 'UNC' key.
    """
    batch = db.batch()
    written = 0
    seen_keys = set()

    for fund in funds:
        ticker = fund.get("ticker") or "UNC"
        if ticker == "UNC":
            slug = "".join(c if c.isalnum() else "_" for c in (fund.get("name_en") or "unknown"))
            key = f"UNC_{fund.get('manager','?')}_{slug}"[:120]
        else:
            key = ticker

        # avoid clobbering if two funds resolve to the same key
        if key in seen_keys:
            key = f"{key}_{written}"
        seen_keys.add(key)

        doc_ref = db.collection("nav").document(key)
        payload = {**fund, "scraped_at": datetime.now(timezone.utc).isoformat()}
        batch.set(doc_ref, payload)
        written += 1

        # Firestore batches cap at 500 writes
        if written % 400 == 0:
            batch.commit()
            batch = db.batch()

    batch.commit()

    db.collection("nav_meta").document("status").set({
        "last_scraped": datetime.now(timezone.utc).isoformat(),
        "fund_count": written,
    })

    logger.info(f"Wrote {written} funds to Firestore.")


def main():
    funds = get_all_navs()
    logger.info(f"Total funds scraped across all managers: {len(funds)}")

    if not funds:
        logger.error("No funds scraped from any source — aborting write to avoid wiping good data.")
        sys.exit(1)

    db = init_firestore()
    write_to_firestore(db, funds)


if __name__ == "__main__":
    main()
