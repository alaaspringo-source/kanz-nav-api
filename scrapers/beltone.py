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

# NOTE: this URL changed from /asset-management to /asset-management-1 —
# the old slug now 404s ("Business Line not found"). Verify periodically.
URL = "https://www.beltoneholding.com/en/business-line/asset-management-1"

# AR names are hardcoded (like ci_capital.py) rather than scraping a second
# AR page, since the AR page structure/slug may drift independently.
FUND_MAP = {
    'MID Bank Fund 2': ('MID_BANK_2', 'صندوق بنك إم آي دي الثاني'),
    'ABC (Mazaya)': ('ABC_MAZAYA', 'صندوق البنك العربي الأفريقي (مزايا)'),
    'Banque Du Caire II (El Kahera El Yawmi)': ('BDC_II', 'صندوق بنك القاهرة الثاني (القاهرة اليومي)'),
    'Arab Bank (Yomaty)': ('ARAB_YOMATY', 'صندوق البنك العربي (يوماتي)'),
    'SAIB Money Market Fund': ('SAIB_MM', 'صندوق SAIB النقدي'),
    'Misr Insurance Fund': ('MISR_INS', 'صندوق مصر للتأمين'),
    'Attijariwafa Bank Money Market Fund': ('ATTIJARI_MM', 'صندوق التجاري وفا بنك النقدي'),
    'Beltone 3rd tranche "B-Yawmy" Fund': ('B_YAWMY', 'صندوق بيلتون الشريحة الثالثة (يومي)'),
    'ADIB Islamic': ('ADIB_MM', 'صندوق بنك أبوظبي الإسلامي'),
    'EGX 30 ETF': ('EGX30_ETF', 'صندوق EGX30 المتداول'),
    'Beltone EGX33 "Wafra" Shariah Tracker': ('B_EGX33_SHARIA', 'صندوق بيلتون EGX33 الشرعي (وفرة)'),
    'Beltone EGX100 Tracker': ('B_EGX100', 'صندوق بيلتون EGX100'),
    'Beltone Financial Fund': ('B_FINANCIAL', 'صندوق بيلتون المالي'),
    'Beltone Real Estate Fund': ('B_REALESTATE', 'صندوق بيلتون العقاري'),
    'Beltone Industrial Fund': ('B_INDUSTRIAL', 'صندوق بيلتون الصناعي'),
    'Beltone Consumer Fund': ('B_CONSUMER', 'صندوق بيلتون الاستهلاكي'),
    'Menthum Grow Fund': ('MNT_GROW', 'صندوق منثم جرو'),
    'EGX35-LV': ('EGX35_LV', 'صندوق EGX35 LV'),
    'Beltone EGX70 Tracker': ('B_EGX70', 'صندوق بيلتون EGX70'),
    'Beltone Evolve Gold Fund "Sabayek"': ('SABAYEK', 'صندوق بيلتون إيفولف للذهب (سبايك)'),
    'Beltone Evolve Silver Fund "Fadda"': ('FADDA', 'صندوق بيلتون إيفولف للفضة (فضة)'),
    'B- Alpha': ('B_ALPHA', 'صندوق بيلتون ألفا'),
    'Suez Canal Bank II (Agial)': ('SCB_AGIAL', 'صندوق بنك قناة السويس الثاني (أجيال)'),
    'MID Bank Fund 1': ('MID_BANK_1', 'صندوق بنك إم آي دي الأول'),
    'Beltone Gems Equity Fund- USD': ('B_GEMS', 'صندوق بيلتون جيمز'),
    'QNBA Tawazon': ('QNBA_TAWAZON', 'صندوق QNB الأهلي توازن'),
    'Beltone Fixed Income Fund "B-Secure"': ('B_SECURE', 'صندوق بيلتون للدخل الثابت (بي سكيور)'),
    'Beltone 2nd tranche "B-Cobonat" Fund': ('B_COBONAT', 'صندوق بيلتون الشريحة الثانية (كوبونات)'),
    'Egyptian Sport Fund': ('EGYPT_SPORT', 'صندوق الرياضة المصري'),
    'Beltone Fixed Income USD Fund': ('B_SECURE_USD', 'صندوق بيلتون للدخل الثابت بالدولار'),
}

SKIP_NAMES = {"fund name", ""}


def scrape() -> list[dict]:
    try:
        response = requests.get(URL, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logger.error(f"Beltone: HTTP {response.status_code}")
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

            nav = float(price_match.group(1))
            if nav <= 0:
                continue

            currency = "USD" if "USD" in name.upper() else "EGP"
            ticker, name_ar = FUND_MAP.get(name, ("UNC", None))
            date_val = cols[3].get_text(strip=True) if len(cols) > 3 else "N/A"

            results.append({
                "ticker": ticker,
                "name_en": name,
                "name_ar": name_ar,
                "nav": nav,
                "currency": currency,
                "date": date_val,
                "manager": "Beltone",
                "source": "beltoneholding.com",
            })

        logger.info(f"Beltone: Scraped {len(results)} funds.")
        return results

    except Exception as e:
        logger.error(f"Beltone: Critical error — {e}")
        return []
