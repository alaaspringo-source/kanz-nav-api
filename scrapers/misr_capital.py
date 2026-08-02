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

URL = "https://misrcapital.com/financial-services/asset-management/"

FUND_MAP = {
    "Banque Misr Second Fund": "MC_BM_2",
    "Banque Misr Third Fund": "MC_BM_3",
}


def scrape() -> list[dict]:
    """
    Confirmed via raw HTML inspection: this is plain server-rendered HTML,
    no JS needed. The "17/8/2022" date seen for Banque Misr Second Fund is
    genuinely embedded in the static response, not a JS-hydration
    placeholder — it appears the site simply hasn't updated that fund's
    NAV recently. Real, just possibly stale for some funds.

    NOTE: only funds under the initially-active category tab ("Equity
    Funds") were confirmed present in the static HTML. Other categories
    (Money Market, Fixed Income, etc.) may or may not be in the DOM
    depending on how the page is built — this scraper picks up whatever
    "sub-fund-details" blocks exist in the raw response, which may be
    fewer than the site's full fund list.
    """
    results = []
    try:
        response = requests.get(URL, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.error(f"Misr Capital: HTTP {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        for block in soup.find_all("div", class_="sub-fund-details"):
            h3 = block.find("h3")
            if not h3:
                continue
            name = h3.get_text(strip=True)

            # Find the "NAV" row specifically (not YTD%, not Inception Year).
            nav_value = None
            date_val = "N/A"
            for div in block.find_all("div"):
                h4 = div.find("h4")
                if not h4:
                    continue
                if not h4.get_text(strip=True).startswith("NAV"):
                    continue
                date_span = h4.find("span", class_="modified-date")
                if date_span:
                    dm = re.search(r"\(([\d/]+)\)", date_span.get_text())
                    if dm:
                        date_val = dm.group(1)
                value_span = div.find("span", recursive=False) or (
                    div.find_all("span")[-1] if div.find_all("span") else None
                )
                if value_span:
                    vm = re.search(r"([\d.]+)", value_span.get_text())
                    if vm:
                        nav_value = float(vm.group(1))
                break

            if nav_value is None or nav_value <= 0:
                continue

            results.append({
                "ticker": FUND_MAP.get(name, "UNC"),
                "name_en": name,
                "name_ar": None,
                "nav": nav_value,
                "currency": "EGP",
                "date": date_val,
                "manager": "Misr Capital",
                "source": "misrcapital.com",
            })

        logger.info(f"Misr Capital: Scraped {len(results)} funds.")

    except Exception as e:
        logger.error(f"Misr Capital: Critical error — {e}")

    return results
