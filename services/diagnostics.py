"""Integration health checks and startup diagnostics."""

import logging
import time
from typing import Any

import requests

from config import (
    FACT_CHECK_API_KEY,
    FACT_CHECK_MAX_RESULTS,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GNEWS_API_KEY,
    GNEWS_COUNTRY,
    GNEWS_LANG,
    GNEWS_MAX_ARTICLES,
    env_file_loaded,
    mask_secret,
)
from services.fact_check_service import FACT_CHECK_URL
from services.gemini_service import generate_ai_explanation
from services.news_service import GNEWS_URL, fetch_live_news

logger = logging.getLogger(__name__)

SAMPLE_NEWS_TEXT = (
    "The government announced a new healthcare reform policy after "
    "extensive parliamentary debate and public consultation."
)
SAMPLE_FACT_CHECK_QUERY = "COVID-19 vaccine safety"


def check_gnews() -> dict[str, Any]:
    """Verify GNews.io configuration and connectivity."""
    result = {
        "service": "GNews.io",
        "env_var": "GNEWS_API_KEY",
        "configured": bool(GNEWS_API_KEY),
        "key_preview": mask_secret(GNEWS_API_KEY),
        "endpoint": GNEWS_URL,
        "status": "disabled",
        "message": "GNEWS_API_KEY is not configured.",
        "sample_request": {
            "method": "GET",
            "url": GNEWS_URL,
            "params": {
                "lang": GNEWS_LANG,
                "country": GNEWS_COUNTRY,
                "max": GNEWS_MAX_ARTICLES,
                "apikey": "<GNEWS_API_KEY>",
            },
        },
    }

    if not GNEWS_API_KEY:
        return result

    articles, error = fetch_live_news()
    if error:
        result["status"] = "error"
        result["message"] = error
    else:
        result["status"] = "ok"
        result["message"] = f"Connected — fetched {len(articles)} headline(s)."
        result["sample_response"] = articles[:2]

    return result


def check_gemini() -> dict[str, Any]:
    """Verify Gemini API configuration and connectivity."""
    result = {
        "service": "Google Gemini",
        "env_var": "GEMINI_API_KEY",
        "configured": bool(GEMINI_API_KEY),
        "key_preview": mask_secret(GEMINI_API_KEY),
        "model": GEMINI_MODEL,
        "endpoint": (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{GEMINI_MODEL}:generateContent"
        ),
        "status": "disabled",
        "message": "GEMINI_API_KEY is not configured.",
        "sample_request": {
            "method": "POST",
            "url": (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{GEMINI_MODEL}:generateContent?key=<GEMINI_API_KEY>"
            ),
            "body": {
                "contents": [{"parts": [{"text": "Summarize this news in one sentence."}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 64},
            },
        },
    }

    if not GEMINI_API_KEY:
        return result

    explanation, error = generate_ai_explanation(
        SAMPLE_NEWS_TEXT,
        "Real News",
        90.0,
    )
    if error:
        result["status"] = "error"
        result["message"] = error
    else:
        result["status"] = "ok"
        result["message"] = "Connected — received AI explanation."
        result["sample_response"] = explanation[:200] if explanation else None

    return result


def check_fact_check() -> dict[str, Any]:
    """Verify Google Fact Check Tools API configuration and connectivity."""
    result = {
        "service": "Google Fact Check",
        "env_var": "FACT_CHECK_API_KEY",
        "configured": bool(FACT_CHECK_API_KEY),
        "key_preview": mask_secret(FACT_CHECK_API_KEY),
        "endpoint": FACT_CHECK_URL,
        "status": "disabled",
        "message": "FACT_CHECK_API_KEY is not configured.",
        "sample_request": {
            "method": "GET",
            "url": FACT_CHECK_URL,
            "params": {
                "query": SAMPLE_FACT_CHECK_QUERY,
                "key": "<FACT_CHECK_API_KEY>",
                "pageSize": FACT_CHECK_MAX_RESULTS,
                "languageCode": "en",
            },
        },
    }

    if not FACT_CHECK_API_KEY:
        return result

    params = {
        "query": SAMPLE_FACT_CHECK_QUERY,
        "key": FACT_CHECK_API_KEY,
        "pageSize": 1,
        "languageCode": "en",
    }

    try:
        response = requests.get(FACT_CHECK_URL, params=params, timeout=12)
        try:
            data = response.json()
        except ValueError:
            data = {}
        response.raise_for_status()
    except requests.RequestException as exc:
        result["status"] = "error"
        if isinstance(data, dict) and "error" in data:
            result["message"] = data["error"].get("message", str(exc))
        else:
            result["message"] = f"Request failed: {exc}"
        return result

    if isinstance(data, dict) and "error" in data:
        result["status"] = "error"
        result["message"] = data["error"].get("message", "Unknown API error")
        return result

    claim_count = len(data.get("claims", []))
    result["status"] = "ok"
    result["message"] = f"Connected — API returned {claim_count} claim(s) for sample query."
    return result


def run_diagnostics() -> dict[str, Any]:
    """Run all integration checks and return a summary."""
    checks = {
        "gnews": check_gnews(),
        "gemini": check_gemini(),
        "fact_check": check_fact_check(),
    }

    configured = sum(1 for check in checks.values() if check["configured"])
    healthy = sum(1 for check in checks.values() if check["status"] == "ok")

    from datetime import datetime, timezone, timedelta
    ist_now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=30)))
    return {
        "timestamp": ist_now.strftime("%Y-%m-%d %H:%M:%S IST"),
        "env_file_loaded": env_file_loaded(),
        "summary": {
            "configured": configured,
            "healthy": healthy,
            "total": len(checks),
        },
        "integrations": checks,
    }


def integration_warnings() -> list[str]:
    """Return user-facing warnings for missing configuration (no live API calls)."""
    warnings: list[str] = []

    # Only warn about missing .env if the API keys are not already loaded from the environment (production)
    if not env_file_loaded() and not (GNEWS_API_KEY and GEMINI_API_KEY and FACT_CHECK_API_KEY):
        warnings.append(
            "No .env file found. Copy .env.example to .env and set your API keys."
        )

    if not GNEWS_API_KEY:
        warnings.append("GNews.io is disabled: set GNEWS_API_KEY in .env")
    if not GEMINI_API_KEY:
        warnings.append("Gemini is disabled: set GEMINI_API_KEY in .env")
    if not FACT_CHECK_API_KEY:
        warnings.append("Fact Check is disabled: set FACT_CHECK_API_KEY in .env")

    return warnings


def log_startup_diagnostics() -> None:
    """Log integration configuration at application startup (no live API calls)."""
    if env_file_loaded():
        logger.info("Loaded environment from .env")
    else:
        logger.warning("No .env file found — using shell environment variables only")

    integrations = (
        ("gnews", "GNEWS_API_KEY", GNEWS_API_KEY),
        ("gemini", "GEMINI_API_KEY", GEMINI_API_KEY),
        ("fact_check", "FACT_CHECK_API_KEY", FACT_CHECK_API_KEY),
    )

    configured_count = 0
    for name, env_var, key in integrations:
        if key:
            configured_count += 1
            message = f"{env_var} is set ({mask_secret(key)})"
            status = "configured"
        else:
            message = f"{env_var} is not set — integration disabled"
            status = "disabled"

        logger.info("Integration %-10s | status=%-11s | %s", name, status, message)

    logger.info(
        "Integration summary: %d/3 configured (visit /diagnostics for live API checks)",
        configured_count,
    )
