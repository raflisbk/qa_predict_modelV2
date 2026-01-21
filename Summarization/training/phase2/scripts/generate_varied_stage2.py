"""
Generate varied Stage 2 training data with narrative Insight section.
Uses diverse language patterns instead of rigid templates.
"""

import pandas as pd
import random
import csv
from pathlib import Path

# Narrative opening patterns (varied)
NARRATIVE_OPENINGS = [
    "{day}'s {time} window delivers an impressive {score}/100 engagement score",
    "The data reveals that {day} {time} achieves a remarkable {score}/100",
    "Analysis shows {day} {time} as a high-performing slot with {score}/100",
    "{day} between {time} stands out with {score}/100 engagement",
    "Your audience is most active on {day} during {time}, scoring {score}/100",
    "Peak performance on {day} occurs at {time} with {score}/100",
    "The {time} window on {day} captures strong engagement at {score}/100",
    "{day}'s sweet spot is {time}, hitting {score}/100 engagement",
    "Data indicates {day} {time} yields {score}/100 audience engagement",
    "The optimal posting window on {day} is {time} with {score}/100",
]

NARRATIVE_CONTEXTS = [
    "reaching users during their {activity}",
    "capturing audiences when they're {activity}",
    "connecting with users as they {activity}",
    "engaging viewers during {activity}",
    "tapping into peak {activity} moments",
    "aligning with natural {activity} patterns",
]

ACTIVITIES = {
    "Morning Rush": ["checking phones before work", "commuting", "starting their day", "morning routines"],
    "Mid-Morning": ["work breaks", "mid-morning browsing", "coffee break scrolling", "productive morning hours"],
    "Lunch Break": ["midday rest", "lunch browsing", "taking a break", "midday downtime"],
    "Afternoon Lull": ["post-lunch browsing", "afternoon breaks", "relaxed afternoon moments", "work wind-down"],
    "Late Afternoon": ["end-of-day scrolling", "pre-dinner browsing", "afternoon leisure", "transitioning from work"],
    "Commute Hours": ["transit time", "commuting home", "travel browsing", "on-the-go scrolling"],
    "Prime Time": ["leisure hours", "evening relaxation", "peak entertainment time", "after-dinner browsing"],
    "Late Night": ["night owl scrolling", "bedtime browsing", "quiet evening hours", "late-night unwinding"],
    "Overnight": ["late-night dedication", "night owl activity", "early morning quiet", "minimal but focused browsing"],
}

# Insight patterns (narrative, accessible)
PEAK_INSIGHTS = [
    "The highest engagement peaks at {hour} with {value} points, outperforming the {avg} daily average by {diff}%.",
    "Activity reaches its zenith at {hour} ({value} points), which is {diff}% stronger than the typical daily performance of {avg}.",
    "Your audience is most responsive at {hour}, showing {value} engagement points — that's {diff}% above the daily norm of {avg}.",
    "The data shows a clear peak at {hour} with {value} points, representing a {diff}% boost over the {avg} average.",
    "At {hour}, engagement hits {value} points, a notable {diff}% improvement compared to the {avg} daily baseline.",
    "Peak moment occurs at {hour} reaching {value} — significantly higher ({diff}%) than the usual {avg} average.",
]

COMPARISON_INSIGHTS = [
    "Posting during this window outperforms {period} ({window}) by {improvement}%, making it a stronger choice for visibility.",
    "Compared to {period} hours ({window}), this slot delivers {improvement}% better engagement — ideal for reaching active audiences.",
    "This window beats the {period} slot ({window}) by {improvement}%, giving your content a clear advantage.",
    "You'll see {improvement}% more engagement here than during {period} ({window}), a meaningful difference for content reach.",
    "The data favors this time over {period} ({window}) with a {improvement}% edge in audience interaction.",
    "Choosing this slot over {period} ({window}) means {improvement}% higher engagement potential.",
]

RECOMMENDATION_INSIGHTS = [
    "This makes it an excellent window for important announcements or high-priority content.",
    "Consider scheduling your key posts during this peak engagement period.",
    "Leverage this high-activity window for maximum content visibility.",
    "This time slot offers the best opportunity to connect with your audience.",
    "Prioritize this window for content that requires strong initial engagement.",
    "Use this insight to optimize your posting strategy for better reach.",
]

def get_period_name(time_window: str) -> str:
    """Determine period name from time window."""
    start_hour = int(time_window.split(":")[0])
    if 0 <= start_hour < 6:
        return "Overnight"
    elif 6 <= start_hour < 9:
        return "Morning Rush"
    elif 9 <= start_hour < 12:
        return "Mid-Morning"
    elif 12 <= start_hour < 13:
        return "Lunch Break"
    elif 13 <= start_hour < 15:
        return "Afternoon Lull"
    elif 15 <= start_hour < 17:
        return "Late Afternoon"
    elif 17 <= start_hour < 19:
        return "Commute Hours"
    elif 19 <= start_hour < 22:
        return "Prime Time"
    else:
        return "Late Night"

def generate_input_text(day: str, time: str, score: int, hourly_data: str, daily_avg: float, peak_hour: int, peak_value: int) -> str:
    """Generate input text for training."""
    return f"""Day: {day}, Time: {time}, Score: {score}
Hourly: {hourly_data}
Daily Avg: {daily_avg}, Peak: {peak_hour:02d}({peak_value})"""

