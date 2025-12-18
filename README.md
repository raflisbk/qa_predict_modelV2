# Best Time Post POC

Sistem prediksi waktu posting optimal menggunakan Google Trends data dan Machine Learning untuk memberikan rekomendasi hari dan jam terbaik untuk posting konten di social media atau e-commerce.

## 🎯 Fitur Utama

- **Data Collection**: Fetching data Google Trends (daily & hourly) menggunakan Apify
- **3 Model ML**: LightGBM, LSTM, dan NeuralProphet untuk prediksi optimal
- **ONNX Inference**: Fast inference dengan ONNX Runtime
- **Top-3 Recommendations**: Memberikan 3 rekomendasi waktu posting terbaik dengan confidence score
- **10 Kategori Trending**: Fashion, Food, Tech, E-commerce, Entertainment, Travel, Health, Finance, Education, Gaming

## 📋 Prerequisites

- Python 3.9+
- Docker & Docker Compose
- Apify API Token
- PostgreSQL (via Docker)

## 🚀 Quick Start

### 1. Clone & Setup Environment

```bash
cd "d:\Subek\project\Draft\UKI\Best time post v2"

# Copy environment template
copy .env.example .env

# Edit .env dan masukkan Apify API token
notepad .env
```

### 2. Start PostgreSQL Database

```bash
docker-compose up -d
```

Database akan running di `localhost:5432` dengan PgAdmin di `localhost:5050`

### 3. Install Dependencies

```bash
# Create virtual environment (optional)
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run Data Collection

```bash
# Collect data untuk semua kategori
python src/data/collect_data.py

# Atau collect untuk kategori spesifik
python src/data/collect_data.py --category "Fashion & Beauty"
```

### 5. Train Models

```bash
# Train semua model
python src/models/train_all.py

# Atau train model spesifik
python src/models/lightgbm/train.py
python src/models/lstm/train.py
python src/models/neuralprophet/train.py
```

### 6. Get Predictions

```bash
# Get top-3 recommendations
python src/inference/predict.py --keyword "fashion" --category "Fashion & Beauty"
```

## 📁 Project Structure (CCDS-compliant)

```
best-time-post-v2/
├── config/
│   ├── categories.json          # Top 10 categories
│   └── indonesia_events.json    # Holidays & events
├── data/
│   ├── raw/                     # Raw Apify responses
│   ├── processed/               # Cleaned data
│   ├── interim/                 # Intermediate data
│   └── external/                # External data sources
├── database/
│   └── schema.sql               # PostgreSQL schema
├── src/
│   ├── data/                    # Data collection scripts
│   ├── features/                # Feature engineering
│   ├── models/
│   │   ├── lightgbm/           # LightGBM model
│   │   ├── lstm/               # LSTM model
│   │   ├── neuralprophet/      # NeuralProphet model
│   │   └── ensemble/           # Ensemble logic
│   ├── inference/              # ONNX inference
│   ├── evaluation/             # Model evaluation
│   └── database/               # Database operations
├── models/                      # Trained models
│   ├── lightgbm/
│   ├── lstm/
│   ├── neuralprophet/
│   └── onnx/                   # ONNX exported models
├── notebooks/                   # Jupyter notebooks
├── tests/                       # Unit tests
├── reports/
│   ├── figures/                # Visualizations
│   └── metrics/                # Model metrics
├── logs/                        # Application logs
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## 🔧 Configuration

Edit `.env` file:

```env
# Apify
APIFY_API_TOKEN=your_token_here

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=best_time_post
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Google Trends
GOOGLE_TRENDS_REGION=ID
GOOGLE_TRENDS_LANGUAGE=id
```

## 📊 Output Format

```json
[
  {
    "rank": 1,
    "day": "Wednesday",
    "time_window": "14:00 - 17:00",
    "confidence_score": 0.87
  },
  {
    "rank": 2,
    "day": "Thursday",
    "time_window": "10:00 - 13:00",
    "confidence_score": 0.82
  },
  {
    "rank": 3,
    "day": "Monday",
    "time_window": "15:00 - 18:00",
    "confidence_score": 0.76
  }
]
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## 📈 Model Performance

| Model         | Top-1 Accuracy | Top-3 Accuracy | Inference Time |
| ------------- | -------------- | -------------- | -------------- |
| LightGBM      | TBD            | TBD            | TBD ms         |
| LSTM          | TBD            | TBD            | TBD ms         |
| NeuralProphet | TBD            | TBD            | TBD ms         |

## 🗓️ Timeline

- **Day 1 (17 Des)**: Data collection & preprocessing
- **Day 2 (18 Des)**: Model development & training
- **Day 3 (19 Des)**: Integration, testing & documentation

## 📝 License

MIT License

## 👥 Contributors

- Subek Team
