"""
Temporary diagnostic script — run this once via GitHub Actions to see exactly
why Azimut, CI Capital, Beltone, AFIM, and AAIM are failing. Prints raw
status codes and HTML snippets so we can fix the real cause instead of guessing.

Delete this file once the real scrapers are all fixed.
"""
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


def check(name, url, headers=None, verify=True):
    print(f"\n{'='*60}\n{name}: {url}\n{'='*60}")
    try:
        resp = requests.get(url, headers=headers or HEADERS, timeout=20, verify=verify)
        print(f"Status: {resp.status_code}")
        print(f"Length: {len(resp.text)} chars")
        print(f"First 1500 chars:\n{resp.text[:1500]}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")


# Azimut — SSL TLSV1_UNRECOGNIZED_NAME. Test with and without the Referer/Origin
# headers, and with SNI-sensitive settings, to isolate whether it's IP-blocking
# or a header/SNI mismatch.
check("Azimut (with finance headers)", "https://api.azimut.eg/api/list/funds", headers={
    **HEADERS,
    "Referer": "https://azimut.eg/",
    "Origin": "https://azimut.eg",
})
check("Azimut (plain, no Referer/Origin)", "https://api.azimut.eg/api/list/funds")

# CI Capital — SSL CERTIFICATE_VERIFY_FAILED. Test with verify=False to confirm
# it's purely a cert chain issue and not an IP block (NOT for production use,
# diagnostic only).
check("CI Capital (verify=True)", "https://www.cicapital.com/fundprice/")
check("CI Capital (verify=False, diagnostic only)", "https://www.cicapital.com/fundprice/", verify=False)

# Beltone, AFIM, AAIM — returned 0 funds. Need raw HTML to fix selectors.
check("Beltone", "https://www.beltoneholding.com/en/business-line/asset-management-1")
check("AFIM", "https://www.afim.com.eg/public/investment")
check("AAIM", "https://aaim.com.eg/en/what-we-offer/funds")
