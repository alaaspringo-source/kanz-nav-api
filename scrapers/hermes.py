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

FUND_MAP = {
    "Bank of Alexandria Mutual Fund No. 1": "ALEX_1",
    "Credit Agricole Mutual Fund No. 1": "CA_1",
    "Credit Agricole Mutual Fund No. 2": "CA_2",
    "Banque du Caire Mutual Fund No. 1": "CAIRE_1",
    "Egyptian Gulf Bank Mutual Fund": "EGB_1",
    "SAIB's Second Investment Fund": "SAIB_2",
    "EFG Hermes Equity Fund": "EFG_EQ",
    "KFH-Alpha-Shariaa Compliant Equity Fund": "KFH_ALPHA",
    "Al Baraka Bank Islamic Fund": "ALBARAKA_EQ",
    "Faisal Islamic Bank of Egypt Fund": "FAISAL",
    "BANK NXT (Helal) Fund 2": "NXT_HELAL",
    "EFG Hermes Islamic Equity Fund": "EFG_EQ_SHARIA",
    "Bank of Alexandria Mutual Fund No. 2": "ALEX_2_MM",
    "Credit Agricole Money Market Fund No. 3": "CA_3_MM",
    "FABMisr Money Market Fund (Modkharaty)": "FAB_MM",
    "HSBC Money Market Fund": "HSBC_MM",
    "Emirates NBD Money Market Fund (Mazid)": "ENBD_MAZID",
    "BANK NXT Money Market Fund": "NXT_MM",
    "QNB Al Ahli Money Market Fund (Themar)": "QNB_THEMAR",
    "EFG Hermes Money Market Fund": "EFG_MM",
    "Al Baraka Bank Islamic Money Market Fund (Al Barakat)": "ALBARAKAT_MM",
    "KFH-Tharwa-Shariaa-Compliant Money Market Fund": "KFH_THARWA",
    "Bank of Alexandria Fund No. 3": "ALEX_3_FI",
    "SAIB's Third Investment Fund (El Rabeh)": "SAIB_3_FI",
    "EFG Hermes Fixed Income Fund (USD)": "EFG_FI_USD",
    "Al Baraka Capital Fund - Manasek": "ALBARAKA_MANASEK",
    "Egyptian Agricultural Bank (Al Massy)": "EAB_MASSY",
    "EFG Hermes Gold Fund": "EFG_GOLD",
}

SKIP_NAMES = {
    "fund name", "conventional equity funds", "sharia compliant funds",
    "money market funds", "islamic money market funds", "fixed income funds",
    "fixed income funds usd", "islamic fixed income funds", "blended funds",
    "gold funds",
}


def scrape() -> list[dict]:
    url = "https://efgholding.com/en/our-services/mutual-funds"
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.error(f"Hermes: HTTP {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            name = cols[0].get_text(strip=True)
            if not name or name.lower() in SKIP_NAMES:
                continue

            price_raw = cols[1].get_text(strip=True).replace(",", "")
            price_match = re.search(r"(\d+\.?\d*)", price_raw)
            if not price_match:
                continue

            date_val = cols[4].get_text(strip=True) if len(cols) > 4 else "N/A"
            currency = "USD" if "USD" in name.upper() else "EGP"

            results.append({
                "ticker": FUND_MAP.get(name, "UNC"),
                "name_en": name,
                "name_ar": None,
                "nav": float(price_match.group(1)),
                "currency": currency,
                "date": date_val,
                "manager": "Hermes",
                "source": "efgholding.com",
            })

        logger.info(f"Hermes: Scraped {len(results)} funds.")
        return results

    except Exception as e:
        logger.error(f"Hermes: Critical error — {e}")
        return []
