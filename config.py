"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load .env from project root (does not override existing shell env vars)
_env_path = BASE_DIR / ".env"
load_dotenv(_env_path, override=False)

# Model artifacts
MODEL_PATH = BASE_DIR / "model.pkl"
VECTORIZER_PATH = BASE_DIR / "vectorizer.pkl"
MODEL_CONFIG_PATH = BASE_DIR / "model_config.json"

# Flask
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# GNews.io (headlines feed)
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "").strip()
GNEWS_COUNTRY = os.getenv("GNEWS_COUNTRY", "in")
GNEWS_LANG = os.getenv("GNEWS_LANG", "en")
GNEWS_MAX_ARTICLES = int(os.getenv("GNEWS_MAX_ARTICLES", "5"))

# Google Fact Check Tools API
FACT_CHECK_API_KEY = os.getenv("FACT_CHECK_API_KEY", "").strip()
FACT_CHECK_MAX_RESULTS = int(os.getenv("FACT_CHECK_MAX_RESULTS", "5"))

# Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Prediction defaults (overridden by model_config.json when present)
DEFAULT_OPTIMAL_THRESHOLD = 0.51


def env_file_loaded() -> bool:
    """Return True if a .env file exists in the project root."""
    return _env_path.is_file()


def mask_secret(value: str) -> str:
    """Return a masked representation of a secret for logs/UI."""
    if not value:
        return "(not set)"
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"
