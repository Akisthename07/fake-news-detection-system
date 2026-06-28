"""Model artifact loading and configuration."""

import json
import logging
import pickle
from pathlib import Path

from config import (
    DEFAULT_OPTIMAL_THRESHOLD,
    MODEL_CONFIG_PATH,
    MODEL_PATH,
    VECTORIZER_PATH,
)

logger = logging.getLogger(__name__)


class ModelLoadError(Exception):
    """Raised when model artifacts cannot be loaded."""


def load_model_artifacts() -> tuple[object, object, dict]:
    """
    Load trained model, vectorizer, and configuration.

    Returns:
        Tuple of (model, vectorizer, config dict).
    """
    model = _load_pickle(MODEL_PATH, "model")
    vectorizer = _load_pickle(VECTORIZER_PATH, "vectorizer")
    config = _load_model_config()
    return model, vectorizer, config


def _load_pickle(path: Path, label: str):
    if not path.exists():
        raise ModelLoadError(
            f"{label} file not found at {path.name}. Run `python train_model.py` first."
        )

    try:
        with path.open("rb") as file:
            artifact = pickle.load(file)
        logger.info("Loaded %s from %s", label, path.name)
        return artifact
    except (pickle.UnpicklingError, EOFError, OSError) as exc:
        raise ModelLoadError(f"Failed to load {label}: {exc}") from exc


def _load_model_config() -> dict:
    defaults = {
        "optimal_threshold": DEFAULT_OPTIMAL_THRESHOLD,
        "logistic_regression_accuracy": 99.4,
        "naive_bayes_accuracy": 96.1,
        "selected_model": "Logistic Regression",
    }

    if not MODEL_CONFIG_PATH.exists():
        logger.warning(
            "model_config.json not found; using default threshold %.2f",
            DEFAULT_OPTIMAL_THRESHOLD,
        )
        return defaults

    try:
        with MODEL_CONFIG_PATH.open("r", encoding="utf-8") as file:
            config = json.load(file)
        merged = {**defaults, **config}
        logger.info("Loaded model configuration from model_config.json")
        return merged
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read model_config.json: %s", exc)
        return defaults
