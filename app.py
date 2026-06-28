"""
Fake News Detection System

Flask web application using TF-IDF + Logistic Regression with optional
Gemini explanations, Google Fact Check lookup, and GNews headlines.
"""

import logging
import os

from flask import Flask, jsonify, render_template, request

from config import FLASK_DEBUG, FLASK_HOST, FLASK_PORT
from services.analysis import (
    analyze_sentiment,
    calculate_credibility,
    detect_clickbait,
    explain_prediction,
    get_model_comparison,
    predict_news,
)
from services.diagnostics import integration_warnings, log_startup_diagnostics, run_diagnostics
from services.fact_check_service import search_fact_checks
from services.gemini_service import generate_ai_explanation
from services.model_loader import ModelLoadError, load_model_artifacts
from services.news_service import fetch_live_news
from utils.logging_config import setup_logging

setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = Flask(__name__)

try:
    model, vectorizer, model_config = load_model_artifacts()
    OPTIMAL_THRESHOLD = float(model_config.get("optimal_threshold", 0.51))
except ModelLoadError as exc:
    logger.critical("%s", exc)
    raise SystemExit(str(exc)) from exc

log_startup_diagnostics()


@app.route("/", methods=["GET", "POST"])
def home():
    context = {
        "prediction": None,
        "confidence": None,
        "user_text": "",
        "error": None,
        "sentiment": None,
        "credibility": None,
        "clickbait": None,
        "explanation": None,
        "model_comparison": None,
        "ai_explanation": None,
        "ai_error": None,
        "fact_checks": [],
        "fact_check_error": None,
        "live_articles": [],
        "news_error": None,
        "integrations": _integration_status(),
        "integration_warnings": integration_warnings(),
    }

    live_articles, news_error = fetch_live_news()
    context["live_articles"] = live_articles
    context["news_error"] = news_error

    if request.method == "POST":
        user_text = request.form.get("news_text", "").strip()
        context["user_text"] = user_text

        if not user_text:
            context["error"] = "Please enter news text to analyze."
        elif len(user_text) < 10:
            context["error"] = "Please enter at least 10 characters."
        else:
            try:
                prediction, confidence, _ = predict_news(
                    user_text,
                    model,
                    vectorizer,
                    OPTIMAL_THRESHOLD,
                )
            except ValueError as exc:
                logger.warning("Prediction failed for user input: %s", exc)
                context["error"] = str(exc)
                return render_template("index.html", **context)

            if not prediction:
                context["error"] = (
                    "Unable to analyze this text. Please provide longer, readable content."
                )
            else:
                context["prediction"] = prediction
                context["confidence"] = confidence
                context["sentiment"] = analyze_sentiment(user_text)
                context["clickbait"] = detect_clickbait(user_text)
                context["credibility"] = calculate_credibility(
                    confidence,
                    len(user_text),
                    context["clickbait"]["risk"],
                )
                context["explanation"] = explain_prediction(
                    user_text, prediction, confidence
                )
                context["model_comparison"] = get_model_comparison(model_config)

                ai_explanation, ai_error = generate_ai_explanation(
                    user_text, prediction, confidence
                )

                if ai_explanation and not ai_error:
                    import re
                    verdict_match = re.search(r"VERDICT:\s*(Real News|Fake News|Real|Fake)", ai_explanation, re.IGNORECASE)
                    if verdict_match:
                        ai_verdict = "Real News" if "real" in verdict_match.group(1).lower() else "Fake News"
                        if ai_verdict != prediction:
                            logger.info("Gemini AI corrected prediction from %s to %s", prediction, ai_verdict)
                            prediction = ai_verdict
                            context["prediction"] = prediction
                            context["explanation"] = explain_prediction(
                                user_text, prediction, confidence
                            )
                            # Re-evaluate credibility score based on updated verdict
                            context["credibility"] = calculate_credibility(
                                confidence,
                                len(user_text),
                                context["clickbait"]["risk"],
                            )
                        
                        # Strip headers for a clean user-facing UI explanation
                        clean_exp = re.sub(r"^VERDICT:\s*(Real News|Fake News|Real|Fake)\s*", "", ai_explanation, flags=re.IGNORECASE).strip()
                        if clean_exp.upper().startswith("EXPLANATION:"):
                            clean_exp = clean_exp[12:].strip()
                        ai_explanation = clean_exp

                context["ai_explanation"] = ai_explanation
                context["ai_error"] = ai_error

                fact_checks, fact_check_error = search_fact_checks(user_text)
                context["fact_checks"] = fact_checks
                context["fact_check_error"] = fact_check_error

                logger.info(
                    "Analysis complete: prediction=%s confidence=%s",
                    prediction,
                    confidence,
                )

    return render_template("index.html", **context)


@app.route("/diagnostics")
def diagnostics_page():
    """HTML diagnostics dashboard for integration health."""
    report = run_diagnostics()
    return render_template("diagnostics.html", report=report)


@app.route("/diagnostics.json")
def diagnostics_json():
    """JSON diagnostics endpoint for scripts and monitoring."""
    return jsonify(run_diagnostics())


def _integration_status() -> dict[str, bool]:
    from config import FACT_CHECK_API_KEY, GEMINI_API_KEY, GNEWS_API_KEY

    return {
        "gnews": bool(GNEWS_API_KEY),
        "gemini": bool(GEMINI_API_KEY),
        "fact_check": bool(FACT_CHECK_API_KEY),
    }


if __name__ == "__main__":
    logger.info(
        "Starting Fake News Detection app on http://%s:%s (debug=%s)",
        FLASK_HOST,
        FLASK_PORT,
        FLASK_DEBUG,
    )
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
