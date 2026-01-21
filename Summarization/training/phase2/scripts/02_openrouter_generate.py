#!/usr/bin/env python3
"""
Step 2: Generate Stage 2 training data using OpenRouter API.

This script reads prompts from stage2_prompts.csv and calls OpenRouter API
to generate narrative outputs with "Insight" section.

Features:
- Checkpoint resume support
- Batch processing with periodic saves
- Retry logic with exponential backoff

Usage:
    python 02_openrouter_generate.py
    python 02_openrouter_generate.py --sample 100
    python 02_openrouter_generate.py --force-restart
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
SCRIPT_DIR = Path(__file__).parent
INPUT_CSV = SCRIPT_DIR.parent / "data" / "stage2_prompts.csv"
OUTPUT_CSV = SCRIPT_DIR.parent / "data" / "processed" / "stage2_training_narrative.csv"

DEFAULT_MODEL = "xiaomi/mimo-v2-flash:free"
BATCH_SIZE = 50
MAX_RETRIES = 5
DELAY_BETWEEN_REQUESTS = 0.5

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are an AI analyst that transforms hourly engagement data into clear, narrative recommendations.

Your task is to analyze the given hourly data and write:
1. A 1-2 sentence narrative explaining WHY this time slot is best (engaging, natural language)
2. An "Insight" section with 2-3 bullet points that explain the data in simple terms

IMPORTANT RULES:
- Use "Insight:" as the section header (NOT "Traceback:")
- Each bullet point must be a complete, natural sentence
- Make it accessible to non-technical readers
- Calculate percentages accurately from the provided data
- Keep total output under 80 words
- Vary your language - don't be repetitive"""


def get_headers() -> dict:
    """Get API headers with authentication."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/summarization-training",
        "X-Title": "Stage2 Training Generator"
    }


def call_openrouter(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Call OpenRouter API with prompt and return response."""
    headers = get_headers()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300,
        "temperature": 0.9
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                ENDPOINT,
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"].strip()
                    if "text" in choice:
                        return choice["text"].strip()
                return json.dumps(data)

            if response.status_code in (429, 503):
                backoff = 2 ** attempt
                logger.warning(
                    "Rate/Service error %d, retrying in %ds... (attempt %d)",
                    response.status_code, backoff, attempt
                )
                time.sleep(backoff)
                continue

            if response.status_code >= 400:
                logger.error(
                    "API Error %d: %s",
                    response.status_code,
                    response.text[:500] if response.text else "No response body"
                )

            response.raise_for_status()

        except requests.RequestException as exc:
            backoff = 2 ** attempt
            logger.warning(
                "Request error: %s. Retrying in %ds...", exc, backoff
            )
            time.sleep(backoff)

    return ""


def load_checkpoint() -> tuple[set, list]:
    """Load existing checkpoint data if available."""
    processed_indices = set()
    existing_results = []

    if not OUTPUT_CSV.exists():
        return processed_indices, existing_results

    try:
        checkpoint_df = pd.read_csv(OUTPUT_CSV)
        existing_results = checkpoint_df.to_dict("records")

        if INPUT_CSV.exists():
            source_df = pd.read_csv(INPUT_CSV)
            processed_inputs = set(checkpoint_df["input_text"].tolist())

            for idx, row in source_df.iterrows():
                if row.get("input_text", "") in processed_inputs:
                    processed_indices.add(idx)

        logger.info(
            "Loaded checkpoint: %d rows already processed",
            len(existing_results)
        )

    except Exception as exc:
        logger.warning("Could not load checkpoint: %s", exc)
        logger.info("Starting fresh...")

    return processed_indices, existing_results


def main(
    model: str = DEFAULT_MODEL,
    batch_size: int = BATCH_SIZE,
    sample_size: Optional[int] = None,
    force_restart: bool = False
) -> None:
    """Execute batch generation with checkpoint support."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set in environment.")
        print("Set it using: $env:OPENROUTER_API_KEY = 'your_key_here'")
        sys.exit(1)

    print("=" * 60)
    print("Stage 2 OpenRouter Batch Generator")
    print("=" * 60)
    print(f"Model: {model}")
    print(f"Input: {INPUT_CSV}")
    print(f"Output: {OUTPUT_CSV}")
    print(f"Batch size: {batch_size}")
    print("=" * 60)

    if not INPUT_CSV.exists():
        logger.error("Input file not found: %s", INPUT_CSV)
        logger.info("Run 01_generate_prompts.py first to create prompts.")
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    total_rows = len(df)

    if sample_size:
        df = df.head(sample_size)
        logger.info("SAMPLE MODE: processing %d of %d", len(df), total_rows)
    else:
        logger.info("Processing all %d rows", total_rows)

    if force_restart:
        logger.warning("Force restart enabled - ignoring existing checkpoint")
        processed_indices = set()
        results = []
    else:
        processed_indices, results = load_checkpoint()

    remaining_df = df[~df.index.isin(processed_indices)]
    remaining_count = len(remaining_df)

    if remaining_count == 0:
        logger.info("All rows already processed! Nothing to do.")
        return

    logger.info("Remaining to process: %d rows", remaining_count)
    logger.info("Already completed: %d rows", len(processed_indices))
    print("-" * 60)

    rows_in_batch = 0
    out_rows = len(results)

    try:
        for idx, row in remaining_df.iterrows():
            prompt = row["prompt_for_gemini"]
            input_text = row["input_text"]

            print(f"\r[{out_rows + 1}/{len(df)}] Generating for row {idx}...", end="")

            response_text = call_openrouter(prompt, model=model)

            if response_text:
                results.append({
                    "input_text": input_text,
                    "target_text": response_text
                })
                out_rows += 1
                rows_in_batch += 1
            else:
                logger.warning("Empty response for row %d, skipping...", idx)

            if rows_in_batch >= batch_size:
                pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
                logger.info("\nCheckpoint saved: %s (%d rows)", OUTPUT_CSV, out_rows)
                rows_in_batch = 0

            time.sleep(DELAY_BETWEEN_REQUESTS)

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user. Saving checkpoint...")
        pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
        logger.info("Checkpoint saved: %s (%d rows)", OUTPUT_CSV, out_rows)
        sys.exit(0)

    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print("\n" + "=" * 60)
    print(f"Done! Generated {out_rows} total rows -> {OUTPUT_CSV}")
    print("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Stage 2 training data using OpenRouter API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model to use for generation"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help="Number of rows per batch checkpoint"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Process only first N rows (for testing)"
    )
    parser.add_argument(
        "--force-restart",
        action="store_true",
        help="Ignore existing checkpoint and start fresh"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(
        model=args.model,
        batch_size=args.batch_size,
        sample_size=args.sample,
        force_restart=args.force_restart
    )
