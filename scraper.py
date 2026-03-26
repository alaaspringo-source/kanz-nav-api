import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

EGX_GOLD_URL = "https://www.egx.com.eg/en/GoldCompanyDataPageAll.aspx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def scrape_gold_funds() -> list[dict]:
    """
    Scrapes the EGX gold investment fund indicators page.
    Returns a list of dicts with keys: name, nav, date, manager
    """
    try:
        response = requests.get(EGX_GOLD_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch EGX gold page: {e}")
        raise

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the main data table — EGX uses a standard HTML table
    tables = soup.find_all("table")
    if not tables:
        raise ValueError("No tables found on EGX gold page — page structure may have changed")

    funds = []

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]

            # Expected columns: Fund Name, Manager, Avg price/gram, NAV Price, Date
            if len(cols) < 4:
                continue

            # Skip rows that are clearly headers or footers
            if not cols[0] or cols[0].lower() in ("fund name", ""):
                continue

            # Try to parse NAV — it's a float
            try:
                nav = float(cols[3].replace(",", ""))
            except (ValueError, IndexError):
                continue

            # Try to parse date
            try:
                raw_date = cols[4] if len(cols) > 4 else ""
                date = datetime.strptime(raw_date, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                date = None

            funds.append({
                "name": cols[0],
                "manager": cols[1] if len(cols) > 1 else None,
                "nav": nav,
                "date": date,
                "type": "gold",
            })

    if not funds:
        raise ValueError("Scraper returned 0 funds — table structure may have changed")

    logger.info(f"Scraped {len(funds)} gold funds from EGX")
    return funds
