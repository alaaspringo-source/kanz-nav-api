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

URL = "https://nicapital.com.eg/lines-of-business/asset-management/"

FUND_MAP = {
    "SIULA MONEY MARKET FUND": ("NI_SIULA", "صندوق سيولة النقدي"),
    "15/30 Fixed Income Fund": ("NI_1530", "صندوق 15/30 للدخل الثابت"),
    "MAKASEB 1st Tranche": ("NI_MAKASEB_1", "صندوق مكاسب الشريحة الأولى"),
    "MAKASEB 2nd Tranche": ("NI_MAKASEB_2", "صندوق مكاسب الشريحة الثانية"),
    "SAHMY FUND": ("NI_SAHMY", "صندوق سهمي"),
    "SAHMY 70 FUND": ("NI_SAHMY_70", "صندوق سهمي 70"),
    "EDUCATION FOR LIFE": ("NI_EDU_LIFE", "صندوق التعليم من أجل الحياة"),
}


def scrape() -> list[dict]:
    results = []
    try:
        response = requests.get(URL, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.error(f"NI Capital: HTTP {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n")
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # Pattern per fund block (seen in the "FUNDS CERTIFICATES PRICES"
        # section): NAME ... date ... "Certificate Price" ... price (with
        # or without an "EGP" prefix on the same/next line).
        for i, line in enumerate(lines):
            if line != "Certificate Price":
                continue

            # Price is the next non-empty line, possibly "EGP 24.27184"
            # or just "198.1782".
            if i + 1 >= len(lines):
                continue
            price_line = lines[i + 1]
            price_match = re.search(r"(\d+\.\d+|\d+)", price_line)
            if not price_match:
                continue
            nav = float(price_match.group(1))

            # Date is usually 1-2 lines before "Certificate Price".
            date_val = "N/A"
            for j in range(max(0, i - 3), i):
                if re.search(r"\d{4}", lines[j]) and re.search(r"[A-Za-z]", lines[j]):
                    date_val = lines[j]
                    break

            # Fund name: search backwards for the nearest ALL-CAPS-ish
            # heading line before the date (skip image/blank noise).
            name = None
            for j in range(i - 1, max(0, i - 8), -1):
                candidate = lines[j]
                if candidate == date_val:
                    continue
                if re.match(r"^\d", candidate):
                    continue
                if len(candidate) > 3 and not candidate.startswith("http"):
                    name = candidate
                    break

            if not name or nav <= 0:
                continue

            ticker, name_ar = FUND_MAP.get(name, ("UNC", None))

            results.append({
                "ticker": ticker,
                "name_en": name,
                "name_ar": name_ar,
                "nav": nav,
                "currency": "EGP",
                "date": date_val,
                "manager": "NI Capital",
                "source": "nicapital.com.eg",
            })

        logger.info(f"NI Capital: Scraped {len(results)} funds.")

    except Exception as e:
        logger.error(f"NI Capital: Critical error — {e}")

    return results
