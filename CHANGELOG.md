# Changelog

All notable changes to the Fake News Detection System (NewsVerify).

## [2.1.0] — 2026-06-14

### Added

- **Modular architecture** — Split monolithic `app.py` into `config`, `services`, and `utils` packages without changing the Flask single-route design.
- **Environment-based configuration** — API keys and settings loaded from environment variables via `.env.example` template.
- **Structured logging** — Centralized logging with timestamps, levels, and module names (`utils/logging_config.py`).
- **Google Gemini integration** — Optional AI-assisted explanations via Gemini API (`services/gemini_service.py`).
- **Google Fact Check integration** — Optional claim search via Fact Check Tools API (`services/fact_check_service.py`).
- **Improved GNews integration** — HTTP status checks, timeout handling, error messages, and removed hardcoded API key.
- **Shared preprocessing** — Training and inference now use the same `preprocess_text()` function to fix train/serve skew.
- **Model configuration file** — `model_config.json` saved during training with threshold and accuracy metrics.
- **Test suite** — 17 pytest tests covering analysis, services, and Flask routes.
- **Documentation** — `README.md`, `DOCUMENTATION.md`, and this changelog.

### Changed

- **UI refresh** — Professional navbar with integration status badges, accessible collapsible sections, Inter font, and improved error/warning states.
- **Error handling** — Graceful degradation for missing model files, API failures, and invalid input with user-visible messages.
- **Dependencies** — Updated version constraints for Python 3.13 compatibility.
- **Model metrics** — Performance section now reads live values from `model_config.json` instead of hardcoded numbers.

### Fixed

- **Hardcoded API key removed** — GNews key no longer embedded in source code.
- **Silent API failures** — News, Gemini, and Fact Check errors are logged and surfaced in the UI.
- **Template crash** — Fixed `article.description[:80]` when description is `None`.
- **Bare except clause** — Sentiment analysis now catches specific exceptions with logging.
- **Duplicate validation** — Consolidated input validation flow in the route handler.

### Removed

- **Dead code** — Removed inline duplicate preprocessing from `train_model.py` (now shared).
- **Misleading naming** — Renamed internal `NEWS_API_KEY` to `GNEWS_API_KEY` to reflect the actual provider.

## [2.0.0] — Prior release

- Initial Flask application with TF-IDF + Logistic Regression.
- TextBlob sentiment, regex clickbait detection, and GNews headline widget.
- Hardcoded configuration and monolithic `app.py`.
