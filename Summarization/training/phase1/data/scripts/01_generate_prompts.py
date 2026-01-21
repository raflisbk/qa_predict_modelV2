"""Generate synthetic dataset prompts for AI training.

This script creates 10,000 unique scenarios combining days, time slots,
scores, and styles for social media posting optimization.
"""
import random

import pandas as pd


# --- CONFIGURATION ---
TOTAL_ROWS = 10000
OUTPUT_FILE = "./data/step1_dataset_prompts.csv"

# --- 1. DEFINE LISTS ---
DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]

TIME_SLOTS = [
    {
        "window": "06:00 - 09:00",
        "label": "Morning Rush",
        "insight": "users checking phones before work"
    },
    {
        "window": "09:00 - 12:00",
        "label": "Mid-Morning",
        "insight": "professionals active during work breaks"
    },
    {
        "window": "12:00 - 13:00",
        "label": "Lunch Break",
        "insight": "high engagement during midday rest"
    },
    {
        "window": "13:00 - 17:00",
        "label": "Afternoon Lull",
        "insight": "moderate activity during work hours"
    },
    {
        "window": "17:00 - 19:00",
        "label": "Commute Hours",
        "insight": "audiences active during transit"
    },
    {
        "window": "19:00 - 22:00",
        "label": "Prime Time",
        "insight": "peak leisure time after dinner"
    },
    {
        "window": "22:00 - 00:00",
        "label": "Late Night",
        "insight": "night owls scrolling before sleep"
    },
    {
        "window": "00:00 - 06:00",
        "label": "Overnight",
        "insight": "minimal but dedicated late-night audience"
    }
]

STYLES = [
    "Analytic (Focus on numbers & trends)",
    "Strategic (Focus on ROI & Growth)",
    "Executive (Brief, Direct, Decision-oriented)",
    "Enthusiastic (High energy, Marketing tone)",
    "Advisory (Consultative, Helpful)",
    "Urgent (Creating FOMO/Action)",
    "Relaxed (Casual professional)",
    "Detailed (Deep dive analysis)",
    "Persuasive (Convincing)",
    "Storytelling (Narrative flow)"
]

# --- 2. GENERATE DATASET ---
def generate_dataset():
    """Generate complete dataset with synthetic prompts."""
    dataset = []
    
    print(f"Generating {TOTAL_ROWS} unique scenarios...")

    for i in range(TOTAL_ROWS):
        # 3. Random scenario generation
        score = random.randint(70, 99)
        runner_up_score = random.randint(40, score)
        gap = score - runner_up_score
        
        # Determine dominance label
        if gap > 20:
            dominance_label = "Unrivaled"
        elif gap > 10:
            dominance_label = "Clear Lead"
        else:
            dominance_label = "Tight Race"
        
        # Determine graph shape
        graph_shape = random.choice(["Sharp Spike", "Sustained Plateau"])
        
        # Select random day, time slot, and style
        day = random.choice(DAYS)
        time_slot = random.choice(TIME_SLOTS)
        style = random.choice(STYLES)
        
        # 4. Construct prompt for Gemini (what the teacher sees)
        prompt_for_gemini = (
            f"Data Context:\n"
            f"- Day: {day}\n"
            f"- Time: {time_slot['window']} ({time_slot['label']})\n"
            f"- Score: {score}/100 (Runner-up: {runner_up_score})\n"
            f"- Pattern: {dominance_label} dominance with "
            f"{graph_shape} behavior\n"
            f"- User Behavior: {time_slot['insight']}\n"
            f"\n"
            f"Task: Write a 1-2 sentence reason WHY this is the best "
            f"time to post, based on the data signals above.\n"
            f"Required Style: {style}\n"
            f"Keep it under 40 words and be specific about the "
            f"data patterns."
        )
        
        # Student input (simplified version - what the student AI
        # will see during training)
        student_input = (
            f"Day: {day}, Time: {time_slot['window']}, "
            f"Score: {score}, Dominance: {dominance_label}, "
            f"Shape: {graph_shape}, Style: {style}"
        )
        
        # 5. Append to dataset
        dataset.append({
            "day": day,
            "time": time_slot['window'],
            "score": score,
            "dominance": dominance_label,
            "shape": graph_shape,
            "style": style,
            "prompt_for_gemini": prompt_for_gemini,
            "student_input": student_input
        })
        
        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"Progress: {i + 1}/{TOTAL_ROWS} rows generated...")

    # Save to CSV
    df = pd.DataFrame(dataset)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n✓ Done! Created {OUTPUT_FILE} with {len(df)} rows.")
    print(f"Column names: {list(df.columns)}")
    print("\nSample row:")
    print(f"  student_input: {df.iloc[0]['student_input']}")
    sample_prompt = df.iloc[0]['prompt_for_gemini'][:200]
    print(f"  prompt_for_gemini (first 200 chars): {sample_prompt}...")


if __name__ == "__main__":
    generate_dataset()
