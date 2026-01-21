"""
Stage 2 Training Data Generator

Transforms hourly Google Trends data into training pairs for fine-tuning
the summarization model with traceback capability.

Input: hourly_trends_*.csv
Output: stage2_training_data.csv with input_text and target_text columns
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Time window definitions (3-hour slots)
TIME_WINDOWS = [
    ("00:00 - 03:00", "Late Night", range(0, 3)),
    ("03:00 - 06:00", "Early Morning", range(3, 6)),
    ("06:00 - 09:00", "Morning", range(6, 9)),
    ("09:00 - 12:00", "Late Morning", range(9, 12)),
    ("12:00 - 15:00", "Afternoon", range(12, 15)),
    ("15:00 - 18:00", "Late Afternoon", range(15, 18)),
    ("18:00 - 21:00", "Evening", range(18, 21)),
    ("21:00 - 00:00", "Night", range(21, 24)),
]

# Narrative templates for different patterns
NARRATIVE_TEMPLATES = [
    "{day} {period_name} captures users during {activity}, with a commanding {score}/100 engagement score.",
    "{day}'s {period_name} window ({time_window}) shows strong performance with {score}/100, capturing audiences during {activity}.",
    "The {time_window} slot on {day} delivers {score}/100 engagement, reaching users during {activity}.",
]

# Activity descriptions by time period
ACTIVITIES = {
    "Late Night": ["pre-sleep scrolling sessions", "late-night browsing", "quiet nighttime engagement"],
    "Early Morning": ["early riser phone checks", "pre-dawn scrolling", "quiet morning routines"],
    "Morning": ["morning commute browsing", "breakfast-time scrolling", "early work breaks"],
    "Late Morning": ["mid-morning work breaks", "coffee break scrolling", "pre-lunch browsing"],
    "Afternoon": ["lunch break research", "afternoon work lulls", "midday content consumption"],
    "Late Afternoon": ["post-lunch browsing", "afternoon break scrolling", "end-of-workday checks"],
    "Evening": ["post-dinner leisure time", "evening relaxation browsing", "peak leisure engagement"],
    "Night": ["pre-sleep content consumption", "nighttime wind-down scrolling", "evening entertainment time"],
}


def load_hourly_data(csv_path: str) -> pd.DataFrame:
    """Load and preprocess hourly trends data."""
    logger.info(f"Loading data from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Filter out rows with no data
    df = df[df['interest_value'] > 0]
    
    logger.info(f"Loaded {len(df)} rows with valid data")
    logger.info(f"Keywords: {df['keyword'].unique().tolist()}")
    logger.info(f"Days: {df['day_of_week'].unique().tolist()}")
    
    return df


def get_window_for_hour(hour: int) -> Tuple[str, str, range]:
    """Get the time window info for a given hour."""
    for window, name, hours in TIME_WINDOWS:
        if hour in hours:
            return window, name, hours
    return TIME_WINDOWS[0]  # Default to first window


def calculate_window_stats(df_day: pd.DataFrame, window_hours: range) -> Dict:
    """Calculate statistics for a time window."""
    window_data = df_day[df_day['hour'].isin(window_hours)]
    
    if window_data.empty:
        return None
    
    return {
        "avg": round(window_data['interest_value'].mean(), 1),
        "peak_hour": int(window_data.loc[window_data['interest_value'].idxmax(), 'hour']),
        "peak_value": round(window_data['interest_value'].max(), 1),
    }


def generate_traceback(
    best_window: str,
    best_period: str,
    window_stats: Dict,
    daily_avg: float,
    comparison_windows: List[Dict]
) -> str:
    """Generate traceback analysis text."""
    lines = ["\nTraceback:"]
    
    # Peak hour info
    peak_diff = round((window_stats['peak_value'] - daily_avg) / daily_avg * 100) if daily_avg > 0 else 0
    lines.append(f"- Peak: {window_stats['peak_hour']:02d}:00 ({window_stats['peak_value']}), {peak_diff:+d}% vs daily avg ({daily_avg})")
    
    # Comparisons with other windows
    for comp in comparison_windows[:3]:  # Max 3 comparisons
        if comp['avg'] > 0:
            improvement = round((window_stats['avg'] - comp['avg']) / comp['avg'] * 100)
            if improvement > 0:
                lines.append(f"- vs {comp['name']} {comp['window']} (avg {comp['avg']}): +{improvement}% improvement")
    
    return "\n".join(lines)


def generate_training_sample(
    keyword: str,
    day: str,
    df_day: pd.DataFrame
) -> Dict:
    """Generate a single training sample from daily data."""
    
    # Calculate stats for all windows
    window_stats_list = []
    for window, period_name, hours in TIME_WINDOWS:
        stats = calculate_window_stats(df_day, hours)
        if stats:
            stats['window'] = window
            stats['name'] = period_name
            window_stats_list.append(stats)
    
    if not window_stats_list:
        return None
    
    # Find best window
    best = max(window_stats_list, key=lambda x: x['avg'])
    
    # Calculate daily average
    daily_avg = round(df_day['interest_value'].mean(), 1)
    
    # Create hourly string
    hourly_str = ", ".join([
        f"{int(row['hour']):02d}({int(row['interest_value'])})"
        for _, row in df_day.sort_values('hour').iterrows()
    ])
    
    # Create input text
    input_text = (
        f"Day: {day}, Time: {best['window']}, Score: {round(best['avg'])}\n"
        f"Hourly: {hourly_str}\n"
        f"Daily Avg: {daily_avg}, Peak: {best['peak_hour']:02d}({best['peak_value']})"
    )
    
    # Generate narrative
    template = random.choice(NARRATIVE_TEMPLATES)
    activity = random.choice(ACTIVITIES.get(best['name'], ["active browsing"]))
    narrative = template.format(
        day=day,
        period_name=best['name'].lower(),
        time_window=best['window'],
        score=round(best['avg']),
        activity=activity
    )
    
    # Generate traceback (compare with other windows)
    other_windows = [w for w in window_stats_list if w['window'] != best['window']]
    traceback = generate_traceback(
        best['window'],
        best['name'],
        best,
        daily_avg,
        sorted(other_windows, key=lambda x: x['avg'], reverse=True)
    )
    
    # Combine for target text
    target_text = narrative + traceback
    
    return {
        "input_text": input_text,
        "target_text": target_text
    }


def generate_dataset(df: pd.DataFrame) -> List[Dict]:
    """Generate full training dataset from hourly data."""
    samples = []
    
    # Group by keyword and day
    for keyword in df['keyword'].unique():
        df_keyword = df[df['keyword'] == keyword]
        
        for day in df_keyword['day_of_week'].unique():
            df_day = df_keyword[df_keyword['day_of_week'] == day]
            
            # Need at least some hours for meaningful analysis
            if len(df_day) < 6:
                continue
            
            sample = generate_training_sample(keyword, day, df_day)
            if sample:
                samples.append(sample)
                logger.debug(f"Generated sample for {keyword} - {day}")
    
    logger.info(f"Generated {len(samples)} training samples")
    return samples


def main():
    """Main entry point."""
    # Find the hourly trends CSV
    data_dir = Path(__file__).parent
    csv_files = list(data_dir.glob("hourly_trends*.csv"))
    
    if not csv_files:
        logger.error("No hourly_trends*.csv file found!")
        return
    
    csv_path = csv_files[0]
    logger.info(f"Using data file: {csv_path}")
    
    # Load data
    df = load_hourly_data(str(csv_path))
    
    # Generate training samples
    samples = generate_dataset(df)
    
    if not samples:
        logger.error("No training samples generated!")
        return
    
    # Save to CSV
    output_path = data_dir / "stage2_training_data.csv"
    df_output = pd.DataFrame(samples)
    df_output.to_csv(output_path, index=False)
    
    logger.info(f"Saved {len(samples)} samples to {output_path}")
    
    # Print sample
    print("\n" + "="*60)
    print("SAMPLE INPUT:")
    print(samples[0]['input_text'])
    print("\nSAMPLE TARGET:")
    print(samples[0]['target_text'])
    print("="*60)


if __name__ == "__main__":
    main()
