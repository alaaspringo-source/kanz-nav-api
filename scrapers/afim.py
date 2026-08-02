from bs4 import BeautifulSoup
import logging
import re

from scrapers._render import fetch_rendered_html

logger = logging.getLogger(__name__)

URL = "https://www.afim.com.eg/public/investment"

FUND_MAP = {
    "صندوق الواعد": ("AFIM_ELWAED", "El Waed - Fixed Income"),
    "صندوق حورس": ("AFIM_HOURAS", "Houras - Money Market"),
    "صندوق تميز": ("AFIM_TAMAYOZ", "Tamayoz - Money Market"),
    "الصندوق الرابع": ("NBE_4_MM", "NBE Fund 4 - Money Market"),
    "صندوق وثاق": ("WETHAQ_MM", "Wethaq Fund - Money Market"),
    "صندوق بشائر": ("BASHAYER", "Bashayer - Islamic Fund"),
    "الصندوق الأول": ("NBE_1_BAL", "NBE Fund 1 - Balanced"),
    "صندوق الأهلي حياة": ("AHLY_HAYAH", "Al Ahly Hayah - Balanced"),
    "الصندوق الثاني": ("NBE_2_EQ", "NBE Fund 2 - Equity"),
    "الصندوق الثالث": ("NBE_3_EQ", "NBE Fund 3 - Equity"),
    "الصندوق الخامس": ("NBE_5_EQ", "NBE Fund 5 - Equity"),
    "الصندوق السابع": ("NBE_7", "NBE Fund 7"),
    "صندوق دهب": ("AFIM_GOLD", "Dahab Gold Fund"),
}


def scrape() -> list[dict]:
    # No stable selector to wait on before the challenge page swaps to real
    # content, so use the fixed-wait fallback (page JS-reloads at ~5s).
    html = fetch_rendered_html(URL, wait_ms=12000)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    results = []

    for a in soup.find_all("a"):
        text = a.get_text(" ", strip=True)
        m = re.search(r"سعر الوثيقة:\s*([\d.]+)\s*جنيه", text)
        if not m:
            continue

        nav = float(m.group(1))
        name_ar = text.split("اقرأ المزيد")[0].strip()
        if not name_ar:
            continue

        ticker, name_en = ("UNC", name_ar)
        for key, (t, en) in FUND_MAP.items():
            if key in name_ar:
                ticker, name_en = t, en
                break

        results.append({
            "ticker": ticker,
            "name_en": name_en,
            "name_ar": name_ar,
            "nav": nav,
            "currency": "EGP",
            "date": "N/A",
            "manager": "AFIM",
            "source": "afim.com.eg",
        })

    logger.info(f"AFIM: Scraped {len(results)} funds.")
    return results
