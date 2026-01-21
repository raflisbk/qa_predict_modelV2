"""List available models from OpenRouter for the provided API key.

Usage:
  set OPENROUTER_API_KEY in your environment, then run:
    python openrouter_list_models.py

This prints a compact table of model id, provider and description.
"""
import json
import os

import requests

API_URL = "https://openrouter.ai/api/v1/models"


def main():
    """Fetch and display available OpenRouter models."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: Please set OPENROUTER_API_KEY environment variable.")
        return

    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        r = requests.get(API_URL, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()

        models = data.get("data") or data.get("models") or data
        response_keys = list(data.keys())
        print(
            f"Found {len(models)} models "
            f"(raw response keys: {response_keys})\n"
        )
        for m in models:
            # flexible field access
            mid = m.get("id") or m.get("model") or m.get("name")
            prov = (
                m.get("provider") or m.get("source") or m.get("owner")
            )
            desc = m.get("description") or m.get("summary") or ""
            print(f"- {mid}  | provider: {prov} | {desc}")

    except requests.HTTPError as he:
        print("HTTP error:", he)
        try:
            print("Response:", r.text)
        except Exception:
            pass
    except Exception as e:
        print("Error connecting to OpenRouter:", e)


if __name__ == '__main__':
    main()
