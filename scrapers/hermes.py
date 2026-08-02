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
    "Bank of Alexandria Mutual Fund No. 1": ("ALEX_1", "صندوق بنك الإسكندرية الأول"),
    "Credit Agricole Mutual Fund No. 1": ("CA_1", "صندوق كريدي أجريكول الأول"),
    "Credit Agricole Mutual Fund No. 2": ("CA_2", "صندوق كريدي أجريكول الثاني"),
    "Banque du Caire Mutual Fund No. 1": ("CAIRE_1", "صندوق بنك القاهرة الأول"),
    "Egyptian Gulf Bank Mutual Fund": ("EGB_1", "صندوق بنك المصري الخليجي"),
    "SAIB's Second Investment Fund": ("SAIB_2", "صندوق بنك التنمية الصناعية الثاني"),
    "EFG Hermes Equity Fund": ("EFG_EQ", "صندوق إي إف چي هيرميس للأسهم"),
    "KFH-Alpha-Shariaa Compliant Equity Fund": ("KFH_ALPHA", "صندوق بيت التمويل الكويتي ألفا الشرعي"),
    "Al Baraka Bank Islamic Fund": ("ALBARAKA_EQ", "صندوق بنك البركة الإسلامي"),
    "Faisal Islamic Bank of Egypt Fund": ("FAISAL", "صندوق بنك فيصل الإسلامي المصري"),
    "BANK NXT (Helal) Fund 2": ("NXT_HELAL", "صندوق بنك نكست (هلال) الثاني"),
    "EFG Hermes Islamic Equity Fund": ("EFG_EQ_SHARIA", "صندوق إي إف چي هيرميس الإسلامي للأسهم"),
    "Bank of Alexandria Mutual Fund No. 2": ("ALEX_2_MM", "صندوق بنك الإسكندرية الثاني"),
    "Credit Agricole Money Market Fund No. 3": ("CA_3_MM", "صندوق كريدي أجريكول النقدي الثالث"),
    "FABMisr Money Market Fund (Modkharaty)": ("FAB_MM", "صندوق بنك أبوظبي الأول مصر النقدي (مدخراتي)"),
    "HSBC Money Market Fund": ("HSBC_MM", "صندوق إتش إس بي سي النقدي"),
    "Emirates NBD Money Market Fund (Mazid)": ("ENBD_MAZID", "صندوق بنك الإمارات دبي الوطني النقدي (مزيد)"),
    "BANK NXT Money Market Fund": ("NXT_MM", "صندوق بنك نكست النقدي"),
    "QNB Al Ahli Money Market Fund (Themar)": ("QNB_THEMAR", "صندوق QNB الأهلي النقدي (ثمار)"),
    "EFG Hermes Money Market Fund": ("EFG_MM", "صندوق إي إف چي هيرميس النقدي"),
    "Al Baraka Bank Islamic Money Market Fund (Al Barakat)": ("ALBARAKAT_MM", "صندوق بنك البركة الإسلامي النقدي (البركات)"),
    "KFH-Tharwa-Shariaa-Compliant Money Market Fund": ("KFH_THARWA", "صندوق بيت التمويل الكويتي ثروة الشرعي النقدي"),
    "Bank of Alexandria Fund No. 3": ("ALEX_3_FI", "صندوق بنك الإسكندرية الثالث"),
    "SAIB's Third Investment Fund (El Rabeh)": ("SAIB_3_FI", "صندوق بنك التنمية الصناعية الثالث (الرابح)"),
    "EFG Hermes Fixed Income Fund (USD)": ("EFG_FI_USD", "صندوق إي إف چي هيرميس للدخل الثابت بالدولار"),
    "Al Baraka Capital Fund - Manasek": ("ALBARAKA_MANASEK", "صندوق البركة كابيتال - مناسك"),
    "Egyptian Agricultural Bank (Al Massy)": ("EAB_MASSY", "صندوق البنك الزراعي المصري (الماسي)"),
    "EFG Hermes Gold Fund": ("EFG_GOLD", "صندوق إي إف چي هيرميس للذهب"),
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
            ticker, name_ar = FUND_MAP.get(name, ("UNC", None))

            results.append({
                "ticker": ticker,
                "name_en": name,
                "name_ar": name_ar,
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
