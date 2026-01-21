"""AI Training Dataset Generator - Using GitHub Copilot Agent.

This script processes prompts in batches and creates JSON files
for Copilot agent to generate responses.
"""
import json

import pandas as pd
from tqdm import tqdm


# --- KONFIGURASI ---
INPUT_FILE = "./data/step1.csv"
OUTPUT_FILE = "./data/training_dataset_copilot.csv"
BATCH_SIZE = 100  # Process dan save per batch
SAMPLE_SIZE = None  # Set angka untuk test (misal 200), None untuk semua

print("=" * 60)
print("AI Training Dataset Generator - Using GitHub Copilot Agent")
print("=" * 60)

def generate_response(prompt_text):
    """Generate response from prompt using GitHub Copilot agent.

    Args:
        prompt_text: The prompt string containing data context and style.

    Returns:
        Generated response string based on the prompt.
    """
    # Parse the prompt to extract key information
    lines = prompt_text.split('\n')
    
    # Extract data from prompt
    day = None
    time_window = None
    score = None
    dominance = None
    shape = None
    style = None
    
    for line in lines:
        if '- Day:' in line:
            day = line.split('Day:')[1].strip()
        elif '- Time:' in line:
            time_window = line.split('Time:')[1].split('(')[0].strip()
        elif '- Score:' in line:
            score_text = line.split('Score:')[1].split('/')[0].strip()
            score = int(score_text)
        elif '- Pattern:' in line:
            if 'Unrivaled' in line:
                dominance = 'Unrivaled'
            elif 'Clear Lead' in line:
                dominance = 'Clear Lead'
            else:
                dominance = 'Tight Race'

            if 'Sharp Spike' in line:
                shape = 'Sharp Spike'
            else:
                shape = 'Sustained Plateau'
        elif 'Required Style:' in line:
            style = line.split('Required Style:')[1].strip()
    
    # Generate response based on the data
    # This placeholder will be replaced by actual Copilot-generated content
    return f"PLACEHOLDER_FOR_ROW_{day}_{time_window}_{score}"


def main():
    """Main execution function for batch processing."""
    # Load data
    print(f"\n📂 Loading data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    
    # Limit to sample if set
    if SAMPLE_SIZE:
        df = df.head(SAMPLE_SIZE)
        print(f"🎯 SAMPLE MODE: Processing {len(df)} rows")
    else:
        print(f"📊 Processing ALL {len(df)} rows")
    
    print(f"\n🤖 Using GitHub Copilot (Claude Sonnet 4.5) for generation")
    print(f"💾 Saving results to: {OUTPUT_FILE}")
    print(f"📦 Batch size: {BATCH_SIZE} rows\n")
    
    # Process in batches
    results = []

    print("Starting generation...")
    print("-" * 60)

    # MANUAL PROMPT BATCHES - For Copilot to process
    # We'll create batches of prompts for the user to send to Copilot

    batch_files = []
    for batch_num in range(0, len(df), BATCH_SIZE):
        batch_df = df.iloc[batch_num:batch_num + BATCH_SIZE]
        batch_file = f"./data/batch_{batch_num}_{batch_num + len(batch_df)}.json"
        
        batch_data = []
        for idx, row in batch_df.iterrows():
            batch_data.append({
                'row_id': idx,
                'student_input': row['student_input'],
                'prompt_for_gemini': row['prompt_for_gemini']
            })
        
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)

        batch_files.append(batch_file)
        print(
            f"✓ Created batch file: {batch_file} "
            f"({len(batch_data)} prompts)"
        )

    print("\n" + "=" * 60)
    print("📋 NEXT STEPS:")
    print("=" * 60)
    print(f"\n{len(batch_files)} batch files created in ./data/")
    print("\nTo generate responses:")
    print("1. Send each batch file to GitHub Copilot")
    print("2. Ask Copilot to generate responses for each prompt")
    print("3. Save responses back to a results file")
    print("\nOR use the interactive script: copilot_batch_processor.py")


if __name__ == "__main__":
    main()
