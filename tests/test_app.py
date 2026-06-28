"""Unit tests for Fake News Detection application."""

import json
import pickle
from unittest.mock import MagicMock, patch

import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from services.analysis import (
    analyze_sentiment,
    calculate_credibility,
    detect_clickbait,
    explain_prediction,
    predict_news,
)
from utils.text import preprocess_text


@pytest.fixture
def trained_model():
    texts = [
        "government announces new policy for healthcare reform nationwide",
        "breaking shocking secret doctors dont want you to know about miracle cure",
        "parliament passes budget with bipartisan support after lengthy debate",
        "exclusive leaked viral trending you wont believe this unbelievable claim",
    ]
    labels = [1, 0, 1, 0]

    vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
    X = vectorizer.fit_transform(texts)

    model = LogisticRegression(max_iter=1000)
    model.fit(X, labels)

    return model, vectorizer


class TestPreprocessText:
    def test_lowercases_and_strips_urls(self):
        text = "BREAKING NEWS https://example.com Story HERE"
        result = preprocess_text(text)
        assert "https" not in result
        assert result.islower()

    def test_empty_input(self):
        assert preprocess_text("") == ""
        assert preprocess_text(None) == ""


class TestPredictNews:
    def test_returns_none_for_short_text(self, trained_model):
        model, vectorizer = trained_model
        label, confidence, prob = predict_news("short", model, vectorizer, 0.5)
        assert label is None
        assert confidence is None
        assert prob is None

    def test_predicts_with_valid_text(self, trained_model):
        model, vectorizer = trained_model
        text = "government announces new policy for healthcare reform nationwide"
        label, confidence, prob = predict_news(text, model, vectorizer, 0.5)
        assert label in {"Real News", "Fake News"}
        assert confidence is not None
        assert 0 <= prob <= 1


class TestClickbaitDetection:
    def test_detects_high_risk(self):
        text = "shocking breaking exclusive viral trending unbelievable"
        result = detect_clickbait(text)
        assert result["risk"] == "High"
        assert result["count"] >= 3

    def test_low_risk_for_neutral_text(self):
        result = detect_clickbait("The committee reviewed quarterly financial results.")
        assert result["risk"] == "Low"
        assert result["count"] == 0


class TestCredibility:
    def test_high_credibility_for_long_confident_text(self):
        result = calculate_credibility(90, 600, "Low")
        assert result["level"] == "High"
        assert result["score"] >= 75

    def test_clickbait_reduces_score(self):
        base = calculate_credibility(80, 200, "Low")
        reduced = calculate_credibility(80, 200, "High")
        assert reduced["score"] < base["score"]


class TestExplainPrediction:
    def test_returns_expected_keys(self):
        result = explain_prediction(
            "Sample news article about policy changes in the capital.",
            "Real News",
            88.5,
        )
        assert "reason" in result
        assert "keywords" in result
        assert result["confidence_level"] == "Very High"


class TestSentiment:
    def test_returns_sentiment_structure(self):
        result = analyze_sentiment("This is a positive and wonderful announcement.")
        assert result["sentiment"] in {"Positive", "Negative", "Neutral"}
        for key in ("positive", "negative", "neutral"):
            assert 0 <= result[key] <= 100


class TestNewsService:
    @patch("services.news_service.requests.get")
    def test_fetch_live_news_success(self, mock_get):
        from services.news_service import fetch_live_news

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "articles": [
                {
                    "title": "Test headline",
                    "description": "Test description",
                    "source": {"name": "Test Source"},
                    "url": "https://example.com",
                }
            ]
        }
        mock_get.return_value = mock_response

        with patch("services.news_service.GNEWS_API_KEY", "test-key"):
            articles, error = fetch_live_news()

        assert error is None
        assert len(articles) == 1
        assert articles[0]["title"] == "Test headline"

    @patch("services.news_service.requests.get")
    def test_fetch_live_news_handles_timeout(self, mock_get):
        import requests
        from services.news_service import fetch_live_news

        mock_get.side_effect = requests.Timeout()

        with patch("services.news_service.GNEWS_API_KEY", "test-key"):
            articles, error = fetch_live_news()

        assert len(articles) > 0
        assert error is None


