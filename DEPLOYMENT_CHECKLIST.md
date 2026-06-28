# Deployment Checklist — NewsVerify v2.1.1

Use this checklist before deploying to production or submitting the project.

## 1. Environment Setup

- [ ] Copy `.env.example` to `.env` in the project root
- [ ] Set `GNEWS_API_KEY` (from [gnews.io](https://gnews.io/))
- [ ] Set `GEMINI_API_KEY` (from [Google AI Studio](https://aistudio.google.com/apikey)) — must be a valid Gemini API key (typically starts with `AIza`)
- [ ] Set `FACT_CHECK_API_KEY` (Google Cloud API key with Fact Check Tools API enabled)
- [ ] Set `FLASK_DEBUG=false` in production
- [ ] Confirm `.env` is listed in `.gitignore` and **never committed**
- [ ] Remove any API keys from `.env.example` (placeholders only)

## 2. Verify .env Loading

```bash
python -c "from config import env_file_loaded, GNEWS_API_KEY; print('env:', env_file_loaded(), 'gnews:', bool(GNEWS_API_KEY))"
```

Expected: `env: True gnews: True` (when `.env` exists and key is set)

Startup log should show:

```
Loaded environment from .env
Integration gnews      | status=configured | GNEWS_API_KEY is set (0bca...d6ba)
Integration gemini     | status=configured | GEMINI_API_KEY is set (...)
Integration fact_check | status=configured | FACT_CHECK_API_KEY is set (...)
Integration summary: 3/3 configured (visit /diagnostics for live API checks)
```

## 3. Model Artifacts

- [ ] Run `python train_model.py` if `model.pkl` / `vectorizer.pkl` are missing
- [ ] Confirm `model_config.json` exists
- [ ] Optional: review `model_analysis.png` for training metrics

## 4. Dependencies

```bash
pip install -r requirements.txt
python -m textblob.download_corpora
```

## 5. Live API Verification

```bash
python scripts/test_api_integrations.py
```

Or open in browser:

- [ ] `http://127.0.0.1:5000/diagnostics` — HTML dashboard
- [ ] `http://127.0.0.1:5000/diagnostics.json` — JSON for monitoring

| Integration | Expected status |
|-------------|-----------------|
| GNews.io | `ok` — fetches headlines |
| Gemini | `ok` — returns AI explanation |
| Fact Check | `ok` — returns claim search results |

## 6. Automated Tests

```bash
python -m pytest tests/ -v
```

Expected: **24 passed**, 0 failed

## 7. Manual UI Smoke Test

- [ ] Open `/` — home page loads with integration badges
- [ ] If keys missing — **Integration Warnings** banner appears at top
- [ ] Submit news text (10+ chars) — **Analysis Results** dashboard appears
- [ ] Expand **AI Explanation (Gemini)** — Gemini response or warning
- [ ] Expand **Related Fact Checks** — fact-check cards or warning
- [ ] Scroll to **Latest Headlines** — GNews article cards or feed warning
- [ ] Open **Diagnostics** link in navbar — live status page loads

## 8. Security

- [ ] No API keys in source code
- [ ] `FLASK_DEBUG=false` in production
- [ ] Rotate any keys that were previously hardcoded or committed
- [ ] Use HTTPS reverse proxy (nginx/Caddy) in production

## 9. Production Run

```bash
python app.py
# Or with gunicorn (recommended):
# pip install gunicorn
# gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

## 10. Post-Deploy Monitoring

- [ ] Check startup logs for integration status
- [ ] Poll `/diagnostics.json` periodically
- [ ] Monitor for HTTP 429 (Gemini rate limits) in logs

---

**Sign-off**

| Check | Status | Date |
|-------|--------|------|
| .env configured | | |
| All tests pass | | |
| Live API checks | | |
| UI smoke test | | |
| Security review | | |
