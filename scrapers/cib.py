import requests
import logging

logger = logging.getLogger(__name__)

API_URL = "https://www.cibeg.com/api/fund/getfunds"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.cibeg.com/en/personal/fund-prices",
    "Accept": "application/json, text/plain, */*",
}

FUND_MAP = {
    "Osoul Fund":            ("CIB_OSSOUL",  "صندوق أصول"),
    "Istethmar Fund":        ("CIB_IST",     "إستثمار"),
    "Aman Fund":             ("CIB_AMAN",    "أمان"),
    "Hemaya Fund":           ("CIB_HEMAYA",  "حماية"),
    "Thabat Fund":           ("CIB_THABAT",  "ثبات"),
    "Misr Almustaqbal Fund": ("CIB_MST",     "مصر المستقبل"),
    "Takamel Fund":          ("CIB_TAK",     "تكامل"),
    "Osoul":                 ("CIB_OSSOUL",  "صندوق أصول"),
    "Istethmar":             ("CIB_IST",     "إستثمار"),
    "Aman":                  ("CIB_AMAN",    "أمان"),
    "Hemaya":                ("CIB_HEMAYA",  "حماية"),
    "Thabat":                ("CIB_THABAT",  "ثبات"),
    "Misr Almustaqbal":      ("CIB_MST",     "مصر المستقبل"),
    "Takamel":               ("CIB_TAK",     "تكامل"),
}


def _parse_date(raw: str) -> str:
    """Convert '20260401.0' to '01-04-2026'."""
    try:
        s = str(raw).split(".")[0]
        return f"{s[6:8]}-{s[4:6]}-{s[0:4]}"
    except Exception:
        return str(raw)


def scrape() -> list[dict]:
    """Fetch CIB fund NAVs directly from the official JSON endpoint. No key needed."""
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=30)

        if response.status_code != 200:
            logger.error(f"CIB: API returned {response.status_code}")
            return []

        if not response.content or not response.text.strip():
            logger.error("CIB: Empty response body")
            return []

        data = response.json()
        nav_list = data.get("fundNavList", {}).get("navList", [])
        logger.info(f"CIB: API returned {len(nav_list)} funds.")

        results = []
        for fund in nav_list:
            name = fund.get("fundTitle", "").strip()
            nav = fund.get("nav")
            currency = fund.get("fundCurrency", "EGP")
            date = _parse_date(fund.get("navDate", ""))

            if not name or nav is None:
                continue

            ticker, name_ar = FUND_MAP.get(name, ("UNC", None))

            results.append({
                "ticker": ticker,
                "name_en": name,
                "name_ar": name_ar,
                "nav": float(nav),
                "currency": currency,
                "date": date,
                "manager": "CIB",
                "source": "cibeg.com",
            })

        logger.info(f"CIB: Scraped {len(results)} funds.")
        return results

    except Exception as e:
        logger.error(f"CIB: Critical error — {e}")
        return []
