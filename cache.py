from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)

_lock = threading.Lock()

_cache = {
    "funds": [],
    "last_scraped": None,   # ISO string
    "error": None,          # Last scrape error if any
}


def get_cache() -> dict:
    with _lock:
        return dict(_cache)


def set_cache(funds: list[dict]) -> None:
    with _lock:
        _cache["funds"] = funds
        _cache["last_scraped"] = datetime.utcnow().isoformat()
        _cache["error"] = None
    logger.info(f"Cache updated with {len(funds)} funds at {_cache['last_scraped']}")


def set_error(error: str) -> None:
    with _lock:
        _cache["error"] = error
    logger.error(f"Cache error set: {error}")


def is_empty() -> bool:
    with _lock:
        return len(_cache["funds"]) == 0
