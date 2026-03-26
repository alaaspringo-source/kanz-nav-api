from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

import cache
from scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Holds scheduler reference so it isn't garbage collected
_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    logger.info("Kanz NAV API starting up...")
    _scheduler = start_scheduler()
    yield
    logger.info("Kanz NAV API shutting down...")
    if _scheduler:
        _scheduler.shutdown()


app = FastAPI(
    title="Kanz NAV API",
    description="Middleware that scrapes Egyptian mutual fund NAVs from EGX for the Kanz app",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your Flutter app domain in production
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Basic health check — confirms the API is alive."""
    return {"status": "ok"}


@app.get("/nav")
def get_all_navs():
    """
    Returns all currently cached mutual fund NAVs.
    This is the primary endpoint Kanz calls.
    """
    data = cache.get_cache()

    if cache.is_empty():
        raise HTTPException(
            status_code=503,
            detail="NAV data not yet available — scraper may still be running or failed",
        )

    return {
        "funds": data["funds"],
        "last_scraped": data["last_scraped"],
        "error": data["error"],
        "count": len(data["funds"]),
    }


@app.get("/nav/{fund_name}")
def get_fund_nav(fund_name: str):
    """
    Returns NAV for a specific fund by name (case-insensitive partial match).
    Example: /nav/AZ%20Gold  or  /nav/azimut
    """
    data = cache.get_cache()

    if cache.is_empty():
        raise HTTPException(status_code=503, detail="NAV data not yet available")

    query = fund_name.lower()
    matches = [f for f in data["funds"] if query in f["name"].lower()]

    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"No fund found matching '{fund_name}'. Use /nav to see all available funds.",
        )

    return {
        "matches": matches,
        "last_scraped": data["last_scraped"],
        "query": fund_name,
    }


@app.post("/nav/refresh")
def force_refresh():
    """
    Manually triggers a scrape. 
    Useful during development or if you need to force an update.
    Protect this endpoint with a secret key in production.
    """
    from scheduler import run_scrape_job
    run_scrape_job()
    data = cache.get_cache()
    return {
        "message": "Scrape triggered",
        "funds_cached": len(data["funds"]),
        "last_scraped": data["last_scraped"],
        "error": data["error"],
    }
