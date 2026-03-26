from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from scraper import scrape_gold_funds
import cache

logger = logging.getLogger(__name__)


def run_scrape_job():
    """Scrapes EGX and updates cache. Called on schedule and on startup."""
    logger.info("Running NAV scrape job...")
    try:
        funds = scrape_gold_funds()
        cache.set_cache(funds)
    except Exception as e:
        error_msg = str(e)
        cache.set_error(error_msg)
        logger.error(f"Scrape job failed: {error_msg}")


def start_scheduler():
    """
    Starts the background scheduler.
    Runs once immediately on startup, then daily at 18:00 Cairo time (UTC+2 = 16:00 UTC).
    EGX closes at ~15:30 Cairo time, so 18:00 gives enough buffer for NAVs to be published.
    """
    scheduler = BackgroundScheduler(timezone="UTC")

    scheduler.add_job(
        run_scrape_job,
        trigger=CronTrigger(hour=16, minute=0),  # 18:00 Cairo (UTC+2)
        id="daily_nav_scrape",
        name="Daily EGX NAV Scrape",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started — daily scrape at 18:00 Cairo time")

    # Also run immediately on startup so cache is populated from first request
    run_scrape_job()

    return scheduler
