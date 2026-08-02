import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


def dump(name, url, marker):
    print(f"\n{'='*60}\n{name}\n{'='*60}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
        idx = resp.text.find(marker)
        if idx == -1:
            print(f"Marker '{marker}' not found. First 2000 chars:")
            print(resp.text[:2000])
        else:
            print(f"Found marker at {idx}. Raw HTML around it:\n")
            print(resp.text[max(0, idx-800):idx+1500])
    except Exception as e:
        print(f"FAILED: {e}")


dump("HC Securities", "https://www.hc-si.com/", "Suez Canal Bank Fund No. 1")
dump("Misr Capital", "https://misrcapital.com/financial-services/asset-management/", "Banque Misr Second Fund")
