"""Google Fact Check Tools API integration."""

import logging
from typing import Any

import requests

from config import FACT_CHECK_API_KEY, FACT_CHECK_MAX_RESULTS

logger = logging.getLogger(__name__)

FACT_CHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


def search_fact_checks(query: str) -> tuple[list[dict[str, str]], str | None]:
    """
    Search Google Fact Check Tools for related claim reviews.

    Returns:
        Tuple of (fact check results, error message or None).
    """
    if not FACT_CHECK_API_KEY:
        logger.warning("FACT_CHECK_API_KEY not configured; skipping fact check lookup")
        return [], "Fact check unavailable: FACT_CHECK_API_KEY is not configured."

    query = query.strip()
    if len(query) < 10:
        return [], None

    import re
    # Extract the first sentence and trim it to the first 10 words for optimal search index matches
    sentences = [s.strip() for s in re.split(r"[\.\!\?]", query) if s.strip()]
    first_sentence = sentences[0] if sentences else query
    words = first_sentence.split()
    search_term = " ".join(words[:10]) if len(words) > 10 else first_sentence

    params = {
        "query": search_term,
        "key": FACT_CHECK_API_KEY,
        "pageSize": FACT_CHECK_MAX_RESULTS,
        "languageCode": "en",
    }

    try:
        response = requests.get(FACT_CHECK_URL, params=params, timeout=12)
        try:
            data = response.json()
        except ValueError:
            data = {}
        response.raise_for_status()
    except requests.Timeout:
        logger.error("Fact Check API request timed out")
        return [], "Fact check lookup timed out."
    except requests.HTTPError as exc:
        if isinstance(data, dict) and "error" in data:
            message = data["error"].get("message", str(exc))
        else:
            message = str(exc)
        logger.error("Fact Check API HTTP error: %s", message)
        return [], f"Fact check error: {message}"
    except requests.RequestException as exc:
        logger.error("Fact Check API request failed: %s", exc)
        return [], "Fact check service unavailable."

    if isinstance(data, dict) and "error" in data:
        message = data["error"].get("message", "Unknown API error")
        logger.error("Fact Check API error: %s", message)
        return [], f"Fact check error: {message}"

    results: list[dict[str, str]] = []
    for claim in data.get("claims", []):
        review = _extract_primary_review(claim)
        if not review:
            continue

        publisher_info = review.get("publisher") or {}
        publisher_name = publisher_info.get("name", "Unknown") if isinstance(publisher_info, dict) else "Unknown"

        results.append(
            {
                "claim": claim.get("text", "Unknown claim"),
                "claimant": claim.get("claimant", "Unknown"),
                "publisher": publisher_name,
                "rating": review.get("textualRating", "Not rated"),
                "url": review.get("url", "#"),
                "title": review.get("title", "Fact check review"),
            }
        )

    logger.info("Found %d fact check results for query", len(results))
    return results, None


def _extract_primary_review(claim: dict[str, Any]) -> dict[str, Any] | None:
    reviews = claim.get("claimReview") or []
    if not reviews:
        return None
    return reviews[0]
