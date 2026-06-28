"""Core analysis functions for fake news detection."""

import logging
import re
from typing import Any

from utils.text import preprocess_text

logger = logging.getLogger(__name__)

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

CLICKBAIT_PATTERNS = {
    "shocking": r"\b(shocking|unbelievable|incredible)\b",
    "breaking": r"\b(breaking|urgent|news)\b",
    "exclusive": r"\b(exclusive|leaked|exposed|secret)\b",
    "sensational": r"\b(viral|trending|you won\'t believe|must see)\b",
}


def predict_news(
    text: str,
    model: object,
    vectorizer: object,
    optimal_threshold: float,
) -> tuple[str | None, float | None, float | None]:
    """Predict fake/real news with the configured threshold."""
    cleaned = preprocess_text(text)
    if not cleaned or len(cleaned) < 10:
        return None, None, None

    try:
        vector = vectorizer.transform([cleaned])
    except Exception as exc:
        logger.exception("Vectorization failed: %s", exc)
        raise ValueError("Unable to process the provided text.") from exc

    if not hasattr(model, "predict_proba"):
        logger.error("Loaded model does not support probability predictions")
        return None, None, None

    probabilities = model.predict_proba(vector)[0]
    real_probability = float(probabilities[1])

    label = "Real News" if real_probability >= optimal_threshold else "Fake News"
    confidence = round(max(probabilities) * 100, 2)

    logger.info(
        "Prediction=%s confidence=%.2f real_prob=%.4f",
        label,
        confidence,
        real_probability,
    )
    return label, confidence, real_probability


def analyze_sentiment(text: str) -> dict[str, Any]:
    """Analyze text sentiment using TextBlob."""
    if TextBlob is None:
        logger.warning("TextBlob not installed; returning neutral sentiment")
        return {"sentiment": "Neutral", "positive": 0, "negative": 0, "neutral": 100}

    try:
        polarity = TextBlob(text).sentiment.polarity

        if polarity > 0.1:
            sentiment = "Positive"
        elif polarity < -0.1:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        positive = max(0, min(100, round((polarity + 1) * 50)))
        negative = max(0, min(100, round((-polarity + 1) * 50)))
        neutral = 100 - max(positive, negative)

        return {
            "sentiment": sentiment,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
        }
    except Exception as exc:
        logger.warning("Sentiment analysis failed: %s", exc)
        return {"sentiment": "Neutral", "positive": 0, "negative": 0, "neutral": 100}


def detect_clickbait(text: str) -> dict[str, Any]:
    """Detect clickbait indicators via regex patterns."""
    detected_terms: list[str] = []
    text_lower = text.lower()

    for pattern in CLICKBAIT_PATTERNS.values():
        detected_terms.extend(re.findall(pattern, text_lower, re.IGNORECASE))

    detected_terms = list(set(detected_terms))[:5]
    count = len(detected_terms)

    if count >= 3:
        risk = "High"
    elif count > 0:
        risk = "Medium"
    else:
        risk = "Low"

    return {"risk": risk, "terms": detected_terms, "count": count}


def calculate_credibility(
    confidence: float | None,
    text_length: int,
    clickbait_risk: str,
) -> dict[str, Any]:
    """Calculate a heuristic credibility score."""
    base_score = confidence if confidence is not None else 50

    if text_length > 500:
        base_score = min(100, base_score + 15)
    elif text_length > 250:
        base_score = min(100, base_score + 10)
    elif text_length > 100:
        base_score = min(100, base_score + 5)

    if clickbait_risk == "High":
        base_score = max(0, base_score - 20)
    elif clickbait_risk == "Medium":
        base_score = max(0, base_score - 10)

    score = round(base_score)

    if score >= 75:
        level, color = "High", "#10b981"
    elif score >= 50:
        level, color = "Medium", "#f59e0b"
    else:
        level, color = "Low", "#ef4444"

    return {"score": score, "level": level, "color": color}


def explain_prediction(text: str, prediction: str, confidence: float) -> dict[str, Any]:
    """Generate a rule-based explanation for the prediction."""
    words = text.split()
    keywords = [w.lower() for w in words if 5 <= len(w) <= 20]
    keywords = list(set(keywords))[:5]

    confidence_level = (
        "Very High" if confidence > 85 else "High" if confidence > 70 else "Moderate"
    )

    if prediction == "Real News":
        if confidence > 80:
            reason = "Matches established news patterns with substantial detail."
        elif confidence > 65:
            reason = "Shows characteristics consistent with verified sources."
        else:
            reason = "Contains elements typical of real news articles."
    else:
        if confidence > 80:
            reason = "Exhibits patterns commonly found in misinformation."
        elif confidence > 65:
            reason = "Contains indicators associated with unreliable content."
        else:
            reason = "Shows some characteristics of unverified information."

    return {
        "reason": reason,
        "keywords": keywords,
        "confidence_level": confidence_level,
    }


def get_model_comparison(config: dict) -> dict[str, float]:
    """Return model accuracy metrics from saved configuration."""
    return {
        "logistic_regression": float(config.get("logistic_regression_accuracy", 99.4)),
        "naive_bayes": float(config.get("naive_bayes_accuracy", 96.1)),
        "selected_model": config.get("selected_model", "Logistic Regression"),
    }
