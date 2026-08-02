import requests
from bs4 import BeautifulSoup
import logging
import re
import urllib3

# CI Capital's server sends an incomplete cert chain (confirmed via diagnostic:
# same request succeeds with verify=False, fails with verify=True on
# "unable to get local issuer certificate"). This is their server misconfig,
# not a MITM risk we're exposed to — this is a public GET of a price page,
# no credentials or sensitive data are ever sent.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

FUND_MAP = {
    "Banque Misr Money Market Fund (EGP)":          ("BM_MM_EGP",   "صندوق بنك مصر لأسواق النقد بالجنيه"),
    "CIB Money Market Fund (Ossoul)":               ("CIB_OSSOUL",  "صندوق CIB النقدي (أصول)"),
    "United Bank Egypt Money Market Fund (Rakhaa)": ("UB_RAKHAA",   "صندوق بنك يونايتد النقدي (رخاء)"),
    "Banque Misr Money Market Fund (USD)":          ("BM_MM_USD",   "صندوق بنك مصر لأسواق النقد بالدولار"),
    "Sarwa Life Insurance Co. Fund":                ("SARWA",       "صندوق شركة سروة للتأمين على الحياة"),
    "Fawry CI Capital Money Market Fund (Yawmy)":   ("FAWRY_MM",    "صندوق فوري سي آي كابيتال النقدي (يومي)"),
    "Allianz Co. Money Market Fund":                ("ALLIANZ_MM",  "صندوق شركة أليانز النقدي"),
    "Suez Canale Bank Money Market Fund":           ("SCB_MM",      "صندوق بنك قناة السويس النقدي"),
    "Banque Misr Money Market Fund (EUR)":          ("BM_MM_EUR",   "صندوق بنك مصر لأسواق النقد باليورو"),
    "CIAM Money Market Fund (Misr Al Youmy)":       ("CIAM_MM",     "صندوق سي آي للاستثمار النقدي (مصر اليومي)"),
    "Misr Life Insurance Co. Money Market Fund":    ("MLI_MM",      "صندوق شركة مصر للتأمين على الحياة النقدي"),
    "CIAF Money Market Fund":                       ("CIAF_MM",     "صندوق سي آي ايه اف النقدي"),
    "Basata Fund":                                  ("BASATA",      "صندوق بساطة"),
    "menthum Fixed Income Fund (USD)":              ("MNT_FI_USD",  "صندوق منثم للدخل الثابت بالدولار"),
    "CIB Fixed Income Fund (Thabat)":               ("CIB_THABAT",  "صندوق CIB للدخل الثابت (ثبات)"),
    "CIAM Fixed Income Fund (Kol Shahr)":           ("CIAM_FI",     "صندوق سي آي للدخل الثابت (كل شهر)"),
    "Banque Du Caire Fixed Income Fund (El Thabet)":("BDC_FI",      "صندوق بنك القاهرة للدخل الثابت (الثابت)"),
    "Shefa Orman Charity Fund":                     ("SHEFA",       "صندوق شفاء أورمان الخيري"),
    "CIAM Fixed Income Fund (Misr Al Yomy USD)":    ("CIAM_FI_USD", "صندوق سي آي للدخل الثابت (مصر اليومي بالدولار)"),
    "CIB Fund (4) (Hemaya)":                        ("CIB_HEMAYA",  "صندوق CIB (4) (حماية)"),
    "Banque Misr Fund Life Ins.&Capital Guranteed(EL-OMR)": ("BM_OMOR", "صندوق بنك مصر للتأمين على الحياة وضمان رأس المال (العمر)"),
    "Banque Misr First Fund":                       ("BM_FIRST",    "صندوق بنك مصر الأول"),
    "Banque Misr Second Fund":                      ("BM_SECOND",   "صندوق بنك مصر الثاني"),
    "Banque Misr Third Fund":                       ("BM_THIRD",    "صندوق بنك مصر الثالث"),
    "Banque Misr Fourth Fund (El Hosn)":            ("BM_HOSN",     "صندوق بنك مصر الرابع (الحصن)"),
    "CIB Balanced Fund":                            ("CIB_BAL",     "صندوق CIB المتوازن"),
    "Fawry Plus Fund":                              ("FAWRY_PLUS",  "صندوق فوري بلس"),
}


def scrape() -> list[dict]:
    url = "https://www.cicapital.com/fundprice/"
    results = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        if response.status_code != 200:
            logger.error(f"CI Capital: HTTP {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        update_text = soup.find(string=re.compile(r"Last update"))
        last_update = update_text.strip().replace("Last update: ", "") if update_text else "N/A"

        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            name = cols[-2].get_text(strip=True) if len(cols) >= 2 else None
            price_raw = cols[-1].get_text(strip=True).replace(",", "")

            if not name or name in ("Fund Name", "Fund Type", "Price"):
                continue

            price_match = re.search(r"(\d+\.\d+|\d+)", price_raw)
            if not price_match:
                continue

            ticker, name_ar = FUND_MAP.get(name, ("UNC", None))
            currency = "USD" if "USD" in name.upper() or "USD" in price_raw.upper() else \
                       "EUR" if "EUR" in name.upper() else "EGP"

            results.append({
                "ticker": ticker,
                "name_en": name,
                "name_ar": name_ar,
                "nav": float(price_match.group(1)),
                "currency": currency,
                "date": last_update,
                "manager": "CI Capital",
                "source": "cicapital.com",
            })

        logger.info(f"CI Capital: Scraped {len(results)} funds.")

    except Exception as e:
        logger.error(f"CI Capital: Critical error — {e}")

    return results
