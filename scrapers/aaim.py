from bs4 import BeautifulSoup
import logging
import re

from scrapers._render import fetch_rendered_html

logger = logging.getLogger(__name__)

URL = "https://aaim.com.eg/en/what-we-offer/funds"

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


def scrape() -> list[dict]:
    html = fetch_rendered_html(URL, wait_ms=12000)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    results = []

    fund_cards = soup.find_all("a", href=re.compile(r"/what-we-offer/funds/[\w-]+"))
    logger.info(f"AAIM: Found {len(fund_cards)} fund cards.")

    for card in fund_cards:
        text = card.get_text(strip=True)

        m_nav = re.search(r"([\d,]+\.?\d*)\s*(EGP|USD)", text)
        if not m_nav:
            continue
        nav = float(m_nav.group(1).replace(",", ""))
        currency = m_nav.group(2)

        m_date = re.search(r"Last update\s*([\d]{1,2}\s+\w+,?\s*\d{4})", text)
        date_val = m_date.group(1) if m_date else "N/A"

        name_part = text[: m_nav.start()]
        name_part = re.split(
            r"Equity|Money Market|Fixed Income \(EGP\)|Fixed Income \(USD\)|Capital Protection|Sharia Compliant.*",
            name_part,
        )[0]
        half = len(name_part) // 2
        name_en = name_part[:half] if (len(name_part) % 2 == 0 and name_part[:half] == name_part[half:]) else name_part

        if not name_en:
            continue

        ticker, name_ar = FUND_MAP.get(name_en, ("UNC", None))

        results.append({
            "ticker": ticker,
            "name_en": name_en,
            "name_ar": name_ar,
            "nav": nav,
            "currency": currency,
            "date": date_val,
            "manager": "AAIM",
            "manager_ar": "البنك العربي الأفريقي",
            "source": "aaim.com.eg",
        })

    logger.info(f"AAIM: Scraped {len(results)} funds.")
    return results
