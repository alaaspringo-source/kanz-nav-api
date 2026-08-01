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

# EN name -> (ticker, AR name). Names updated to match the live site
# (several changed since the map was first written, e.g. "Alfenar" -> "El Fanar").
FUND_MAP = {
    "Iskan":            ("AAIM_ISKAN",       "اسكان"),
    "Juman":            ("AAIM_JUMAN",       "جمان"),
    "Shield":           ("AAIM_SHIELD",      "شيلد"),
    "Guard":            ("AAIM_GUARD",       "جارد"),
    "Gozoor":           ("AAIM_GOZOOR",      "جذور"),
    "Diamond":          ("AAIM_DIAMOND",     "دياموند"),
    "Misr Takaful":     ("AAIM_TAKAFUL",     "مصر للتأمين التكافلي"),
    "Istsmar w Aman":   ("AAIM_MISR_INS",    "استثمار وامان"),
    "Afaaq":            ("AAIM_AFAAQ",       "آفاق"),
    "Bareeq":           ("AAIM_BAREEQ",      "بريق"),
    "El Fanar":         ("AAIM_ALFENAR",     "الفنار"),
    "Al Tameer":        ("AAIM_ALTAMIR",     "التعمير"),
    "Kenz Foras":       ("AAIM_KANZFORSA",   "كنز فرص"),
    "Kenz Shariah":     ("AAIM_KANZSHARIA",  "كنز شريعة"),
    "Sarwaty":          ("AAIM_THERWATY",    "ثروتي الانمائي"),
    "Gosour":           ("AAIM_GUSUR",       "جسور للاستثمار"),
    "Bond$":            ("AAIM_BONDS",       "بوندز"),
}


def _scrape_page(url: str) -> list[dict]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.error(f"AAIM: HTTP {response.status_code} for {url}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        # Fund cards are anchor tags linking to individual fund pages.
        fund_cards = soup.find_all("a", href=re.compile(r"/what-we-offer/funds/[\w-]+"))
        logger.info(f"AAIM: Found {len(fund_cards)} fund cards on {url}")

        for card in fund_cards:
            text = card.get_text(strip=True)
            if not text or "coming-soon" in card.get("href", "").lower():
                pass  # still parse "coming soon" funds; skip only if no NAV found below

            # Pattern seen: "ShieldShieldEquity831.32EGPLast update 18 Jul, 2026"
            m_nav = re.search(r"([\d,]+\.?\d*)\s*(EGP|USD)", text)
            if not m_nav:
                continue
            nav = float(m_nav.group(1).replace(",", ""))
            currency = m_nav.group(2)

            m_date = re.search(r"Last update\s*([\d]{1,2}\s+\w+,?\s*\d{4})", text)
            date_val = m_date.group(1) if m_date else "N/A"

            # Fund name is the leading repeated text before the category word.
            # e.g. "ShieldShield" -> "Shield". Take text up to first digit.
            name_part = text[: m_nav.start()]
            # category words that might trail the doubled name
            name_part = re.split(
                r"Equity|Money Market|Fixed Income \(EGP\)|Fixed Income \(USD\)|Capital Protection|Sharia Compliant.*",
                name_part,
            )[0]
            # de-duplicate doubled name e.g. "ShieldShield" -> "Shield"
            half = len(name_part) // 2
            if len(name_part) % 2 == 0 and name_part[:half] == name_part[half:]:
                name_en = name_part[:half]
            else:
                name_en = name_part

            if not name_en:
                continue

            results.append({"name": name_en, "nav": nav, "currency": currency, "date": date_val})

        return results

    except Exception as e:
        logger.error(f"AAIM: Critical error for {url} — {e}")
        return []


def scrape() -> list[dict]:
    en_url = "https://aaim.com.eg/en/what-we-offer/funds"
    rows = _scrape_page(en_url)

    results = []
    for row in rows:
        name_en = row["name"]
        ticker, name_ar = FUND_MAP.get(name_en, ("UNC", None))

        results.append({
            "ticker": ticker,
            "name_en": name_en,
            "name_ar": name_ar,
            "nav": row["nav"],
            "currency": row["currency"],
            "date": row["date"],
            "manager": "AAIM",
            "manager_ar": "البنك العربي الأفريقي",
            "source": "aaim.com.eg",
        })

    logger.info(f"AAIM: Scraped {len(results)} funds.")
    return results
