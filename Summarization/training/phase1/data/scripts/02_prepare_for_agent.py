"""Batch Response Generator using AI Analysis.

Generates high-quality training data responses by preparing prompts
for Copilot agent processing.
"""
import json

import pandas as pd

# Read the batch file
df = pd.read_csv('./data/batch_first_50.csv')

print(f"Processing {len(df)} prompts...")
print("=" * 60)

# This will store all generated responses
responses = []

# Process each prompt
for idx in range(len(df)):
    student_input = df.iloc[idx]['student_input']
    prompt = df.iloc[idx]['prompt_for_gemini']
    
    # Parse prompt to extract context
    lines = prompt.split('\n')
    day = time = score = dominance = shape = style = behavior = ""
    
    for line in lines:
        if '- Day:' in line:
            day = line.split(':')[1].strip()
        elif '- Time:' in line:
            time_full = line.split('Time:')[1].strip()
            time = time_full.split('(')[0].strip()
            if '(' in time_full:
                time_label = time_full.split('(')[1].replace(')', '').strip()
            else:
                time_label = ""
        elif '- Score:' in line:
            score_text = line.split('Score:')[1].strip()
            score = score_text.split('/')[0].strip()
            if 'Runner-up' in score_text:
                runner_up = (
                    score_text.split('Runner-up:')[1]
                    .replace(')', '').strip()
                )
            else:
                runner_up = ""
        elif '- Pattern:' in line:
            pattern = line.split('Pattern:')[1].strip()
            if 'Unrivaled' in pattern:
                dominance = 'Unrivaled'
            elif 'Clear Lead' in pattern:
                dominance = 'Clear Lead'
            else:
                dominance = 'Tight Race'
            if 'Sharp Spike' in pattern:
                shape = 'Sharp Spike'
            else:
                shape = 'Sustained Plateau'
        elif '- User Behavior:' in line:
            behavior = line.split('User Behavior:')[1].strip()
        elif 'Required Style:' in line:
            style = line.split('Required Style:')[1].strip()
    
    # Store for manual review
    responses.append({
        'row_id': idx,
        'student_input': student_input,
        'context': {
            'day': day,
            'time': time,
            'score': score,
            'dominance': dominance,
            'shape': shape,
            'behavior': behavior,
            'style': style
        },
        'full_prompt': prompt
    })

# Save to JSON for GitHub Copilot to process
with open(
    './data/prompts_for_copilot_agent.json', 'w', encoding='utf-8'
) as f:
    json.dump(responses, f, indent=2, ensure_ascii=False)

print(f"\n✓ Extracted {len(responses)} prompts")
print("✓ Saved to ./data/prompts_for_copilot_agent.json")
print("\n" + "=" * 60)
print("READY FOR AI GENERATION")
print("=" * 60)
print("\nNext: GitHub Copilot agent will generate responses")
print("for each prompt based on the style and data context.")
