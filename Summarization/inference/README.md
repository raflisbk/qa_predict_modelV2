# Inference Module

This module provides production inference for the T5 summarization model with traceback capability.

## Files

- **`model_loader.py`** - Loads the fine-tuned T5 model (Stage 2) with singleton pattern
- **`summarizer.py`** - Main inference logic for generating summaries from aggregation data
- **`requirements.txt`** - Python dependencies

## Usage

### Basic Usage

```python
from summarizer import generate_summary

# From aggregation service
hourly_summary = {
    "day": "Monday",
    "time_window": "17:00 - 20:00",
    "score": 85.2,
    "daily_avg": 69.0,
    "peak_hour": 18,
    "peak_value": 89.0,
    "hourly": "06(52), 07(58), 08(62), ..., 23(55)"
}

# Generate summary
summary = generate_summary(hourly_summary)
print(summary)
```

**Output:**

```
Monday evenings capture professionals during post-work leisure,
with dominant 85/100 engagement as users actively scroll after dinner.

Traceback:
- Peak: 18:00 (89), +29% vs daily avg (69)
- vs Morning 06:00-09:00 (avg 60): +42% improvement
- vs Afternoon 12:00-15:00 (avg 75): +13% improvement
```

### Advanced Usage

```python
from summarizer import Summarizer

# Initialize summarizer (loads model once)
summarizer = Summarizer()

# Generate multiple summaries
for summary_data in hourly_summaries:
    result = summarizer.generate(summary_data)
    print(result)
```

## Integration with Aggregation Service

Add this to your aggregation service after `process_data()`:

```python
from summarization.inference.summarizer import generate_summary

# In your endpoint handler
processed_data = process_data(timeline_data)

# Generate summary for top recommendation
if processed_data.get("hourly_summary"):
    top_summary = processed_data["hourly_summary"][0]  # Rank 1
    narrative = generate_summary(top_summary)

    # Add to response
    processed_data["summary"] = narrative
```

## Model Path

By default, the model is loaded from:

```
../phase2/models/stage2_merged/
```

To use a different path:

```python
from model_loader import get_model_loader

loader = get_model_loader(model_path="/path/to/your/model")
```

## Requirements

- Python 3.8+
- GPU recommended (but CPU works)
- ~4GB RAM for model inference

## Installation

```bash
cd inference
pip install -r requirements.txt
```
