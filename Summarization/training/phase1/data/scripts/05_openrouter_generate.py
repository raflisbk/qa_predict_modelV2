#!/usr/bin/env python3
"""Batch generator using OpenRouter API with checkpoint resume support.

This module provides functionality to generate training data for summarization
models using the OpenRouter API. It includes automatic checkpoint loading to
resume from the last processed row, batch processing with periodic saves,
retry logic with exponential backoff, and progress tracking.

Example:
    Basic usage::

        $ python 05_openrouter_generate.py

    With sample size::

        $ python 05_openrouter_generate.py --sample 100

    Force restart::

        $ python 05_openrouter_generate.py --force-restart

Attributes:
    INPUT_CSV: Path to the input CSV file containing prompts.
    OUTPUT_CSV: Path to the output CSV file for generated responses.
    DEFAULT_MODEL: Default OpenRouter model to use.
    BATCH_SIZE: Number of rows per checkpoint save.
    MAX_RETRIES: Maximum number of retry attempts for API calls.
    DELAY_BETWEEN_REQUESTS: Delay in seconds between API requests.

Environment Variables:
    OPENROUTER_API_KEY: Required API key for OpenRouter authentication.
"""

import argparse
import json
import logging
import os
import sys
import time
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
INPUT_CSV = "./training/phase1/data/step1_dataset_prompts.csv"
OUTPUT_CSV = "./training/phase1/data/training_dataset_openrouter.csv"
DEFAULT_MODEL = "google/gemini-2.5-flash"
BATCH_SIZE = 100
SAMPLE_SIZE = None
MAX_RETRIES = 5
DELAY_BETWEEN_REQUESTS = 0.5

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are an AI writing assistant specialized in creating concise, "
    "data-driven recommendations for social media posting times. "
    "Generate responses that are specific, actionable, and match the "
    "requested style. Keep responses under 40 words."
)


def get_headers() -> dict:
    """Get API headers with authentication.

    Returns:
        dict: Headers dictionary containing authorization and content type.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/summarization-training",
        "X-Title": "Summarization Training Generator"
    }


def call_openrouter(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Call OpenRouter API with prompt and return response.

    Makes an API request to OpenRouter with retry logic and exponential
    backoff for rate limiting and service errors.

    Args:
        prompt: The prompt text to send to the model.
        model: Model identifier to use for generation.

    Returns:
        Generated text response or empty string on failure.
    """
    headers = get_headers()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
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

            # Log error details for debugging
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
    """Load existing checkpoint data if available.

    Reads the output CSV file and determines which rows have already been
    processed by matching input_text with source data.

    Returns:
        Tuple containing:
            - Set of processed row indices
            - List of existing results as dictionaries
    """
    processed_indices = set()
    existing_results = []

    if not os.path.exists(OUTPUT_CSV):
        return processed_indices, existing_results

    try:
        checkpoint_df = pd.read_csv(OUTPUT_CSV)
        existing_results = checkpoint_df.to_dict("records")

        if os.path.exists(INPUT_CSV):
            source_df = pd.read_csv(INPUT_CSV)
            processed_inputs = set(checkpoint_df["input_text"].tolist())

            for idx, row in source_df.iterrows():
                if row.get("student_input", "") in processed_inputs:
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
    sample_size: Optional[int] = SAMPLE_SIZE,
    force_restart: bool = False
) -> None:
    """Execute batch generation with checkpoint support.

    Args:
        model: Model identifier to use for generation.
        batch_size: Number of rows per batch before saving checkpoint.
        sample_size: Limit processing to first N rows (None for all).
        force_restart: If True, ignore existing checkpoint and start fresh.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set in environment.")
        print("Set it using: $env:OPENROUTER_API_KEY = 'your_key_here'")
        sys.exit(1)

    print("=" * 60)
    print("OpenRouter Batch Generator with Checkpoint Resume")
    print("=" * 60)
    print(f"Model: {model}")
    print(f"Input: {INPUT_CSV}")
    print(f"Output: {OUTPUT_CSV}")
    print(f"Batch size: {batch_size}")
    print("=" * 60)

    if not os.path.exists(INPUT_CSV):
        logger.error("Input file not found: %s", INPUT_CSV)
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
            input_text = row.get("student_input", "")

            print(f"[{out_rows + 1}/{len(df)}] Generating for row {idx}...")

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
                logger.info("Checkpoint saved: %s (%d rows)", OUTPUT_CSV, out_rows)
                rows_in_batch = 0

            time.sleep(DELAY_BETWEEN_REQUESTS)

    except KeyboardInterrupt:
        logger.info("Interrupted by user. Saving checkpoint...")
        pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
        logger.info("Checkpoint saved: %s (%d rows)", OUTPUT_CSV, out_rows)
        sys.exit(0)

    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print("=" * 60)
    print(f"Done! Generated {out_rows} total rows -> {OUTPUT_CSV}")
    print("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Generate training data using OpenRouter API",
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
