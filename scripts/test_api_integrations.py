#!/usr/bin/env python
"""
Run live integration tests against GNews, Gemini, and Fact Check APIs.

Usage:
    python scripts/test_api_integrations.py

Requires a .env file with API keys (copy from .env.example).
"""

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.diagnostics import run_diagnostics  # noqa: E402


def main() -> int:
    print("=" * 70)
    print("NewsVerify — Live API Integration Tests")
    print("=" * 70)

    report = run_diagnostics()
    print(f"\n.env loaded: {report['env_file_loaded']}")
    print(f"Timestamp:   {report['timestamp']}")
    print(f"Summary:     {report['summary']['healthy']}/{report['summary']['total']} healthy\n")

    exit_code = 0

    for name, check in report["integrations"].items():
        print("-" * 70)
        print(f"Service:     {check['service']}")
        print(f"Env var:     {check['env_var']}")
        print(f"Configured:  {check['configured']}")
        print(f"Key preview: {check['key_preview']}")
        print(f"Status:      {check['status']}")
        print(f"Message:     {check['message']}")
        print("\nSample request:")
        print(json.dumps(check["sample_request"], indent=2))

        if check.get("sample_response"):
            print("\nSample response:")
            if isinstance(check["sample_response"], str):
                print(check["sample_response"])
            else:
                print(json.dumps(check["sample_response"], indent=2))

        if check["status"] != "ok":
            exit_code = 1
        print()

    print("=" * 70)
    if exit_code == 0:
        print("All configured integrations are healthy.")
    else:
        print("One or more integrations are disabled or failed.")
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
