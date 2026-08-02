from bs4 import BeautifulSoup
import logging
import re

from scrapers._render import fetch_rendered_html

logger = logging.getLogger(__name__)

URL = "https://www.beltoneholding.com/en/business-line/asset-management-1"

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


def _norm(s: str) -> str:
    return s.replace("\u2019", "'").replace("\u2018", "'").replace('\u201c', '"').replace('\u201d', '"').strip()


FUND_MAP = {_norm(k): v for k, v in FUND_MAP.items()}


def scrape() -> list[dict]:
    html = fetch_rendered_html(URL, wait_ms=8000)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    results = []

    # Fund name: <p class="min-w-[200px] ...">
    name_els = soup.find_all("p", class_=lambda c: c and "min-w-[200px]" in c)
    logger.info(f"Beltone: Found {len(name_els)} fund name elements.")

    for name_el in name_els:
        name = name_el.get_text(strip=True)
        if not name or name.lower() in SKIP_NAMES:
            continue

        # Row container: walk up to the div holding both name and the
        # price/date/date/ytd group, then find the price cell (w-[144px]).
        row = name_el.find_parent("div", class_=lambda c: c and "box-border" in c)
        if not row:
            continue

        price_el = row.find("p", class_=lambda c: c and "w-[144px]" in c)
        if not price_el:
            continue

        price_raw = price_el.get_text(strip=True).replace(",", "")
        price_match = re.search(r"(\d+\.?\d*)", price_raw)
        if not price_match:
            continue

        nav = float(price_match.group(1))
        if nav <= 0:
            continue

        # Column order confirmed: price (w-144), inception date (w-126),
        # last update date (w-104), YTD% (w-104). We want "last update".
        date_els = row.find_all("p", class_=lambda c: c and "w-[104px]" in c)
        date_val = date_els[0].get_text(strip=True) if date_els else "N/A"

        currency = "USD" if "USD" in name.upper() else "EGP"
        ticker, name_ar = FUND_MAP.get(_norm(name), ("UNC", None))

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
