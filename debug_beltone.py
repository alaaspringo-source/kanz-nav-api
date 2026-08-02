from scrapers._render import fetch_rendered_html
from bs4 import BeautifulSoup

html = fetch_rendered_html(
    "https://www.beltoneholding.com/en/business-line/asset-management-1",
    wait_ms=8000,
)
if not html:
    print("Fetch failed entirely.")
else:
    print(f"Total HTML length: {len(html)}")
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    print(f"Found {len(tables)} <table> tag(s).")

    # Look for a fund name we know should be on the page as an anchor point
    idx = html.find("MID Bank")
    if idx == -1:
        idx = html.find("Beltone Financial")
    if idx != -1:
        print(f"\nFound fund name near index {idx}. Context (2000 chars around it):\n")
        print(html[max(0, idx-500):idx+1500])
    else:
        print("\nCouldn't find any known fund name in the HTML at all.")
        print("First 3000 chars of body:\n")
        body = soup.find("body")
        print(str(body)[:3000] if body else html[:3000])
