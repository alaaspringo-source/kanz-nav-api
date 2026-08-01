import logging
import time
import os
from scrapers import beltone, hermes, azimut, ci_capital, bm, cib, afim, aaim

logger = logging.getLogger(__name__)

SCRAPER_API_KEY = "f435eb2b9040c41115dc263a6005358a"


def get_all_navs() -> list[dict]:
    all_funds = []

    scrapers = [
        ("Azimut", lambda: azimut.scrape_gold_funds()),
        ("CI Capital", lambda: ci_capital.scrape(SCRAPER_API_KEY)),
        ("Beltone", lambda: beltone.scrape(SCRAPER_API_KEY)),
        ("Hermes", lambda: hermes.scrape(SCRAPER_API_KEY)),
        ("Banque Misr", lambda: bm.scrape(SCRAPER_API_KEY)),
        ("CIB", lambda: cib.scrape(SCRAPER_API_KEY)),
        ("AFIM", lambda: afim.scrape(SCRAPER_API_KEY)),
        ("AAIM", lambda: aaim.scrape(SCRAPER_API_KEY)),
    ]

    for name, fn in scrapers:
        try:
            logger.info(f"Manager: Starting {name}...")
            data = fn()
            for item in data:
                item.setdefault("manager", name)
            all_funds.extend(data)
            logger.info(f"Manager: {name} returned {len(data)} funds.")
        except Exception as e:
            logger.error(f"Manager: {name} failed — {e}")
        time.sleep(5)

    return all_funds


def get_managed_navs(api_key: str) -> list[dict]:
    """Legacy wrapper."""
    all_funds = []
    try:
        all_funds.extend(beltone.scrape(api_key))
    except Exception as e:
        logger.error(f"Manager: Beltone failed: {e}")
    time.sleep(5)
    try:
        all_funds.extend(hermes.scrape(api_key))
    except Exception as e:
        logger.error(f"Manager: Hermes failed: {e}")
    return all_funds