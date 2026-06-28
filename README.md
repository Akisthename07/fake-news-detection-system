# NewsVerify — Fake News Detection System

AI-assisted fake news detection using TF-IDF + Logistic Regression, with optional Gemini explanations, Google Fact Check lookup, and GNews headlines.

## Features

- **ML classification** — TF-IDF vectorization with Logistic Regression (~99.4% test accuracy)
- **Sentiment analysis** — TextBlob polarity scoring
- **Clickbait detection** — Regex-based sensational language patterns
- **Credibility scoring** — Heuristic score from confidence, length, and clickbait risk
- **Gemini AI explanations** — Optional natural-language reasoning (requires API key)
- **Google Fact Check** — Optional related claim reviews (requires API key)
- **Live headlines** — GNews.io feed (requires API key)
- **Dark mode** — Persistent theme toggle

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
python -m textblob.download_corpora
```

### 2. Train the model (first run only)

```bash
python train_model.py
```

This creates `model.pkl`, `vectorizer.pkl`, `model_config.json`, and `model_analysis.png`.

### 3. Configure environment (optional)

Copy `.env.example` to `.env` and set API keys:

| Variable | Purpose |
|----------|---------|
| `GNEWS_API_KEY` | Live headline feed ([gnews.io](https://gnews.io/)) |
| `GEMINI_API_KEY` | AI explanations ([Google AI Studio](https://ai.google.dev/)) |
| `FACT_CHECK_API_KEY` | Fact-check search ([Fact Check Tools API](https://developers.google.com/fact-check/tools/api)) |

The app runs without API keys; external features degrade gracefully.

### 4. Run the application

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Run Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

```
├── app.py                  # Flask entry point
├── config.py               # Environment-based configuration
├── train_model.py          # Model training script
├── services/
│   ├── analysis.py         # ML prediction and heuristics
│   ├── fact_check_service.py
│   ├── gemini_service.py
│   ├── model_loader.py
│   └── news_service.py
├── utils/
│   ├── logging_config.py
│   └── text.py             # Shared preprocessing
├── templates/index.html
├── static/style.css
└── tests/
```

## Documentation

See [DOCUMENTATION.md](DOCUMENTATION.md) for the full architecture report and integration details.

## License

Educational / demonstration project.
