"""
gemini_probe.py  —  one-shot diagnosis for the Gemini 429.

Run from your project root (same dir you run app.py from):
    python gemini_probe.py

It does two independent things:
  1) Reports WHICH gemini_service.py Python actually imports, and whether
     that file is the OLD version (FALLBACK_MODEL, a string) or the NEW one
     (FALLBACK_MODELS, a list). This catches a stale / shadowed module.
  2) Calls Google directly, bypassing your app code entirely, and prints the
     real HTTP status, the Retry-After header, and the full JSON body so you
     can see the actual reason (RPM vs RPD vs 403 vs model-not-found).
"""

import json
import os
import sys
from pathlib import Path

import requests

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
PROBE_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]


def load_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()
    env = Path(".env")
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY") and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def report_loaded_module() -> None:
    print("=" * 70)
    print("1) WHICH gemini_service IS PYTHON ACTUALLY RUNNING?")
    print("=" * 70)
    print(f"cwd: {os.getcwd()}")
    try:
        from services import gemini_service as g
    except Exception as exc:  # noqa: BLE001
        print(f"  !! could not import services.gemini_service: {exc}")
        print("     (run this from the same directory you run app.py from)")
        return

    print(f"  imported from: {getattr(g, '__file__', '?')}")
    has_old = hasattr(g, "FALLBACK_MODEL")        # str  -> old file
    has_new = hasattr(g, "FALLBACK_MODELS")       # list -> patched file
    if has_new and not has_old:
        print("  version: NEW (patched). Good — the fix is in place.")
    elif has_old and not has_new:
        print("  version: OLD (unpatched).  <-- THIS is the file running.")
        print("     The patched gemini_service.py is NOT what your app loads.")
        print("     You edited a different copy, or the server wasn't restarted,")
        print("     or a stale .pyc is being used.")
    else:
        print(f"  version: AMBIGUOUS (old={has_old}, new={has_new})")

    # Show any duplicate copies on disk that could be shadowing each other.
    matches = list(Path(".").rglob("gemini_service.py"))
    if len(matches) > 1:
        print("  WARNING: multiple gemini_service.py on disk:")
        for m in matches:
            print(f"     - {m}")


def probe_raw(key: str) -> None:
    print()
    print("=" * 70)
    print("2) RAW CALL TO GOOGLE (bypasses your app code)")
    print("=" * 70)
    payload = {"contents": [{"parts": [{"text": "ping"}]}]}
    headers = {"Content-Type": "application/json", "x-goog-api-key": key}

    for model in PROBE_MODELS:
        url = f"{API_BASE}/{model}:generateContent"
        print(f"\n--- {model} ---")
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=20)
        except requests.RequestException as exc:
            print(f"  network error: {exc}")
            continue

        print(f"  HTTP {r.status_code}")
        for h in ("Retry-After", "X-RateLimit-Limit", "X-RateLimit-Remaining"):
            if h in r.headers:
                print(f"  {h}: {r.headers[h]}")

        try:
            body = r.json()
        except ValueError:
            print(f"  body (text): {r.text[:500]}")
            continue

        if r.status_code == 200:
            try:
                txt = body["candidates"][0]["content"]["parts"][0]["text"]
                print(f"  SUCCESS — model replied: {txt.strip()[:80]!r}")
            except (KeyError, IndexError):
                print(f"  200 but no text. finishReason / body:\n{json.dumps(body, indent=2)[:800]}")
        else:
            err = body.get("error", {})
            print(f"  status field : {err.get('status')}")
            print(f"  message      : {err.get('message')}")
            # The QuotaFailure detail tells you RPM vs RPD.
            for d in err.get("details", []):
                if "QuotaFailure" in str(d.get("@type", "")):
                    for v in d.get("violations", []):
                        print(f"  quota hit    : {v.get('quotaId') or v.get('quotaMetric')}")
                if "retryDelay" in d:
                    print(f"  retryDelay   : {d['retryDelay']}")


def main() -> None:
    key = load_key()
    report_loaded_module()
    if not key:
        print("\n!! No GEMINI_API_KEY found in environment or ./.env — can't do the raw call.")
        sys.exit(1)
    print(f"\n(using key ...{key[-6:]})")
    probe_raw(key)
    print("\n" + "=" * 70)
    print("READ THE RESULT:")
    print("  - Section 2 shows HTTP 200 SUCCESS, but your app still errors")
    print("        -> your app runs OLD/shadowed code (see section 1). Replace it + restart.")
    print("  - Section 2 shows HTTP 429 with quota 'PerDay' / RPD")
    print("        -> daily cap; wait for midnight Pacific or enable billing.")
    print("  - Section 2 shows HTTP 429 with quota 'PerMinute' / RPM")
    print("        -> you're calling too fast; throttle, or stop hammering refresh.")
    print("  - Section 2 shows HTTP 403 / API_KEY_SERVICE_BLOCKED / disabled")
    print("        -> enable 'Generative Language API' on that project / unrestrict the key.")
    print("=" * 70)


if __name__ == "__main__":
    main()