"""Test Stage 2 Model with Post-Processing.

This script loads the model and applies post-processing to fix:
1. Peak percentage calculation
2. Time window average calculations
3. Text formatting (newlines)
"""

import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add inference directory to path
inference_dir = Path(__file__).parent / "inference"
sys.path.insert(0, str(inference_dir))

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

# Path to local model
LOCAL_MODEL_PATH = "./models/t5-posting-time-summarizer"


def parse_hourly_data(hourly_str: str) -> List[Tuple[int, float]]:
    """Parse hourly string into list of (hour, value) tuples."""
    pattern = r'(\d+)\((\d+(?:\.\d+)?)\)'
    matches = re.findall(pattern, hourly_str)
    return [(int(h), float(v)) for h, v in matches]


def calculate_time_window_avg(
    hourly_data: List[Tuple[int, float]],
    start_hour: int,
    end_hour: int
) -> float:
    """Calculate average value for a time window."""
    values = [v for h, v in hourly_data if start_hour <= h < end_hour]
    return sum(values) / len(values) if values else 0.0


def fix_traceback_calculations(
    generated_text: str,
    hourly_summary: Dict[str, Any]
) -> str:
    """Fix calculation errors while preserving narrative (Regex-based)."""
    
    # Parse hourly data
    pattern = r'(\d+)\((\d+(?:\.\d+)?)\)'
    matches = re.findall(pattern, hourly_summary['hourly'])
    hourly_dict = {int(h): float(v) for h, v in matches}
    
    peak_value = float(hourly_summary['peak_value'])
    daily_avg = float(hourly_summary['daily_avg'])
    
    # 1. Fix "XX% higher than the daily average"
    def fix_percentage(match):
        try:
            # Simple assumption: compare peak to daily avg
            correct_pct = int(((peak_value - daily_avg) / daily_avg) * 100)
            return f"{correct_pct}% higher than the daily average of {daily_avg}"
        except:
            return match.group(0)

    generated_text = re.sub(
        r'(\d+)%\s+higher\s+than\s+the\s+daily\s+average\s+of\s+([\d.]+)',
        fix_percentage,
        generated_text
    )

    # 2. Fix "The H AM/PM hour hits V points"
    def fix_hour_points(match):
        hour = int(match.group(1))
        meridiem = match.group(2).upper() if match.group(2) else ""
        actual_hour = hour
        if meridiem == "PM" and hour < 12: actual_hour += 12
        elif meridiem == "AM" and hour == 12: actual_hour = 0
            
        if actual_hour in hourly_dict:
            actual_val = hourly_dict[actual_hour]
            val_fmt = int(actual_val) if actual_val.is_integer() else actual_val
            return f"The {hour} {meridiem} hour hits {val_fmt} points".replace("  ", " ")
        return match.group(0)

    generated_text = re.sub(
        r'The\s+(\d+)\s*(AM|PM)?\s*hour\s+hits\s+(\d+(?:\.\d+)?)\s+points',
        fix_hour_points,
        generated_text,
        flags=re.IGNORECASE
    )

    # 3. Format bullets
    text = re.sub(r'(Insight|Traceback):([^\s\n])', r'\1: \2', generated_text)
    text = re.sub(r'([\.!?])\s*(Insight|Traceback):', r'\1\n\n\2:', text)
    
    if "Insight:" in text or "Traceback:" in text:
        header = "Insight:" if "Insight:" in text else "Traceback:"
        parts = text.split(header)
        narrative = parts[0]
        content = parts[1]
        bullets = re.split(r'\s*[-\u2022]\s+', content)
        bullets = [b.strip() for b in bullets if b.strip()]
        if bullets:
            text = narrative.strip() + "\n\n" + header + "\n- " + "\n- ".join(bullets)
    
    return text


