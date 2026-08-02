import requests
from bs4 import BeautifulSoup
import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

URL = "https://misrcapital.com/financial-services/asset-management/"

FUND_MAP = {
    "Banque Misr Second Fund": "MC_BM_2",
    "Banque Misr Third Fund": "MC_BM_3",
    # Add more as they're seen in real scrape output — the page uses an
    # accordion with more funds than were visible in initial inspection.
}


def scrape() -> list[dict]:
    """
    NOTE: initial inspection showed a fund's NAV date as "17/8/2022" —
    a live site should not show a 3+ year old date. This strongly suggests
    either (a) the page shows stale/placeholder data until a JS widget
    hydrates it with live numbers, or (b) that specific fund just hasn't
    been repriced (less likely for a bank fund). Either way: this scraper
    includes a freshness check that logs a warning (but still returns data)
    if dates look stale, so the first real run makes the situation obvious
    in the logs rather than silently caching bad data.
    """
    results = []
    stale_count = 0
    try:
        response = requests.get(URL, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.error(f"Misr Capital: HTTP {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n")
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        for i, line in enumerate(lines):
            nav_header = re.match(r"NAV\s*\((\d{1,2}/\d{1,2}/\d{4})\)", line)
            if not nav_header:
                continue

            date_str = nav_header.group(1)
            if i + 1 >= len(lines):
                continue
            price_match = re.search(r"(\d+\.\d+|\d+)", lines[i + 1])
            if not price_match:
                continue
            nav = float(price_match.group(1))
            if nav <= 0:
                continue

            # Fund name: nearest heading-like line before this block.
            name = None
            for j in range(i - 1, max(0, i - 10), -1):
                candidate = lines[j]
                if candidate.startswith("#") or re.match(r"^\d", candidate):
                    continue
                if len(candidate) > 3 and "Fund" in candidate:
                    name = candidate
                    break

            if not name:
                continue

            # Freshness check
            try:
                fund_date = datetime.strptime(date_str, "%d/%m/%Y")
                if datetime.now() - fund_date > timedelta(days=30):
                    stale_count += 1
            except ValueError:
                pass

            results.append({
                "ticker": FUND_MAP.get(name, "UNC"),
                "name_en": name,
                "name_ar": None,
                "nav": nav,
                "currency": "EGP",
                "date": date_str,
                "manager": "Misr Capital",
                "source": "misrcapital.com",
            })

        if stale_count > 0:
            logger.warning(
                f"Misr Capital: {stale_count}/{len(results)} funds have dates "
                f"older than 30 days — likely stale/placeholder data, not a "
                f"live feed. Verify before trusting this source."
            )

        logger.info(f"Misr Capital: Scraped {len(results)} funds.")

    except Exception as e:
        logger.error(f"Misr Capital: Critical error — {e}")

    return results
