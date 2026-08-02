from scrapers._render import fetch_rendered_html
from bs4 import BeautifulSoup

html = fetch_rendered_html(
    "https://www.beltoneholding.com/en/business-line/asset-management-1",
    wait_selector="table",
)
if not html:
    print("Fetch failed entirely.")
else:
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    print(f"Found {len(tables)} <table> tag(s).\n")
    if tables:
        print("First table's raw HTML (first 3000 chars):\n")
        print(str(tables[0])[:3000])
    else:
        print("No <table> tags at all — dumping first 3000 chars of full body instead:")
        print(html[:3000])
