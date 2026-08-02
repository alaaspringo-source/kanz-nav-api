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

FUND_MAP = {
    "Suez Canal Bank Fund No. 1": ("HC_SCB_1", "صندوق بنك قناة السويس الأول"),
    "Agricultural Bank of Egypt Fund No. 2 (Al Hasad Al Yaumy)": ("HC_ABE_2", "صندوق البنك الزراعي المصري الثاني (الحصاد اليومي)"),
    "QNB (Tadawol)": ("HC_QNB_TADAWOL", "صندوق QNB (تداول)"),
    "Misr Al Mostakbal Company Investment Fund": ("HC_MISR_MOSTAKBAL", "صندوق شركة مصر المستقبل للاستثمار"),
    "Credit Agricole Bank Egypt Balanced Fund No. 4": ("HC_CAE_4", "صندوق كريدي أجريكول مصر المتوازن الرابع"),
    "FAB Misr (Al Awal) Daily Cumulative Return Fund for Liquidity": ("HC_FAB_ALAWAL", "صندوق بنك أبوظبي الأول مصر (الأول) للعائد اليومي التراكمي"),
    "FAB Misr (Etm'nan) Capital Preservation Fund": ("HC_FAB_ETMNAN", "صندوق بنك أبوظبي الأول مصر (اطمئنان) للحفاظ على رأس المال"),
}


def scrape() -> list[dict]:
    results = []
    try:
        response = requests.get(URL, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.error(f"HC Securities: HTTP {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        for row in soup.find_all("div", class_="scroll_info"):
            a = row.find("a")
            if not a:
                continue

            price_span = a.find("span")
            if not price_span:
                continue
            price_match = re.search(r"([\d.]+)", price_span.get_text())
            if not price_match:
                continue
            nav = float(price_match.group(1))
            if nav <= 0:
                continue

            # Fund name is the anchor's text minus the price span's text.
            name = a.get_text().replace(price_span.get_text(), "").strip()

            date_span = row.find("span", class_="date")
            date_val = date_span.get_text(strip=True) if date_span else "N/A"
            ticker, name_ar = FUND_MAP.get(name, ("UNC", None))

            results.append({
                "ticker": ticker,
                "name_en": name,
                "name_ar": name_ar,
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
