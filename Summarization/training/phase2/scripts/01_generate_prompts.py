#!/usr/bin/env python3
"""
Step 1: Generate prompts for Stage 2 training data using OpenRouter.

This script reads the existing stage2_training_data.csv, extracts the input data,
and creates prompts for OpenRouter to generate varied, narrative-style outputs
with "Insight" section instead of "Traceback".

Output format for each row:
- input_text: Original input with hourly data
- prompt_for_gemini: Prompt to send to OpenRouter
"""

import pandas as pd
import csv
from pathlib import Path

# Paths
INPUT_CSV = Path(__file__).parent.parent / "data" / "processed" / "stage2_training_data.csv"
OUTPUT_CSV = Path(__file__).parent.parent / "data" / "stage2_prompts.csv"

# System prompt for OpenRouter
SYSTEM_PROMPT = """You are an AI analyst that transforms hourly engagement data into clear, narrative recommendations.

Your task is to analyze the given hourly data and write:
1. A 1-2 sentence narrative explaining WHY this time slot is best (engaging, natural language)
2. An "Insight" section with 2-3 bullet points that explain the data in simple terms

IMPORTANT RULES:
- Use "Insight:" as the section header (NOT "Traceback:")
- Each bullet point must be a complete, natural sentence
- Make it accessible to non-technical readers
- Calculate percentages accurately from the provided data
- Keep total output under 80 words"""

# Prompt template
PROMPT_TEMPLATE = """Data Context:
{input_data}

Based on this data, write a narrative summary with an Insight section.

Example of GOOD output:
"Saturday's 09:00-12:00 time slot achieves an impressive 84/100 engagement score, capturing users during their relaxed weekend morning browsing.

Insight:
- The peak engagement at 10 AM reaches 92 points, which is 18% higher than the daily average of 78.
- This morning window outperforms the evening slot (6-9 PM) by 12%, making it a better choice for weekend content.
- The sustained high activity throughout this window suggests users are more receptive to longer content."

Now write YOUR output for the data above. Use varied language, don't copy the example exactly."""


def parse_input_text(input_text: str) -> dict:
    """Parse input text to extract components."""
    lines = input_text.strip().split("\n")
    result = {}
    
    for line in lines:
        if line.startswith("Day:"):
            # Parse: Day: Tuesday, Time: 00:00 - 03:00, Score: 72
            parts = line.split(", ")
            for part in parts:
                if "Day:" in part:
                    result["day"] = part.split("Day:")[1].strip()
                elif "Time:" in part:
                    result["time"] = part.split("Time:")[1].strip()
                elif "Score:" in part:
                    result["score"] = part.split("Score:")[1].strip()
        elif line.startswith("Hourly:"):
            result["hourly"] = line
        elif line.startswith("Daily Avg:"):
            result["daily_info"] = line
    
    return result


def main():
    """Generate prompts from existing Stage 2 data."""
    print("=" * 60)
    print("Stage 2 Prompt Generator")
    print("=" * 60)
    print(f"Input: {INPUT_CSV}")
    print(f"Output: {OUTPUT_CSV}")
    print("=" * 60)
    
    if not INPUT_CSV.exists():
        print(f"ERROR: Input file not found: {INPUT_CSV}")
        return
    
    # Read existing data
    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} rows from existing Stage 2 data")
    
    # Generate prompts
    prompts = []
    
    for idx, row in df.iterrows():
        input_text = row["input_text"]
        
        # Create prompt for OpenRouter
        prompt = PROMPT_TEMPLATE.format(input_data=input_text)
        
        prompts.append({
            "input_text": input_text,
            "prompt_for_gemini": prompt
        })
        
        if (idx + 1) % 500 == 0:
            print(f"Processed {idx + 1}/{len(df)} rows...")
    
    # Save to CSV
    output_df = pd.DataFrame(prompts)
    output_df.to_csv(OUTPUT_CSV, index=False, quoting=csv.QUOTE_ALL)
    
    print(f"\nSaved {len(prompts)} prompts to: {OUTPUT_CSV}")
    
    # Show sample
    print("\n" + "=" * 60)
    print("SAMPLE PROMPT:")
    print("=" * 60)
    sample = prompts[0]
    print(f"\nINPUT TEXT:\n{sample['input_text'][:200]}...")
    print(f"\nPROMPT (truncated):\n{sample['prompt_for_gemini'][:500]}...")


if __name__ == "__main__":
    main()
