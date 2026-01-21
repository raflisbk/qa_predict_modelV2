#!/usr/bin/env python3
"""Batch generator menggunakan OpenRouter API untuk bahasa Indonesia.

Modul ini menyediakan fungsionalitas untuk generate training data dalam
bahasa Indonesia untuk model summarization menggunakan OpenRouter API.

Fitur:
- Checkpoint resume support
- Batch processing dengan periodic saves
- Retry logic dengan exponential backoff
- Progress tracking

Contoh penggunaan:
    Basic usage::

        $ python 05_openrouter_generate_id.py

    Dengan sample size::

        $ python 05_openrouter_generate_id.py --sample 100

    Force restart::

        $ python 05_openrouter_generate_id.py --force-restart

Environment Variables:
    OPENROUTER_API_KEY: API key untuk autentikasi OpenRouter.
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

# --- KONFIGURASI ---
INPUT_CSV = "./training/phase1_id/data/step1_dataset_prompts_id.csv"
OUTPUT_CSV = "./training/phase1_id/data/training_dataset_id.csv"
DEFAULT_MODEL = "xiaomi/mimo-v2-flash:free"
BATCH_SIZE = 100
SAMPLE_SIZE = None
MAX_RETRIES = 5
DELAY_BETWEEN_REQUESTS = 0.5

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

# System prompt dalam bahasa Indonesia
SYSTEM_PROMPT = (
    "Anda adalah asisten penulisan AI yang ahli dalam membuat rekomendasi "
    "waktu posting media sosial yang ringkas dan berbasis data. "
    "Generate respons dalam bahasa Indonesia yang spesifik, dapat ditindaklanjuti, "
    "dan sesuai dengan gaya penulisan yang diminta. "
    "Batasi respons maksimal 50 kata. "
    "Gunakan bahasa yang natural dan mudah dipahami."
)


def get_headers() -> dict:
    """Get API headers dengan autentikasi.

    Returns:
        dict: Headers dictionary berisi authorization dan content type.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/summarization-training",
        "X-Title": "Summarization Training Generator ID"
    }


def call_openrouter(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Panggil OpenRouter API dengan prompt dan return respons.

    Args:
        prompt: Teks prompt untuk dikirim ke model.
        model: Model identifier untuk generation.

    Returns:
        Teks respons atau string kosong jika gagal.
    """
    headers = get_headers()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 250,
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
                    "Rate/Service error %d, retry dalam %d detik... (attempt %d)",
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
                "Request error: %s. Retry dalam %d detik...", exc, backoff
            )
            time.sleep(backoff)

    return ""


def load_checkpoint() -> tuple[set, list]:
    """Load checkpoint data yang sudah ada.

    Returns:
        Tuple berisi:
            - Set of processed row indices
            - List of existing results sebagai dictionaries
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
            "Loaded checkpoint: %d baris sudah diproses",
            len(existing_results)
        )

    except Exception as exc:
        logger.warning("Tidak bisa load checkpoint: %s", exc)
        logger.info("Mulai dari awal...")

    return processed_indices, existing_results


def main(
    model: str = DEFAULT_MODEL,
    batch_size: int = BATCH_SIZE,
    sample_size: Optional[int] = SAMPLE_SIZE,
    force_restart: bool = False
) -> None:
    """Jalankan batch generation dengan checkpoint support.

    Args:
        model: Model identifier untuk generation.
        batch_size: Jumlah baris per batch sebelum menyimpan checkpoint.
        sample_size: Batasi proses ke N baris pertama (None untuk semua).
        force_restart: Jika True, abaikan checkpoint dan mulai ulang.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        logger.error("OPENROUTER_API_KEY tidak di-set di environment.")
        print("Set dengan: $env:OPENROUTER_API_KEY = 'your_key_here'")
        sys.exit(1)

    print("=" * 60)
    print("OpenRouter Batch Generator - Bahasa Indonesia")
    print("=" * 60)
    print(f"Model: {model}")
    print(f"Input: {INPUT_CSV}")
    print(f"Output: {OUTPUT_CSV}")
    print(f"Batch size: {batch_size}")
    print("=" * 60)

    if not os.path.exists(INPUT_CSV):
        logger.error("File input tidak ditemukan: %s", INPUT_CSV)
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    total_rows = len(df)

    if sample_size:
        df = df.head(sample_size)
        logger.info("MODE SAMPLE: memproses %d dari %d", len(df), total_rows)
    else:
        logger.info("Memproses semua %d baris", total_rows)

    if force_restart:
        logger.warning("Force restart diaktifkan - mengabaikan checkpoint")
        processed_indices = set()
        results = []
    else:
        processed_indices, results = load_checkpoint()

    remaining_df = df[~df.index.isin(processed_indices)]
    remaining_count = len(remaining_df)

    if remaining_count == 0:
        logger.info("Semua baris sudah diproses! Tidak ada yang perlu dilakukan.")
        return

    logger.info("Sisa yang perlu diproses: %d baris", remaining_count)
    logger.info("Sudah selesai: %d baris", len(processed_indices))
    print("-" * 60)

    rows_in_batch = 0
    out_rows = len(results)

    try:
        for idx, row in remaining_df.iterrows():
            prompt = row["prompt_for_llm"]
            input_text = row.get("student_input", "")

            print(f"[{out_rows + 1}/{len(df)}] Generating untuk baris {idx}...")

            response_text = call_openrouter(prompt, model=model)

            if response_text:
                results.append({
                    "input_text": input_text,
                    "target_text": response_text
                })
                out_rows += 1
                rows_in_batch += 1
            else:
                logger.warning("Respons kosong untuk baris %d, skip...", idx)

            if rows_in_batch >= batch_size:
                pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
                logger.info("Checkpoint disimpan: %s (%d baris)", OUTPUT_CSV, out_rows)
                rows_in_batch = 0

            time.sleep(DELAY_BETWEEN_REQUESTS)

    except KeyboardInterrupt:
        logger.info("Dihentikan oleh user. Menyimpan checkpoint...")
        pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        logger.info("Checkpoint disimpan: %s (%d baris)", OUTPUT_CSV, out_rows)
        sys.exit(0)

    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    print("=" * 60)
    print(f"Selesai! Generated {out_rows} total baris -> {OUTPUT_CSV}")
    print("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Generate training data menggunakan OpenRouter API (Bahasa Indonesia)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model untuk generation"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help="Jumlah baris per batch checkpoint"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Proses hanya N baris pertama (untuk testing)"
    )
    parser.add_argument(
        "--force-restart",
        action="store_true",
        help="Abaikan checkpoint dan mulai dari awal"
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
