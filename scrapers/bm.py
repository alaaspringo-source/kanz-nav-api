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
    "Banque Misr First Mutual Fund - First Issue - Quarterly periodic income": ("BM_FIRST", "صندوق بنك مصر الأول - الإصدار الأول - دخل دوري ربع سنوي"),
    "Banque Misr Mutual Fund - Second Issue - Capital growth": ("BM_SECOND", "صندوق بنك مصر - الإصدار الثاني - نمو رأسمالي"),
    "Banque Misr Capital Guaranteed Fund (Sandouk El Umr)": ("BM_UMR", "صندوق بنك مصر لضمان رأس المال (صندوق العمر)"),
    "Banque Misr Mutual Fund in Egyptian Pounds with a daily cumulative return (day by day)": ("BM_MM_EGP", "صندوق بنك مصر بالجنيه المصري ذو العائد اليومي التراكمي (يوم بيوم)"),
    'Banque Misr Fund IV "In accordance with provisions of Islamic Sharia Law" (EL Hessn)': ("BM_HOSN", "صندوق بنك مصر الرابع (الحصن) المتوافق مع الشريعة الإسلامية"),
    "Banque Misr's third Mutual fund with cumulative return and periodic distribution": ("BM_THIRD", "صندوق بنك مصر الثالث ذو العائد التراكمي والتوزيع الدوري"),
    "Banque Misr Mutual Fund in Dollar with a daily cumulative return (day by day Dollar)": ("BM_MM_USD", "صندوق بنك مصر بالدولار ذو العائد اليومي التراكمي (يوم بيوم دولار)"),
    "Banque Misr Mutual Fund in Euro with a daily cumulative return (day by day Euro)": ("BM_MM_EUR", "صندوق بنك مصر باليورو ذو العائد اليومي التراكمي (يوم بيوم يورو)"),
    "Misr Capital Investment Fund to invest in debt instruments with periodic returns": ("MISR_CAP_DEBT", "صندوق مصر كابيتال للاستثمار في أدوات الدين ذو العائد الدوري"),
    "Egyptian Sports Fund": ("EGYPT_SPORT_BM", "الصندوق الرياضي المصري"),
    "CI Asset Fund with Cumulative Daily Yield - Misr Daily": ("CI_MISR_DAILY", "صندوق سي آي ذو العائد اليومي التراكمي (مصر اليومي)"),
    "CI Asset Management Investment Fund for Investment in Gold with Daily Cumulative Return - Gold Misr": ("CI_GOLD_MISR", "صندوق سي آي للاستثمار في الذهب ذو العائد اليومي التراكمي (جولد مصر)"),
}


def scrape() -> list[dict]:
    url = "https://www.banquemisr.com/en/CAPITAL-MARKETS/Mutual-Funds"
    results = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.error(f"BM: HTTP {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            if any(h in cols[0].get_text() for h in ["#", "رقم"]):
                continue

            name = cols[1].get_text(strip=True)
            price_raw = cols[2].get_text(strip=True).replace(",", "")

            if not name:
                continue

            price_match = re.search(r"(\d+\.\d+|\d+)", price_raw)
            if not price_match:
                continue

            currency = "USD" if "Dollar" in price_raw else "EUR" if "Euro" in price_raw else "EGP"
            ticker, name_ar = FUND_MAP.get(name, ("UNC", None))

            results.append({
                "ticker": ticker,
                "name_en": name,
                "name_ar": name_ar,
                "nav": float(price_match.group(1)),
                "currency": currency,
                "date": "N/A",
                "manager": "Banque Misr",
                "source": "banquemisr.com",
            })

        logger.info(f"BM: Scraped {len(results)} funds.")

    except Exception as e:
        logger.error(f"BM: Critical error — {e}")

    return results
