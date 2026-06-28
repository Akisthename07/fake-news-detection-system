"""Tests for environment configuration loading."""

from pathlib import Path

import pytest
from dotenv import load_dotenv


def test_env_file_loaded_when_present(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("PLACEHOLDER=1\n", encoding="utf-8")

    monkeypatch.setattr("config._env_path", env_file)

    from config import env_file_loaded

    assert env_file_loaded() is True


def test_dotenv_loads_values_from_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GNEWS_API_KEY=test-gnews-key\n", encoding="utf-8")

    monkeypatch.delenv("GNEWS_API_KEY", raising=False)
    load_dotenv(env_file, override=True)

    import os

    assert os.getenv("GNEWS_API_KEY") == "test-gnews-key"


def test_mask_secret():
    from config import mask_secret

    assert mask_secret("") == "(not set)"
    assert mask_secret("abcd") == "****"
    assert mask_secret("abcdefghij") == "abcd...ghij"
