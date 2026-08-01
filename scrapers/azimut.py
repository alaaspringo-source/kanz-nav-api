import requests
import logging

logger = logging.getLogger(__name__)

API_URL = "https://api.azimut.eg/api/list/funds"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://azimut.eg/",
    "Origin": "https://azimut.eg",
}

FUND_MAP = {
    "az- جولد": "AZG",
    "Menthum": "MNT",
    "az- ادخار": "AZS",
    "az– ناصر": "AZN",
    "EBank": "EBANK_MM",
    "az- حالا": "HALAN",
    "az-thndr": "THNDR",
    "az- فرص": "AZO",
    "az- فرص الشريعة": "AZO_S",
    "Az-LV": "AZ_LV",
    "ABC": "ABC",
    "AZ Equity - Egypt": "AEE_USD",
    "EBank – El Khabeer": "EBANK_KH",
    "az- استحقاق T25 EGP": "T25_EGP",
    "az- استحقاق T25 USD": "T25_USD",
    "az- استحقاق  T27 USD": "T27_USD",
    "az–استحقاق  T29 USD": "T29_USD",
    "az–استحقاق  T30 USD": "T30_USD",
    "AZ – استحقاق  T33 USD": "T33_USD",
    "Brassbell": "BRASS",
    "Ataa Charity Fund": "ATAA",
    "Maashy": "MAASHY",
    "Bank Nxt - Sanady": "SANADY",
}


def scrape() -> list[dict]:
    """Fetch all Azimut funds from the official API endpoint. No key needed."""
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            logger.error(f"Azimut: API returned {response.status_code}")
            return []

        data = response.json()
        funds = data.get("data", [])
        logger.info(f"Azimut: API returned {len(funds)} funds.")

        results = []
        for fund in funds:
            name = fund.get("name", "").strip()
            last_nav = fund.get("last_nav") or {}
            nav = last_nav.get("nav")
            date = last_nav.get("date", "N/A")
            currency_obj = fund.get("currency") or {}
            currency = currency_obj.get("symbol", "EGP")

            if not name or nav is None:
                continue

            results.append({
                "ticker": FUND_MAP.get(name, "UNC"),
                "name_en": name,
                "name_ar": None,
                "nav": float(nav),
                "currency": currency,
                "date": date,
                "manager": "Azimut",
                "source": "azimut.eg",
            })

        logger.info(f"Azimut: Scraped {len(results)} funds.")
        return results

    except Exception as e:
        logger.error(f"Azimut: Critical error — {e}")
        return []
