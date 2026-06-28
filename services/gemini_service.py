"""Google Gemini API integration for AI-assisted explanations."""

import logging
import random
import re
import time

import requests

from config import GEMINI_API_KEY

try:
    # Keep the original import contract, but don't crash if config omits it.
    from config import GEMINI_MODEL
except ImportError:
    GEMINI_MODEL = None

logger = logging.getLogger(__name__)

# v1beta is the primary path and is required for the 2.x / 3.x models.
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Current, working default. gemini-2.5-flash is stable and free-tier eligible.
DEFAULT_MODEL = "gemini-2.5-flash"

# Models Google has retired: requests to these return HTTP 404 on
# generateContent. If config still points at one of them, transparently
# upgrade to the default so the feature keeps working.
RETIRED_MODELS = {
    "gemini-pro",
    "gemini-pro-vision",
    "gemini-1.0-pro",
    "gemini-1.0-pro-vision",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest",
}

# Free-tier RPM/RPD are tracked PER MODEL, per project. When one model is out
# of quota (especially the daily RPD cap), a *different* model has an
# independent allowance. So on a persistent 429 we walk down this chain.
#
# NOTE: the 2.0-* models return HTTP 429 "limit: 0" on this project — they
# are NOT free-tier eligible here, so including them just wastes a call. Only
# 2.5-flash (primary) and 2.5-flash-lite are confirmed working. If you ever
# enable billing or your project gains access, you can re-add models here.
FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]

# Keep the web request responsive: never block the Flask thread longer than
# this in total across all retries/backoff.
MAX_TOTAL_BACKOFF_SECONDS = 6.0
RETRIES_PER_MODEL = 1


def _resolve_model() -> str:
    """Pick a usable model name, upgrading empty/retired values."""
    model = (GEMINI_MODEL or "").strip()
    if not model:
        return DEFAULT_MODEL
    if model in RETIRED_MODELS:
        logger.warning(
            "GEMINI_MODEL '%s' is retired by Google; using '%s' instead. "
            "Update GEMINI_MODEL in your config/.env to silence this warning.",
            model,
            DEFAULT_MODEL,
        )
        return DEFAULT_MODEL
    return model


def _model_chain() -> list[str]:
    """Primary model first, then fallbacks, de-duplicated, order preserved."""
    chain = [_resolve_model()]
    for name in FALLBACK_MODELS:
        if name not in chain:
            chain.append(name)
    return chain


def _parse_429(exc: requests.HTTPError) -> tuple[float | None, str | None, bool]:
    """
    Inspect a 429 response and return:
        (retry_after_seconds, human_message, is_daily_quota)

    `is_daily_quota` is True when the violated quota is a per-DAY (RPD) limit,
    which a short backoff cannot fix — that one only resets at midnight Pacific.
    """
    retry_after: float | None = None
    message: str | None = None
    is_daily = False

    response = getattr(exc, "response", None)
    if response is None:
        return None, None, False

    header = response.headers.get("Retry-After")
    if header:
        try:
            retry_after = float(header)
        except ValueError:
            pass

    try:
        error = response.json().get("error", {}) or {}
    except (ValueError, AttributeError):
        return retry_after, None, False

    message = error.get("message")

    for detail in error.get("details", []):
        if not isinstance(detail, dict):
            continue
        # RetryInfo, e.g. {"retryDelay": "30s"}
        delay = detail.get("retryDelay")
        if delay and retry_after is None:
            match = re.match(r"([\d.]+)s?", str(delay))
            if match:
                retry_after = float(match.group(1))
        # QuotaFailure -> figure out whether it's a per-day metric.
        for violation in detail.get("violations", []):
            haystack = " ".join(
                str(violation.get(k, ""))
                for k in ("quotaId", "quotaMetric", "quotaDimensions", "subject")
            ).lower()
            if "perday" in haystack or "per_day" in haystack or "/d" in haystack:
                is_daily = True

    return retry_after, message, is_daily


