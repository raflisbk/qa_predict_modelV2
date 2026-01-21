# Best Time Post - Social Media Posting Time Recommendation System

Sistem rekomendasi waktu posting terbaik menggunakan Google Trends data dan T5 summarization model.

## 📁 Structure

```
best-time-post/
├── README.md                     # This file
│
├── training/                     # Model training
│   ├── phase1/                   # Stage 1: Pattern-based narrative
│   │   ├── data/
│   │   ├── notebooks/
│   │   ├── models/merged/
│   │   └── TRAINING_REPORT.md
│   └── phase2/                   # Stage 2: Traceback capability
│       ├── data/
│       ├── scripts/
│       ├── notebooks/
│       └── models/
│
├── inference/                    # Production inference
│   ├── model_loader.py
│   ├── summarizer.py
│   ├── requirements.txt
│   └── README.md
│
└── agregasi/                     # Aggregation service (API)
    ├── app/
    ├── test/
    ├── Dockerfile
    ├── docker-compose.yml
    └── README.md
```

## 🚀 Quick Start

### 1. Aggregation Service (API)

```bash
cd agregasi
docker-compose up -d
```

API akan berjalan di `http://localhost:8000`

**Endpoint:**

- `GET /predict?keyword={keyword}` - Get time recommendation
- `GET /health` - Health check

### 2. Model Inference

```bash
cd inference
pip install -r requirements.txt
```

```python
from summarizer import generate_summary

hourly_summary = {
    "day": "Monday",
    "time_window": "17:00 - 20:00",
    "score": 85.2,
    "daily_avg": 69.0,
    "peak_hour": 18,
    "peak_value": 89.0,
    "hourly": "06(52), 07(58), ..."
}

summary = generate_summary(hourly_summary)
print(summary)
```

### 3. Training (Optional)

Untuk re-train model, lihat:

- **Phase 1**: `training/phase1/notebooks/train_stage1.ipynb`
- **Phase 2**: `training/phase2/notebooks/train_stage2.ipynb`

## 📊 Pipeline Flow

```
User Request (keyword)
        ↓
Agregasi API (fetch + aggregate)
        ↓
hourly_summary [day, time, score, hourly data]
        ↓
Inference Model (generate narrative + traceback)
        ↓
Response: "Monday evenings capture users..."
          + Traceback analysis
```

## 🔧 Components

| Component     | Purpose                                          | Tech Stack                |
| ------------- | ------------------------------------------------ | ------------------------- |
| **Agregasi**  | Fetch Google Trends data, aggregate hourly stats | FastAPI, Redis, pytrends  |
| **Inference** | Generate summaries from hourly data              | T5, Transformers, PyTorch |
| **Training**  | Fine-tune T5 for narrative + traceback           | Jupyter, PEFT, QLoRA      |

## 📖 Documentation

- [Agregasi Service](agregasi/README.md) - API documentation
- [Inference Module](inference/README.md) - Model usage guide
- [Phase 1 Training](training/phase1/TRAINING_REPORT.md) - Stage 1 report
- [Phase 2 Training](training/phase2/README.md) - Stage 2 guide

## 🛠️ Development

### Run Tests

```bash
cd agregasi
pytest
```

### Model Architecture

- **Base**: `google/flan-t5-large`
- **Fine-tuning**: QLoRA (4-bit quantization)
- **Stage 1**: 6,119 pattern samples → Narrative generation
- **Stage 2**: 321 hourly samples → Traceback analysis

## 📝 Example Output

**Input:**

```
Keyword: makeup
Day: Monday
Time: 17:00-20:00
```

**Output:**

```
Monday evenings capture consumers during post-dinner leisure,
with dominant 85/100 engagement as users actively scroll after work.

Traceback:
- Peak: 18:00 (89), +29% vs daily avg (69)
- vs Morning 06:00-09:00 (avg 60): +42% improvement
- vs Afternoon 12:00-15:00 (avg 75): +13% improvement
```

## 🔗 Related

- Google Trends API: [pytrends](https://github.com/GeneralMills/pytrends)
- Model Hub: [HuggingFace](https://huggingface.co/raflisbk/t5-posting-time-summarizer)

---

**Note:** Rename folder `Summarization` → `best-time-post` secara manual setelah reorganisasi selesai.
