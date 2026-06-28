# NewsVerify — Fake News Detection System
## Technical Documentation & Review Report

**Version:** 2.1.0  
**Date:** June 14, 2026  
**Platform:** Python 3.13 / Flask 2.x  

---

## 1. Executive Summary

NewsVerify is a web-based fake news detection system that classifies news text as **Real** or **Fake** using a supervised machine learning pipeline (TF-IDF + Logistic Regression). The application supplements ML predictions with sentiment analysis, clickbait detection, credibility scoring, and optional external integrations for AI explanations (Gemini), fact-check lookup (Google Fact Check Tools API), and live headlines (GNews.io).

This document describes the system architecture, review findings, integration status, and improvements implemented in version 2.1.0.

---

## 2. System Architecture

### 2.1 High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Browser                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP GET/POST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Flask Application (app.py)                    │
│  Route: /  →  home()  →  render_template("index.html")        │
└─────┬───────────────┬────────────────┬──────────────────────────┘
      │               │                │
      ▼               ▼                ▼
┌───────────┐  ┌─────────────┐  ┌─────────────────────────────────┐
│  Analysis │  │  External   │  │  Model Artifacts                 │
│  Service  │  │  Services   │  │  model.pkl, vectorizer.pkl,      │
│           │  │             │  │  model_config.json               │
└───────────┘  └─────────────┘  └─────────────────────────────────┘
```

### 2.2 Component Breakdown

| Component | File(s) | Responsibility |
|-----------|---------|----------------|
| **Web layer** | `app.py`, `templates/index.html`, `static/style.css` | HTTP handling, UI rendering |
| **Configuration** | `config.py`, `.env.example` | Environment variables, paths |
| **ML inference** | `services/analysis.py`, `services/model_loader.py` | Prediction, heuristics |
| **Text preprocessing** | `utils/text.py` | Shared train/inference cleaning |
| **GNews feed** | `services/news_service.py` | Headline retrieval |
| **Gemini AI** | `services/gemini_service.py` | Natural-language explanations |
| **Fact Check** | `services/fact_check_service.py` | Related claim reviews |
| **Logging** | `utils/logging_config.py` | Structured application logs |
| **Training** | `train_model.py`, `Fake.csv`, `True.csv` | Offline model training |

### 2.3 Data Flow — Text Analysis

1. User submits news text via POST to `/`.
2. Input is validated (minimum 10 characters).
3. Text is preprocessed via `preprocess_text()` (lowercase, URL/HTML removal, normalization).
4. TF-IDF vectorizer transforms text into feature vector.
5. Logistic Regression outputs class probabilities.
6. Decision threshold (default 0.51) determines Real vs Fake label.
7. Parallel heuristics compute sentiment, clickbait risk, and credibility.
8. Optional API calls: Gemini explanation, Fact Check search.
9. Results rendered in dashboard UI.

### 2.4 Machine Learning Pipeline

| Stage | Details |
|-------|---------|
| **Dataset** | Fake.csv (23,481 samples) + True.csv (21,417 samples) |
| **Features** | TF-IDF, 5,000 max features, unigrams + bigrams, English stop words |
| **Models trained** | Multinomial Naive Bayes, Logistic Regression |
| **Production model** | Logistic Regression (higher accuracy) |
| **Split** | 80/20 stratified |
| **Threshold optimization** | Grid search 0.35–0.65 (step 0.02) |

**Current metrics** (from `model_config.json`):

| Metric | Value |
|--------|-------|
| Logistic Regression accuracy | 99.43% |
| Naive Bayes accuracy | 96.07% |
| Optimal threshold | 0.51 |
| Threshold-tuned accuracy | 99.44% |

---

## 3. External Integration Status

### 3.1 GNews.io (Headlines)

| Item | Status |
|------|--------|
| **Implementation** | `services/news_service.py` |
| **Endpoint** | `https://gnews.io/api/v4/top-headlines` |
| **Env variable** | `GNEWS_API_KEY` |
| **Behavior without key** | Feed disabled; user sees configuration message |
| **Error handling** | Timeouts, HTTP errors, invalid JSON, API error payloads |

**Note:** The prior version used a hardcoded API key and misleading variable name (`NEWS_API_KEY`). This was corrected. The provider is GNews.io, not NewsAPI.org.

### 3.2 Google Gemini (AI Explanations)

| Item | Status |
|------|--------|
| **Implementation** | `services/gemini_service.py` |
| **Endpoint** | `generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` |
| **Env variables** | `GEMINI_API_KEY`, `GEMINI_MODEL` (default: `gemini-2.0-flash`) |
| **Trigger** | Runs after successful prediction when key is configured |
| **Behavior without key** | Section hidden or shows setup instructions |

**Prior status:** Not implemented. Added in v2.1.0.

### 3.3 Google Fact Check Tools API