# Test data
test_input = {
    "day": "Saturday",
    "time_window": "09:00 - 12:00",
    "score": 79,
    "daily_avg": 55.7,
    "peak_hour": 9,
    "peak_value": 97,
    "hourly": "01(30), 02(28), 03(30), 04(37), 05(44), 06(48), 07(65), 08(84), 09(97), 10(84), 11(77), 12(73), 13(77), 14(74), 15(59), 16(63), 17(59), 18(50), 19(54), 20(50), 21(50), 22(43), 23(34)"
}

print("=" * 60)
print("Testing Stage 2 Model with Post-Processing")
print("=" * 60)

print(f"\nModel path: {LOCAL_MODEL_PATH}")

print("\nInput:")
print(f"  Day: {test_input['day']}")
print(f"  Time: {test_input['time_window']}")
print(f"  Score: {test_input['score']}")
print(f"  Peak: {test_input['peak_hour']:02d}:00 ({test_input['peak_value']})")
print(f"  Daily Avg: {test_input['daily_avg']}")

# Calculate expected peak percentage
expected_peak_pct = int(((test_input['peak_value'] - test_input['daily_avg']) / test_input['daily_avg']) * 100)
print(f"\nExpected peak percentage: +{expected_peak_pct}%")

print("\nLoading model...")

try:
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        f"{LOCAL_MODEL_PATH}/stage1"
    )
    print("✅ Tokenizer loaded")
    
    # Load base model (simple load without device_map)
    base_model = AutoModelForSeq2SeqLM.from_pretrained(
        f"{LOCAL_MODEL_PATH}/stage1"
    )
    print("✅ Base model loaded")
    
    # Clear memory before loading adapter
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Create offload folder for memory management
    offload_folder = Path("./offload_temp")
    offload_folder.mkdir(exist_ok=True)
    
    # Load adapter with offload support
    # We use stage2b (the new model with Insight format)
    adapter_path = f"{LOCAL_MODEL_PATH}/stage2b"
    model = PeftModel.from_pretrained(
        base_model,
        adapter_path,
        offload_folder=str(offload_folder)
    )
    print(f"✅ LoRA adapter loaded from: {adapter_path}")
    
    model.eval()
    device = next(model.parameters()).device
    
    print("\nGenerating summary...")
    
    # Format input
    input_text = (
        f"Day: {test_input['day']}, "
        f"Time: {test_input['time_window']}, "
        f"Score: {int(test_input['score'])}\n"
        f"Hourly: {test_input['hourly']}\n"
        f"Daily Avg: {test_input['daily_avg']}, "
        f"Peak: {test_input['peak_hour']:02d}({test_input['peak_value']})"
    )
    
    input_with_prefix = f"summarize: {input_text}"
    
    # Tokenize
    inputs = tokenizer(
        input_with_prefix,
        return_tensors="pt",
        max_length=256,
        truncation=True
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    # Generate with stable parameters (no sampling to avoid hallucination)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=512,
            num_beams=4,
            early_stopping=True,
            do_sample=False,
            repetition_penalty=1.2,   # ⬅️ Avoid repetition
            no_repeat_ngram_size=3,   # ⬅️ No repeated 3-grams
        )
    
    # Decode
    raw_summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    print("\n" + "=" * 60)
    print("RAW Output (before post-processing):")
    print("=" * 60)
    print(raw_summary)
    
    # Apply post-processing
    processed_summary = fix_traceback_calculations(raw_summary, test_input)
    
    print("\n" + "=" * 60)
    print("PROCESSED Output (after post-processing):")
    print("=" * 60)
    print(processed_summary)
    print("=" * 60)
    
    # Verify results
    print("\n✅ Post-processing applied!")
    
    if f"+{expected_peak_pct}%" in processed_summary:
        print(f"✅ Peak percentage correct: +{expected_peak_pct}%")
    else:
        print(f"⚠️  Peak percentage may need adjustment")
    
    if "\n" in processed_summary:
        print("✅ Formatting improved with newlines")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