def generate_narrative(day: str, time: str, score: int, period_name: str) -> str:
    """Generate varied narrative opening."""
    opening = random.choice(NARRATIVE_OPENINGS).format(day=day, time=time, score=score)
    activity = random.choice(ACTIVITIES.get(period_name, ["active browsing"]))
    context = random.choice(NARRATIVE_CONTEXTS).format(activity=activity)
    return f"{opening}, {context}."

def generate_insight(peak_hour: int, peak_value: int, daily_avg: float, comparisons: list) -> str:
    """Generate narrative insight section."""
    lines = ["\nInsight:"]
    
    # Peak insight
    peak_diff = round((peak_value - daily_avg) / daily_avg * 100) if daily_avg > 0 else 0
    hour_str = f"{peak_hour}:00" if peak_hour >= 10 else f"{peak_hour} AM"
    peak_line = random.choice(PEAK_INSIGHTS).format(
        hour=hour_str,
        value=peak_value,
        avg=round(daily_avg, 1),
        diff=abs(peak_diff)
    )
    lines.append(f"- {peak_line}")
    
    # Comparison insights (max 2)
    for comp in comparisons[:2]:
        comp_line = random.choice(COMPARISON_INSIGHTS).format(
            period=comp['period'].lower(),
            window=comp['window'],
            improvement=comp['improvement']
        )
        lines.append(f"- {comp_line}")
    
    # Optional recommendation
    if random.random() > 0.5:
        lines.append(f"- {random.choice(RECOMMENDATION_INSIGHTS)}")
    
    return "\n".join(lines)

def generate_hourly_data(base_avg: float = 70) -> tuple:
    """Generate realistic hourly engagement data."""
    hours = []
    values = []
    
    # Generate with realistic patterns
    for h in range(24):
        # More entries for busier hours
        entries = random.randint(1, 4)
        for _ in range(entries):
            # Add variation based on time of day
            if 9 <= h <= 21:  # Active hours
                val = int(base_avg + random.gauss(10, 15))
            else:  # Quiet hours
                val = int(base_avg + random.gauss(-10, 12))
            val = max(20, min(100, val))
            hours.append(h)
            values.append(val)
    
    # Format as hourly string
    hourly_str = ", ".join([f"{h:02d}({v})" for h, v in zip(hours, values)])
    
    # Calculate stats
    daily_avg = round(sum(values) / len(values), 1)
    peak_idx = values.index(max(values))
    peak_hour = hours[peak_idx]
    peak_value = values[peak_idx]
    
    return hourly_str, daily_avg, peak_hour, peak_value

def generate_comparisons(best_score: int, best_period: str) -> list:
    """Generate comparison data for other time windows."""
    other_periods = [p for p in ACTIVITIES.keys() if p != best_period]
    comparisons = []
    
    for period in random.sample(other_periods, min(3, len(other_periods))):
        # Generate lower score for comparison
        other_score = max(40, best_score - random.randint(5, 25))
        improvement = round((best_score - other_score) / other_score * 100)
        
        # Generate time window for period
        if period == "Morning Rush":
            window = "06:00-09:00"
        elif period == "Mid-Morning":
            window = "09:00-12:00"
        elif period == "Lunch Break":
            window = "12:00-13:00"
        elif period == "Afternoon Lull":
            window = "13:00-15:00"
        elif period == "Late Afternoon":
            window = "15:00-17:00"
        elif period == "Commute Hours":
            window = "17:00-19:00"
        elif period == "Prime Time":
            window = "19:00-22:00"
        elif period == "Late Night":
            window = "22:00-00:00"
        else:
            window = "00:00-06:00"
        
        if improvement > 0:
            comparisons.append({
                'period': period,
                'window': window,
                'improvement': improvement
            })
    
    return sorted(comparisons, key=lambda x: x['improvement'])

def main():
    """Generate varied training data."""
    output_path = Path(__file__).parent.parent / "data" / "processed" / "stage2_training_varied.csv"
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    time_windows = [
        "00:00 - 06:00", "06:00 - 09:00", "09:00 - 12:00", "12:00 - 13:00",
        "13:00 - 15:00", "15:00 - 18:00", "18:00 - 21:00", "21:00 - 00:00"
    ]
    
    samples = []
    target_count = 500  # Generate 500 varied samples
    
    print(f"Generating {target_count} varied training samples...")
    
    for i in range(target_count):
        day = random.choice(days)
        time = random.choice(time_windows)
        score = random.randint(70, 98)
        period_name = get_period_name(time.split(" - ")[0])
        
        # Generate hourly data
        hourly_str, daily_avg, peak_hour, peak_value = generate_hourly_data(base_avg=score - 10)
        
        # Generate comparisons
        comparisons = generate_comparisons(score, period_name)
        
        # Generate input
        input_text = generate_input_text(day, time, score, hourly_str, daily_avg, peak_hour, peak_value)
        
        # Generate narrative + insight
        narrative = generate_narrative(day, time, score, period_name)
        insight = generate_insight(peak_hour, peak_value, daily_avg, comparisons)
        target_text = narrative + insight
        
        samples.append({
            "input_text": input_text,
            "target_text": target_text
        })
        
        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{target_count} samples...")
    
    # Save to CSV
    df = pd.DataFrame(samples)
    df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
    print(f"\nSaved {len(samples)} samples to: {output_path}")
    
    # Show sample
    print("\n" + "="*60)
    print("SAMPLE OUTPUT:")
    print("="*60)
    sample = random.choice(samples)
    print(f"\nINPUT:\n{sample['input_text']}")
    print(f"\nTARGET:\n{sample['target_text']}")

if __name__ == "__main__":
    main()
