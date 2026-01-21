# T5 Fine-tuning Training Report

## Model Information

| Parameter              | Value                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------- |
| **Base Model**         | google/flan-t5-large                                                                              |
| **Task**               | Text2Text Generation (Posting Time Recommendation)                                                |
| **Fine-tuning Method** | QLoRA (4-bit quantization + LoRA)                                                                 |
| **Repository**         | [raflisbk/t5-posting-time-summarizer](https://huggingface.co/raflisbk/t5-posting-time-summarizer) |

---

## Training Configuration

### LoRA Settings

| Parameter            | Value                      |
| -------------------- | -------------------------- |
| LoRA Rank (r)        | 64                         |
| LoRA Alpha           | 128                        |
| LoRA Dropout         | 0.05                       |
| Target Modules       | q, v, k, o                 |
| Trainable Parameters | 37,748,736 (4.6% of total) |

### Training Hyperparameters

| Parameter             | Value            |
| --------------------- | ---------------- |
| Epochs                | 20               |
| Batch Size            | 4                |
| Gradient Accumulation | 8                |
| Effective Batch Size  | 32               |
| Learning Rate         | 0.0001           |
| LR Scheduler          | Cosine           |
| Warmup Ratio          | 10%              |
| Optimizer             | paged_adamw_8bit |
| Weight Decay          | 0.01             |
| Max Grad Norm         | 1.0              |

### Data Configuration

| Parameter          | Value      |
| ------------------ | ---------- |
| Total Samples      | 6,119      |
| Training Samples   | 5,508      |
| Validation Samples | 611        |
| Max Input Length   | 128 tokens |
| Max Target Length  | 256 tokens |

---

## Training Progress

### Loss Curve

| Step | Epoch | Training Loss | Validation Loss |
| ---- | ----- | ------------- | --------------- |
| 173  | 1     | 3.1318        | 2.2022          |
| 346  | 2     | 1.9770        | 1.5081          |
| 519  | 3     | 1.5308        | 1.2518          |
| 692  | 4     | 1.4030        | 1.1437          |
| 865  | 5     | 1.2855        | 1.0745          |
| 1038 | 6     | 1.2394        | 1.0247          |
| 1211 | 7     | 1.1640        | 0.9960          |
| 1384 | 8     | 1.1282        | 0.9723          |
| 1557 | 9     | 1.1098        | 0.9415          |
| 1730 | 10    | 1.0751        | 0.9291          |
| 1903 | 11    | 1.0420        | 0.9107          |
| 2076 | 12    | 1.0254        | 0.8978          |
| 2249 | 13    | 1.0203        | 0.8933          |
| 2422 | 14    | 0.9968        | 0.8839          |
| 2595 | 15    | 0.9971        | 0.8764          |
| 2768 | 16    | 0.9856        | 0.8726          |
| 2941 | 17    | 0.9751        | 0.8713          |
| 3114 | 18    | 0.9682        | 0.8702          |
| 3287 | 19    | 0.9612        | 0.8695          |
| 3460 | 20    | 0.9594        | 0.8693          |

### Key Metrics

| Metric                    | Value               |
| ------------------------- | ------------------- |
| **Final Training Loss**   | 0.9594              |
| **Final Validation Loss** | 0.8693              |
| **Total Improvement**     | 60.5% (2.20 → 0.87) |
| **Training Time**         | ~8 hours            |
| **GPU**                   | Tesla T4 (15.83 GB) |

---

## Evaluation Results

| Metric                  | Value         |
| ----------------------- | ------------- |
| eval_loss               | 0.8693        |
| eval_runtime            | 74.30 seconds |
| eval_samples_per_second | 8.22          |
| eval_steps_per_second   | 2.06          |

---

## Sample Predictions

### Sample 1

**Input:**

```
Day: Tuesday, Time: 22:00 - 00:00, Score: 73, Dominance: Unrivaled, Shape: Sustained Plateau, Style: Urgent (Creating FOMO/Action)
```

**Expected:**

```
STRIKE NOW: Tuesday late night (22:00-00:00) crushes competitors with a 73/100 score-26 points ahead...
```

**Predicted:**

```
Don't miss this window! Tuesday late night (22:00-00:00) crushes competitors with a 73/100 score-nearly double the runner-up. Night owls are actively scrolling before bed, creating a sustained engagement plateau you can't afford to miss.
```

### Sample 2

**Input:**

```
Day: Thursday, Time: 09:00 - 12:00, Score: 97, Dominance: Clear Lead, Shape: Sustained Plateau, Style: Advisory (Consultative, Helpful)
```

**Expected:**

```
Thursday mid-mornings (9am-12pm) capture professionals during their most active work breaks, with a...
```

**Predicted:**

```
Thursday mid-morning (9 AM-12 PM) captures professionals during their first work break, delivering a commanding 97/100 engagement score-significantly outperforming alternatives. This sustained plateau period ensures consistent visibility as your audience actively checks social media between tasks.
```

### Sample 3

**Input:**

```
Day: Tuesday, Time: 13:00 - 17:00, Score: 86, Dominance: Unrivaled, Shape: Sharp Spike, Style: Detailed (Deep dive analysis)
```

**Expected:**

```
Tuesday afternoon's 86/100 score with Sharp Spike behavior indicates a concentrated engagement windo...
```

**Predicted:**

```
Tuesday's 13:00-17:00 window demonstrates unrivaled dominance with an 86/100 score-nearly double the runner-up's 41-driven by a sharp spike in moderate work-hour activity as professionals seek content breaks during the afternoon lull.
```

---

## Model Files

### HuggingFace Hub Structure

```
raflisbk/t5-posting-time-summarizer/
├── adapter_config.json          # LoRA configuration
├── adapter_model.safetensors    # LoRA weights (151 MB)
├── tokenizer.json
├── tokenizer_config.json
├── special_tokens_map.json
├── spiece.model
└── merged/                      # Full merged model
    ├── config.json
    ├── model.safetensors
    └── tokenizer files...
```

---

## Usage

### Load LoRA Adapter

```python
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from peft import PeftModel

base_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large")
model = PeftModel.from_pretrained(base_model, "raflisbk/t5-posting-time-summarizer")
tokenizer = AutoTokenizer.from_pretrained("raflisbk/t5-posting-time-summarizer")
```

### Load Merged Model (Faster)

```python
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

model = AutoModelForSeq2SeqLM.from_pretrained(
    "raflisbk/t5-posting-time-summarizer",
    subfolder="merged"
)
tokenizer = AutoTokenizer.from_pretrained("raflisbk/t5-posting-time-summarizer")

# Optimize for inference
model = model.to_bettertransformer()
```

### Inference

```python
def generate_recommendation(input_text):
    inputs = tokenizer(f"summarize : {input_text}", return_tensors="pt")
    outputs = model.generate(**inputs, max_length=256, num_beams=4)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Example
result = generate_recommendation(
    "Day: Monday, Time: 09:00 - 12:00, Score: 95, Dominance: Unrivaled, Shape: Sustained Plateau, Style: Storytelling"
)
print(result)
```

---

## Conclusions

1. **Training Success**: Model converged well with validation loss decreasing from 2.20 to 0.87 (60.5% reduction)
2. **No Overfitting**: Training loss and validation loss remained close throughout training
3. **Quality Output**: Sample predictions show coherent, relevant, and stylistically appropriate responses
4. **Ready for Production**: Model is available on HuggingFace Hub for deployment

---

_Report generated: 2026-01-16_
