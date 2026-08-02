import requests
import logging

logger = logging.getLogger(__name__)

# api.azimut.eg TLS-rejects connections from datacenter/cloud IP ranges
# (confirmed: TLSV1_UNRECOGNIZED_NAME at the handshake, consistent across
# GitHub Actions runners). app.azimut.eg serves the same fund list data and
# is not blocked — use this instead.
API_URL = "https://app.azimut.eg/api/fund/list?size=100&web=true"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://azimut.eg/",
}

FUND_MAP = {
    "az- جولد": ("AZG", "أزيموت جولد"),
    "Menthum": ("MNT", "منثم"),
    "az- ادخار": ("AZS", "أزيموت ادخار"),
    "az– ناصر": ("AZN", "أزيموت ناصر"),
    "EBank": ("EBANK_MM", "إي بنك"),
    "az- حالا": ("HALAN", "أزيموت حالا"),
    "az-thndr": ("THNDR", "أزيموت ثندر"),
    "az- فرص": ("AZO", "أزيموت فرص"),
    "az- فرص الشريعة": ("AZO_S", "أزيموت فرص الشريعة"),
    "Az-LV": ("AZ_LV", "أزيموت إل في"),
    "ABC": ("ABC", "إيه بي سي"),
    "AZ Equity - Egypt": ("AEE_USD", "أزيموت للأسهم - مصر"),
    "EBank – El Khabeer": ("EBANK_KH", "إي بنك - الخبير"),
    "az- استحقاق T25 EGP": ("T25_EGP", "أزيموت استحقاق تي25 جنيه"),
    "az- استحقاق T25 USD": ("T25_USD", "أزيموت استحقاق تي25 دولار"),
    "az- استحقاق  T27 USD": ("T27_USD", "أزيموت استحقاق تي27 دولار"),
    "az–استحقاق  T29 USD": ("T29_USD", "أزيموت استحقاق تي29 دولار"),
    "az–استحقاق  T30 USD": ("T30_USD", "أزيموت استحقاق تي30 دولار"),
    "AZ – استحقاق  T33 USD": ("T33_USD", "أزيموت استحقاق تي33 دولار"),
    "Brassbell": ("BRASS", "براسبيل"),
    "Ataa Charity Fund": ("ATAA", "صندوق عطاء الخيري"),
    "Maashy": ("MAASHY", "معاشي"),
    "Bank Nxt - Sanady": ("SANADY", "بنك نكست - سندي"),
    "az- فاليو": ("AZ_FALYO", "أزيموت فاليو"),
}


def scrape() -> list[dict]:
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            logger.error(f"Azimut: API returned {response.status_code}")
            return []

        data = response.json()
        funds = data.get("response", {}).get("funds", {}).get("dataList", [])
        logger.info(f"Azimut: API returned {len(funds)} funds.")

        results = []
        for fund in funds:
            name = (fund.get("name") or "").strip()
            last_nav = fund.get("last_nav") or {}
            nav = last_nav.get("nav")
            date = last_nav.get("date", "N/A")
            currency_obj = fund.get("currency") or {}
            currency = currency_obj.get("symbol", "EGP")

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
                "manager": "Azimut",
                "source": "azimut.eg",
            })

        logger.info(f"Azimut: Scraped {len(results)} funds.")
        return results

    except Exception as e:
        logger.error(f"Azimut: Critical error — {e}")
        return []