class TestFactCheckService:
    @patch("services.fact_check_service.requests.get")
    def test_search_fact_checks_parses_results(self, mock_get):
        from services.fact_check_service import search_fact_checks

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "claims": [
                {
                    "text": "Sample claim text",
                    "claimant": "Social media",
                    "claimReview": [
                        {
                            "publisher": {"name": "FactChecker"},
                            "textualRating": "False",
                            "url": "https://example.com/review",
                            "title": "Review title",
                        }
                    ],
                }
            ]
        }
        mock_get.return_value = mock_response

        with patch("services.fact_check_service.FACT_CHECK_API_KEY", "test-key"):
            results, error = search_fact_checks("Sample claim about election results")

        assert error is None
        assert len(results) == 1
        assert results[0]["rating"] == "False"

    def test_missing_key_returns_warning(self):
        from services.fact_check_service import search_fact_checks

        with patch("services.fact_check_service.FACT_CHECK_API_KEY", ""):
            results, error = search_fact_checks("Sample claim about election results")

        assert results == []
        assert "FACT_CHECK_API_KEY" in error


class TestGeminiService:
    @patch("services.gemini_service.requests.post")
    def test_generate_ai_explanation_success(self, mock_post):
        from services.gemini_service import generate_ai_explanation

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "This looks like real news."}]}}]
        }
        mock_post.return_value = mock_response

        with patch("services.gemini_service.GEMINI_API_KEY", "test-key"):
            explanation, error = generate_ai_explanation(
                "Government announces new policy.", "Real News", 91.2
            )

        assert error is None
        assert "real news" in explanation.lower()

    def test_missing_key_returns_warning(self):
        from services.gemini_service import generate_ai_explanation

        with patch("services.gemini_service.GEMINI_API_KEY", ""):
            explanation, error = generate_ai_explanation(
                "Government announces new policy.", "Real News", 91.2
            )

        assert explanation is None
        assert "GEMINI_API_KEY" in error


class TestFlaskApp:
    @pytest.fixture
    def client(self, tmp_path, monkeypatch):
        model_path = tmp_path / "model.pkl"
        vectorizer_path = tmp_path / "vectorizer.pkl"
        config_path = tmp_path / "model_config.json"

        texts = [
            "government announces healthcare reform policy nationwide",
            "shocking viral exclusive leaked secret unbelievable cure",
        ]
        labels = [1, 0]
        vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
        X = vectorizer.fit_transform(texts)
        model = LogisticRegression(max_iter=1000)
        model.fit(X, labels)

        with model_path.open("wb") as file:
            pickle.dump(model, file)
        with vectorizer_path.open("wb") as file:
            pickle.dump(vectorizer, file)
        config_path.write_text(
            json.dumps({"optimal_threshold": 0.5, "logistic_regression_accuracy": 99.0}),
            encoding="utf-8",
        )

        monkeypatch.setattr("config.MODEL_PATH", model_path)
        monkeypatch.setattr("config.VECTORIZER_PATH", vectorizer_path)
        monkeypatch.setattr("config.MODEL_CONFIG_PATH", config_path)

        import importlib
        import app as app_module

        importlib.reload(app_module)
        app_module.app.config["TESTING"] = True
        return app_module.app.test_client()

    def test_home_get_renders(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"NewsVerify" in response.data

    def test_home_post_with_short_text_shows_error(self, client):
        response = client.post("/", data={"news_text": "short"})
        assert response.status_code == 200
        assert b"at least 10 characters" in response.data

    def test_home_post_with_valid_text_shows_results(self, client):
        response = client.post(
            "/",
            data={
                "news_text": (
                    "The government announced a new healthcare reform policy "
                    "after extensive parliamentary debate."
                )
            },
        )
        assert response.status_code == 200
        assert b"Analysis Results" in response.data

    def test_diagnostics_page_renders(self, client):
        response = client.get("/diagnostics")
        assert response.status_code == 200
        assert b"Integration Diagnostics" in response.data

    def test_diagnostics_json_renders(self, client):
        with patch("services.diagnostics.fetch_live_news", return_value=([], None)):
            with patch(
                "services.diagnostics.generate_ai_explanation",
                return_value=(None, None),
            ):
                response = client.get("/diagnostics.json")
        assert response.status_code == 200
        data = response.get_json()
        assert "integrations" in data
        assert "gnews" in data["integrations"]