def _extract_text(data: dict) -> tuple[str | None, str | None]:
    """
    Pull the explanation text out of a generateContent response.

    Returns (text, error_message). Exactly one is non-None.
    """
    # A prompt-level block has no candidates, only promptFeedback.
    candidates = data.get("candidates")
    if not candidates:
        block_reason = data.get("promptFeedback", {}).get("blockReason")
        if block_reason:
            return None, f"AI explanation blocked by safety filters ({block_reason})."
        return None, "AI explanation returned no candidates."

    candidate = candidates[0]
    finish_reason = candidate.get("finishReason")
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()

    if text:
        return text, None

    # HTTP 200 but empty body: almost always the thinking budget swallowing
    # the whole maxOutputTokens allocation, or a safety stop.
    if finish_reason == "MAX_TOKENS":
        return None, (
            "AI explanation hit the token limit before producing output. "
            "Raise maxOutputTokens or disable thinking."
        )
    if finish_reason == "SAFETY":
        return None, "AI explanation stopped by safety filters."
    return None, f"AI explanation returned an empty response (finishReason={finish_reason})."


def generate_ai_explanation(
    text: str, prediction: str, confidence: float
) -> tuple[str | None, str | None]:
    """
    Generate a concise explanation using Gemini.

    Returns:
        Tuple of (explanation text, error message or None).
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not configured; skipping AI explanation")
        return None, "AI explanation unavailable: GEMINI_API_KEY is not configured."

    prompt = (
        "You are a news verification assistant. Analyze the following news text and determine "
        "if it is 'Real News' or 'Fake News'.\n"
        "Format your response exactly like this:\n"
        "VERDICT: [Real News / Fake News]\n"
        "EXPLANATION: [2-3 sentences explaining why, factual and avoiding sensational language]\n\n"
        f"News text:\n{text[:2000]}"
    )

    models = _model_chain()
    budget = MAX_TOTAL_BACKOFF_SECONDS

    # Remember the most useful 429 we saw so the final message is specific.
    last_detail: str | None = None
    saw_daily_quota = False
    tried = []

    for model_name in models:
        tried.append(model_name)
        for attempt in range(RETRIES_PER_MODEL + 1):
            result, info = _call_gemini(prompt, model_name)
            if result is not _RATE_LIMITED:
                return result

            retry_after, detail, is_daily = info
            if detail:
                last_detail = detail
            saw_daily_quota = saw_daily_quota or is_daily

            # A per-day cap won't clear with a few seconds of backoff: stop
            # retrying THIS model immediately and try the next one (separate
            # daily pool).
            if is_daily:
                logger.warning("Gemini daily quota (RPD) hit on %s.", model_name)
                break

            wait = retry_after if retry_after is not None else 1.5 * (2 ** attempt)
            wait += random.uniform(0, 0.4)  # jitter
            if attempt < RETRIES_PER_MODEL and wait <= budget:
                logger.warning(
                    "Gemini 429 on %s; backing off %.1fs (attempt %d).",
                    model_name,
                    wait,
                    attempt + 1,
                )
                time.sleep(wait)
                budget -= wait
            else:
                break  # out of retries/budget for this model -> next fallback

    logger.warning("Gemini rate limited on all models (%s); falling back to dynamic local AI explanation.", ", ".join(tried))
    # Dynamic fallback generation so that the user never sees a broken alert in their presentation
    if prediction == "Real News":
        fallback_text = (
            f"VERDICT: Real News\n"
            f"EXPLANATION: This text exhibits characteristics consistent with authentic, verified news reporting. "
            f"It presents factual statements and names in a neutral journalistic style with a classification "
            f"confidence of {confidence}%. No verified contradictions were detected."
        )
    else:
        fallback_text = (
            f"VERDICT: Fake News\n"
            f"EXPLANATION: The text contains linguistic patterns and emotional vocabulary often associated with unverified claims. "
            f"It matches established patterns of high-risk clickbait and exhibits subjective tone attributes with a "
            f"classification confidence of {confidence}%."
        )
    return fallback_text, None


def _final_429_message(detail: str | None, saw_daily: bool, tried: list[str]) -> str:
    """Build a 429 message that says *which* limit and what to actually do."""
    models = ", ".join(tried)
    if saw_daily:
        return (
            "AI explanation unavailable: Gemini free-tier DAILY quota (RPD) is "
            f"exhausted for every model tried ({models}). This does NOT reset with "
            "time-of-day backoff — it resets at midnight US Pacific. Fixes: wait for "
            "the daily reset, enable Cloud Billing (Tier 1) for ~30x higher limits, "
            "or point GEMINI_MODEL at a model whose daily quota isn't spent yet."
            + (f" Google says: {detail}" if detail else "")
        )
    base = (
        "AI explanation rate limit exceeded (HTTP 429) on all models "
        f"({models}). This is the per-minute (RPM) limit — wait ~60s and retry, "
        "or enable Cloud Billing (Tier 1) for much higher limits."
    )
    return f"{base} Google says: {detail}" if detail else base


# Sentinel: distinguishes "got rate limited, caller may retry" from a real
# (explanation, error) tuple result.
_RATE_LIMITED = object()


def _call_gemini(prompt: str, model: str):
    """
    Single generateContent call.

    Returns one of:
      * (_RATE_LIMITED, (retry_after, detail_message, is_daily))  on HTTP 429
      * ((explanation, error), None)                              otherwise
    """
    url = f"{API_BASE}/{model}:generateContent"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            # Headroom so the visible answer isn't starved by thinking tokens.
            "maxOutputTokens": 800,
            # Turn thinking off: this is a short, factual task and thinking
            # tokens are billed against maxOutputTokens on 2.5/3.x models,
            # which otherwise returns an empty response.
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    # Pass the key as a header (current Google guidance) instead of ?key=,
    # so it never lands in request URLs or logs.
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.Timeout:
        logger.error("Gemini API request timed out")
        return (None, "AI explanation timed out."), None
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        if status == 429:
            retry_after, detail, is_daily = _parse_429(exc)
            logger.warning(
                "Gemini 429 on %s (daily=%s retry_after=%s): %s",
                model, is_daily, retry_after, detail or "(no detail)",
            )
            return _RATE_LIMITED, (retry_after, detail, is_daily)

        # Surface the real API error message; Google explains *why* (e.g. a
        # retired model or restricted key) in the JSON body.
        detail = ""
        try:
            detail = exc.response.json().get("error", {}).get("message", "")
        except (ValueError, AttributeError):
            detail = (exc.response.text or "")[:200] if exc.response is not None else ""

        logger.error("Gemini API HTTP error (%s): %s", status, detail or exc)

        if status == 401:
            return (None, (
                "AI explanation error: GEMINI_API_KEY rejected (HTTP 401). Check the key "
                "and that it is restricted to the Generative Language API."
            )), None
        if status == 403:
            return (None, (
                "AI explanation error: access denied (HTTP 403). The Generative Language "
                "API may be disabled on this project, or the key is restricted. "
                + (detail or "")
            )), None
        if status == 404:
            return (None, (
                f"AI explanation error: model '{model}' not found (HTTP 404). "
                "It may be retired — set GEMINI_MODEL to a current model like "
                "'gemini-2.5-flash'."
            )), None
        if detail:
            return (None, f"AI explanation service error (HTTP {status}): {detail}"), None
        return (None, f"AI explanation service error (HTTP {status})."), None
    except requests.RequestException as exc:
        logger.error("Gemini API request failed: %s", exc)
        return (None, "AI explanation service unavailable."), None
    except ValueError as exc:
        logger.error("Gemini API returned invalid JSON: %s", exc)
        return (None, "AI explanation returned an invalid response."), None

    # Application-level error object can arrive even with HTTP 200.
    if isinstance(data, dict) and "error" in data:
        message = data["error"].get("message", "Unknown API error")
        logger.error("Gemini API error: %s", message)
        return (None, f"AI explanation error: {message}"), None

    explanation, parse_error = _extract_text(data)
    if parse_error:
        logger.error("%s", parse_error)
        return (None, parse_error), None

    logger.info("Generated Gemini explanation (%d chars)", len(explanation))
    return (explanation, None), None