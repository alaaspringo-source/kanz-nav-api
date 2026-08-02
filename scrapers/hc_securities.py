import requests
from bs4 import BeautifulSoup
import logging
import re

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

URL = "https://www.hc-si.com/"

# Fund name -> ticker. Names must match exactly as they appear on the site.
FUND_MAP = {
    "Suez Canal Bank Fund No. 1": "HC_SCB_1",
    "Agricultural Bank of Egypt Fund No. 2 (Al Hasad Al Yaumy)": "HC_ABE_2",
    "QNB (Tadawol)": "HC_QNB_TADAWOL",
    "Misr Al Mostakbal Company Investment Fund": "HC_MISR_MOSTAKBAL",
    "Credit Agricole Bank Egypt Balanced Fund No. 4": "HC_CAE_4",
    "FAB Misr (Al Awal) Daily Cumulative Return Fund for Liquidity": "HC_FAB_ALAWAL",
    "FAB Misr (Etm'nan) Capital Preservation Fund": "HC_FAB_ETMNAN",
}


def scrape() -> list[dict]:
    results = []
    try:
        response = requests.get(URL, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.error(f"HC Securities: HTTP {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n")

        # Pattern seen: "Fund Name{1982.15}" followed later by a date like
        # "2026-07-30" (may be same line or the next non-empty line).
        pattern = re.compile(r"([^\n{}]{5,120})\{([\d.]+)\}")
        lines = text.split("\n")

        for i, line in enumerate(lines):
            m = pattern.search(line)
            if not m:
                continue
            name = m.group(1).strip()
            nav = float(m.group(2))
            if nav <= 0:
                continue

            # Look ahead a few lines for a date pattern.
            date_val = "N/A"
            for j in range(i, min(i + 4, len(lines))):
                dm = re.search(r"\d{4}-\d{2}-\d{2}", lines[j])
                if dm:
                    date_val = dm.group(0)
                    break

            results.append({
                "ticker": FUND_MAP.get(name, "UNC"),
                "name_en": name,
                "name_ar": None,
                "nav": nav,
                "currency": "EGP",
                "date": date_val,
                "manager": "HC Securities",
                "source": "hc-si.com",
            })

        logger.info(f"HC Securities: Scraped {len(results)} funds.")

    except Exception as e:
        logger.error(f"HC Securities: Critical error — {e}")

    return results
