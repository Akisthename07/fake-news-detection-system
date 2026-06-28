"""GNews.io headline feed integration."""

import logging
import time
from typing import Any

import requests

from config import (
    GNEWS_API_KEY,
    GNEWS_COUNTRY,
    GNEWS_LANG,
    GNEWS_MAX_ARTICLES,
)

logger = logging.getLogger(__name__)

GNEWS_URL = "https://gnews.io/api/v4/top-headlines"


def fetch_live_news() -> tuple[list[dict[str, str]], str | None]:
    """
    Fetch latest headlines from GNews.io. Falls back to static articles if API fails/quota exhausted.
    """
    if not GNEWS_API_KEY:
        logger.warning("GNEWS_API_KEY not configured; using static headlines.")
        return _get_fallback_headlines(), None

    params = {
        "lang": GNEWS_LANG,
        "country": GNEWS_COUNTRY,
        "max": GNEWS_MAX_ARTICLES,
        "apikey": GNEWS_API_KEY,
        "t": int(time.time()),
    }

    try:
        response = requests.get(GNEWS_URL, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            message = _format_gnews_errors(data["errors"])
            logger.warning("GNews API returned errors (%s); falling back to cached headlines.", message)
            return _get_fallback_headlines(), None

        articles: list[dict[str, str]] = []
        for article in data.get("articles", []):
            description = article.get("description") or ""
            articles.append({
                "title": article.get("title") or "Untitled",
                "description": description,
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url") or "#",
            })
        
        if articles:
            return articles[:6], None
            
    except Exception as exc:
        logger.warning("GNews request failed (%s); falling back to cached headlines.", exc)

    return _get_fallback_headlines(), None


def _get_fallback_headlines() -> list[dict[str, str]]:
    return [
        {
            "title": "ISRO Begins Preparations for Next-Gen Reusable Launch Vehicle Landing Test",
            "description": "The Indian Space Research Organisation has successfully initiated hover and landing test runs for its reusable launch vehicle in Karnataka.",
            "source": "ISRO Press",
            "url": "https://www.isro.gov.in"
        },
        {
            "title": "Reserve Bank of India Issues Guidelines for Cross-Border UPI Merchant Transactions",
            "description": "The central bank has laid down frameworks for financial institutions to facilitate secure mobile merchant payments using UPI abroad.",
            "source": "Reserve Bank of India",
            "url": "https://www.rbi.org.in"
        },
        {
            "title": "Ministry of Electronics Launches Semiconductor Design Support Scheme for Startups",
            "description": "A new funding window has been opened to support domestic startups designing advanced computing chips for automotive systems.",
            "source": "Ministry of IT",
            "url": "https://www.meity.gov.in"
        },
        {
            "title": "National Games 2026: Youth Sports Development Schemes Inaugurated in New Delhi",
            "description": "The sports ministry has announced new financial scholarships and training academies for top-tier junior athletes.",
            "source": "Sports Authority of India",
            "url": "https://sportsauthorityofindia.nic.in"
        },
        {
            "title": "Indian Meteorological Department Forecasts Normal Monsoons Across the Peninsula",
            "description": "Seasonal rainfall patterns are expected to remain consistent with historical averages, supporting agricultural yields.",
            "source": "IMD Weather",
            "url": "https://mausam.imd.gov.in"
        },
        {
            "title": "BCCI Announces Complete Schedule for Domestic Tournaments and Talent Scouting",
            "description": "The Board of Control for Cricket in India has released detailed dates and venues for upcoming inter-state tournaments and junior trials.",
            "source": "BCCI News",
            "url": "https://www.bcci.tv"
        }
    ]


def _format_gnews_errors(errors: Any) -> str:
    if isinstance(errors, list):
        return "; ".join(str(item) for item in errors)
    return str(errors)