| Item | Status |
|------|--------|
| **Implementation** | `services/fact_check_service.py` |
| **Endpoint** | `factchecktools.googleapis.com/v1alpha1/claims:search` |
| **Env variables** | `FACT_CHECK_API_KEY`, `FACT_CHECK_MAX_RESULTS` |
| **Trigger** | Runs after successful prediction when key is configured |
| **Behavior without key** | Skipped silently (no error shown) |

**Prior status:** Not implemented. Added in v2.1.0.

---

## 4. Review Findings

### 4.1 Bugs & Weaknesses (Identified)

| Issue | Severity | Resolution |
|-------|----------|------------|
| Hardcoded GNews API key in source | High (security) | Moved to `GNEWS_API_KEY` env var |
| Train/serve preprocessing mismatch | High (accuracy) | Shared `utils/text.py` preprocessing |
| Model load crash on missing files | Medium | Clear error message via `ModelLoadError` |
| Silent API failures | Medium | Logging + UI error messages |
| `description[:80]` on None | Medium | Safe template slicing |
| Bare `except:` in sentiment | Low | Specific exception handling + logging |
| Hardcoded model metrics in UI | Low | Loaded from `model_config.json` |
| No Gemini / Fact Check integration | Medium | Implemented with graceful fallback |
| No logging | Medium | Centralized logging added |
| No tests | Medium | 17 pytest tests added |

### 4.2 Residual Limitations

- **Rule-based explainability** — The "Why This Prediction?" section uses template strings, not SHAP/LIME feature attribution. Gemini provides richer explanations when configured.
- **Credibility score** — Heuristic composite, not grounded in external source reputation databases.
- **Clickbait detection** — Regex patterns only; may produce false positives on legitimate breaking news.
- **Single route** — No REST API for programmatic access.
- **English only** — Training data and vectorizer are English-centric.

---

## 5. Error Handling & Logging

### 5.1 Logging Format

```
2026-06-14 12:00:00 | INFO     | services.analysis | Prediction=Real News confidence=92.50
```

Configure via `LOG_LEVEL` environment variable (default: `INFO`).

### 5.2 Error Handling Strategy

| Layer | Approach |
|-------|----------|
| **Startup** | Exit with message if model artifacts missing |
| **Prediction** | ValueError caught; user sees friendly message |
| **External APIs** | Try/except per service; empty results + error string |
| **Template** | Null-safe field access for optional data |

---

## 6. User Interface

### 6.1 Design Improvements (v2.1.0)

- Inter font via Google Fonts
- Brand mark and integration status badges in navbar
- Accessible collapsible sections (`aria-expanded`, `hidden` attribute)
- Warning/error alert styles for API failures
- Fact Check and Gemini result sections
- Live feed status indicator (Live / Feed unavailable)
- Removed decorative emoji overload for professional appearance

### 6.2 Dashboard Sections

1. Analysis Results (prediction, confidence, credibility, clickbait)
2. Why This Prediction? (rule-based explanation)
3. AI Explanation — Gemini (optional)
4. Related Fact Checks (optional)
5. Source Credibility breakdown
6. Clickbait Detection details
7. Sentiment Analysis bars
8. Model Performance metrics
9. Latest Headlines feed

---

## 7. Testing

### 7.1 Test Coverage

| Area | Tests |
|------|-------|
| Text preprocessing | 2 |
| ML prediction | 2 |
| Clickbait detection | 2 |
| Credibility scoring | 2 |
| Explanation generation | 1 |
| Sentiment analysis | 1 |
| GNews service | 2 |
| Fact Check service | 1 |
| Gemini service | 1 |
| Flask routes | 3 |

**Total: 17 tests — all passing**

### 7.2 Run Command

```bash
python -m pytest tests/ -v
```

---

## 8. Deployment Checklist

1. Install dependencies: `pip install -r requirements.txt`
2. Download TextBlob corpora: `python -m textblob.download_corpora`
3. Train model: `python train_model.py`
4. Copy `.env.example` → `.env` and set API keys
5. Run: `python app.py`
6. Set `FLASK_DEBUG=false` in production

### Required Files

| File | Generated by |
|------|--------------|
| `model.pkl` | `train_model.py` |
| `vectorizer.pkl` | `train_model.py` |
| `model_config.json` | `train_model.py` |

---

## 9. Security Considerations

- API keys must be stored in environment variables, never committed to source control.
- The prior hardcoded GNews key should be rotated if it was ever exposed publicly.
- Flask debug mode should be disabled in production (`FLASK_DEBUG=false`).
- External API responses are not cached; consider rate limiting for production deployments.

---

## 10. Conclusion

Version 2.1.0 preserves the original Flask + TF-IDF + Logistic Regression architecture while addressing critical gaps in security, reliability, integration completeness, and maintainability. External services (Gemini, Fact Check, GNews) are now properly integrated with environment-based configuration and graceful degradation. The codebase is modularized, tested, and documented for deployment and further development.

---

*Generated as part of the NewsVerify v2.1.0 review and improvement cycle.*
