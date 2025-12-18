-- postgresql 15+

-- Enable UUID extension for uuid_generate_v4() function
-- This is required for predictions, collection_logs, and other tables
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- tabel kategori
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    category_code VARCHAR(50),
    keywords TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_active ON categories(is_active);

--tabel trends harian
CREATE TABLE IF NOT EXISTS daily_trends (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    region VARCHAR(10) NOT NULL DEFAULT 'ID',
    date DATE NOT NULL,
    day_of_week VARCHAR(10),
    interest_value INTEGER CHECK (interest_value >= 0 AND interest_value <= 100),
    is_holiday BOOLEAN DEFAULT FALSE,
    holiday_name VARCHAR(255),
    trending_event TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword, category, region, date)
);

CREATE INDEX idx_daily_keyword_date ON daily_trends(keyword, date);
CREATE INDEX idx_daily_category ON daily_trends(category);
CREATE INDEX idx_daily_date ON daily_trends(date);
CREATE INDEX idx_daily_day_of_week ON daily_trends(day_of_week);
CREATE INDEX idx_daily_is_holiday ON daily_trends(is_holiday);

--tabel trends hourly
CREATE TABLE IF NOT EXISTS hourly_trends (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    region VARCHAR(10) NOT NULL DEFAULT 'ID',
    datetime TIMESTAMP NOT NULL,
    hour INTEGER CHECK (hour >= 0 AND hour <= 23),
    day_of_week VARCHAR(10),
    interest_value INTEGER CHECK (interest_value >= 0 AND interest_value <= 100),
    is_weekend BOOLEAN,
    time_of_day VARCHAR(20),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword, category, region, datetime)
);

CREATE INDEX idx_hourly_keyword_datetime ON hourly_trends(keyword, datetime);
CREATE INDEX idx_hourly_category ON hourly_trends(category);
CREATE INDEX idx_hourly_datetime ON hourly_trends(datetime);
CREATE INDEX idx_hourly_hour ON hourly_trends(hour);
CREATE INDEX idx_hourly_day_of_week ON hourly_trends(day_of_week);
CREATE INDEX idx_hourly_is_weekend ON hourly_trends(is_weekend);

--tabel related topics
CREATE TABLE IF NOT EXISTS related_topics (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    region VARCHAR(10) NOT NULL DEFAULT 'ID',
    topic_mid VARCHAR(100),
    topic_title VARCHAR(255),
    topic_type VARCHAR(100),
    value INTEGER,
    formatted_value VARCHAR(50),
    link TEXT,
    is_rising BOOLEAN DEFAULT FALSE,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_topics_keyword ON related_topics(keyword);
CREATE INDEX idx_topics_category ON related_topics(category);
CREATE INDEX idx_topics_is_rising ON related_topics(is_rising);

--tabel related query
CREATE TABLE IF NOT EXISTS related_queries (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    region VARCHAR(10) NOT NULL DEFAULT 'ID',
    query VARCHAR(255),
    value INTEGER,
    formatted_value VARCHAR(50),
    link TEXT,
    is_rising BOOLEAN DEFAULT FALSE,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_queries_keyword ON related_queries(keyword);
CREATE INDEX idx_queries_category ON related_queries(category);
CREATE INDEX idx_queries_is_rising ON related_queries(is_rising);

-- tabel predict model
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    prediction_id UUID DEFAULT uuid_generate_v4(),
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    predicted_day VARCHAR(10),
    predicted_hour_start INTEGER,
    predicted_hour_end INTEGER,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    rank INTEGER CHECK (rank >= 1 AND rank <= 3),
    prediction_metadata JSONB,
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_predictions_keyword ON predictions(keyword);
CREATE INDEX idx_predictions_category ON predictions(category);
CREATE INDEX idx_predictions_model ON predictions(model_name);
CREATE INDEX idx_predictions_date ON predictions(prediction_date);

-- tabel log data collection
CREATE TABLE IF NOT EXISTS collection_logs (
    id SERIAL PRIMARY KEY,
    collection_id UUID DEFAULT uuid_generate_v4(),
    data_type VARCHAR(50) NOT NULL,
    keyword VARCHAR(255),
    category VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    records_collected INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_logs_status ON collection_logs(status);
CREATE INDEX idx_logs_data_type ON collection_logs(data_type);
CREATE INDEX idx_logs_started_at ON collection_logs(started_at);

-- tabel performa model
CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    dataset_size INTEGER,
    evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_metrics_model ON model_metrics(model_name);
CREATE INDEX idx_metrics_type ON model_metrics(model_type);
CREATE INDEX idx_metrics_date ON model_metrics(evaluation_date);

--tabel log processing data
CREATE TABLE IF NOT EXISTS processing_logs (
    id SERIAL PRIMARY KEY,
    process_id UUID DEFAULT uuid_generate_v4(),
    process_name VARCHAR(100) NOT NULL,
    process_type VARCHAR(50) NOT NULL,
    input_records INTEGER,
    output_records INTEGER,
    records_cleaned INTEGER,
    records_augmented INTEGER,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    processing_time_seconds FLOAT,
    parameters JSONB,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_processing_status ON processing_logs(status);
CREATE INDEX idx_processing_type ON processing_logs(process_type);
CREATE INDEX idx_processing_started ON processing_logs(started_at);

-- tabel log training model
CREATE TABLE IF NOT EXISTS training_logs (
    id SERIAL PRIMARY KEY,
    training_id UUID DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    model_architecture VARCHAR(100),
    dataset_size INTEGER,
    train_size INTEGER,
    test_size INTEGER,
    hyperparameters JSONB,
    training_metrics JSONB,
    validation_metrics JSONB,
    best_epoch INTEGER,
    total_epochs INTEGER,
    training_time_seconds FLOAT,
    model_path VARCHAR(500),
    onnx_path VARCHAR(500),
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_training_model ON training_logs(model_name);
CREATE INDEX idx_training_status ON training_logs(status);
CREATE INDEX idx_training_started ON training_logs(started_at);

-- tabel log kaggle
CREATE TABLE IF NOT EXISTS experiment_logs (
    id SERIAL PRIMARY KEY,
    experiment_id UUID DEFAULT uuid_generate_v4(),
    experiment_name VARCHAR(200) NOT NULL,
    notebook_name VARCHAR(200),
    kaggle_url TEXT,
    description TEXT,
    model_type VARCHAR(50),
    approach VARCHAR(100),
    results JSONB,
    best_metric_value FLOAT,
    best_metric_name VARCHAR(100),
    is_production BOOLEAN DEFAULT FALSE,
    refactored_to_py BOOLEAN DEFAULT FALSE,
    py_module_path VARCHAR(500),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_experiment_name ON experiment_logs(experiment_name);
CREATE INDEX idx_experiment_model_type ON experiment_logs(model_type);
CREATE INDEX idx_experiment_is_production ON experiment_logs(is_production);
CREATE INDEX idx_experiment_created ON experiment_logs(created_at);

-- tabel test daily
CREATE TABLE IF NOT EXISTS test_daily_trends (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    region VARCHAR(10) NOT NULL DEFAULT 'ID',
    date DATE NOT NULL,
    day_of_week VARCHAR(10),
    interest_value INTEGER CHECK (interest_value >= 0 AND interest_value <= 100),
    is_holiday BOOLEAN DEFAULT FALSE,
    holiday_name VARCHAR(255),
    trending_event TEXT,
    raw_data JSONB,
    test_run_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword, category, region, date, test_run_id)
);

CREATE INDEX idx_test_daily_keyword ON test_daily_trends(keyword);
CREATE INDEX idx_test_daily_test_run ON test_daily_trends(test_run_id);

--tabel test hourly
CREATE TABLE IF NOT EXISTS test_hourly_trends (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    region VARCHAR(10) NOT NULL DEFAULT 'ID',
    datetime TIMESTAMP NOT NULL,
    hour INTEGER CHECK (hour >= 0 AND hour <= 23),
    day_of_week VARCHAR(10),
    interest_value INTEGER CHECK (interest_value >= 0 AND interest_value <= 100),
    is_weekend BOOLEAN,
    time_of_day VARCHAR(20),
    raw_data JSONB,
    test_run_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword, category, region, datetime, test_run_id)
);

CREATE INDEX idx_test_hourly_keyword ON test_hourly_trends(keyword);
CREATE INDEX idx_test_hourly_test_run ON test_hourly_trends(test_run_id);

--tabel test related topics
CREATE TABLE IF NOT EXISTS test_related_topics (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    region VARCHAR(10) NOT NULL DEFAULT 'ID',
    topic_mid VARCHAR(100),
    topic_title VARCHAR(255),
    topic_type VARCHAR(100),
    value INTEGER,
    formatted_value VARCHAR(50),
    link TEXT,
    is_rising BOOLEAN DEFAULT FALSE,
    test_run_id UUID,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_test_topics_test_run ON test_related_topics(test_run_id);

-- tabel related queries
CREATE TABLE IF NOT EXISTS test_related_queries (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    region VARCHAR(10) NOT NULL DEFAULT 'ID',
    query VARCHAR(255),
    value INTEGER,
    formatted_value VARCHAR(50),
    link TEXT,
    is_rising BOOLEAN DEFAULT FALSE,
    test_run_id UUID,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_test_queries_test_run ON test_related_queries(test_run_id);

--tabel metadata
CREATE TABLE IF NOT EXISTS test_runs (
    id SERIAL PRIMARY KEY,
    test_run_id UUID DEFAULT uuid_generate_v4() UNIQUE,
    test_name VARCHAR(200) NOT NULL,
    test_type VARCHAR(50) NOT NULL,
    description TEXT,
    keywords_tested TEXT[],
    categories_tested TEXT[],
    date_range_start DATE,
    date_range_end DATE,
    status VARCHAR(50) NOT NULL,
    records_collected INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_test_runs_status ON test_runs(status);
CREATE INDEX idx_test_runs_type ON test_runs(test_type);
CREATE INDEX idx_test_runs_started ON test_runs(started_at);


-- fungsi update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- trigger untuk tabel categories
CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- trigger untuk tabel experiment_logs
CREATE TRIGGER update_experiment_logs_updated_at BEFORE UPDATE ON experiment_logs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- intial data
INSERT INTO categories (category_name, category_code, keywords) VALUES
('Fashion & Beauty', '/m/032tl', ARRAY['fashion', 'beauty', 'makeup', 'skincare', 'hijab fashion']),
('Food & Culinary', '/m/02wbm', ARRAY['resep', 'kuliner', 'makanan', 'food', 'recipe']),
('Technology & Gadgets', '/m/07c1v', ARRAY['smartphone', 'laptop', 'gadget', 'teknologi', 'hp']),
('E-commerce & Shopping', '/m/0jg24', ARRAY['shopee', 'tokopedia', 'online shopping', 'promo', 'diskon']),
('Entertainment & K-Pop', '/m/02jjt', ARRAY['kpop', 'kdrama', 'film', 'musik', 'entertainment']),
('Travel & Tourism', '/m/07bxq', ARRAY['wisata', 'travel', 'liburan', 'destinasi', 'vacation']),
('Health & Fitness', '/m/0kt51', ARRAY['kesehatan', 'fitness', 'diet', 'olahraga', 'workout']),
('Finance & Investment', '/m/0kpv1', ARRAY['investasi', 'saham', 'crypto', 'keuangan', 'trading']),
('Education & Career', '/m/02j71', ARRAY['pendidikan', 'kuliah', 'beasiswa', 'karir', 'lowongan kerja']),
('Gaming & Esports', '/m/0bzvm2', ARRAY['mobile legends', 'pubg', 'genshin impact', 'gaming', 'esports'])
ON CONFLICT (category_name) DO NOTHING;


-- view: analisis trends harian
CREATE OR REPLACE VIEW v_daily_trends_analysis AS
SELECT 
    dt.*,
    EXTRACT(WEEK FROM dt.date) as week_of_year,
    EXTRACT(MONTH FROM dt.date) as month,
    CASE 
        WHEN dt.day_of_week IN ('Saturday', 'Sunday') THEN TRUE 
        ELSE FALSE 
    END as is_weekend
FROM daily_trends dt;

-- view: analisis trends per jam
CREATE OR REPLACE VIEW v_hourly_trends_analysis AS
SELECT 
    ht.*,
    CASE 
        WHEN ht.hour BETWEEN 0 AND 5 THEN 'night'
        WHEN ht.hour BETWEEN 6 AND 11 THEN 'morning'
        WHEN ht.hour BETWEEN 12 AND 17 THEN 'afternoon'
        WHEN ht.hour BETWEEN 18 AND 23 THEN 'evening'
    END as time_category
FROM hourly_trends ht;

-- view: top 3 prediksi
CREATE OR REPLACE VIEW v_top_predictions AS
SELECT 
    p.keyword,
    p.category,
    p.model_name,
    p.predicted_day,
    p.predicted_hour_start,
    p.predicted_hour_end,
    p.confidence_score,
    p.rank,
    p.prediction_date
FROM predictions p
WHERE p.rank <= 3
ORDER BY p.prediction_date DESC, p.rank ASC;

-- view: status pipeline processing
CREATE OR REPLACE VIEW v_processing_pipeline_status AS
SELECT 
    pl.process_name,
    pl.process_type,
    pl.status,
    pl.input_records,
    pl.output_records,
    pl.processing_time_seconds,
    pl.started_at,
    pl.completed_at
FROM processing_logs pl
ORDER BY pl.started_at DESC;

-- view: summary training model
CREATE OR REPLACE VIEW v_training_summary AS
SELECT 
    tl.model_name,
    tl.model_type,
    tl.dataset_size,
    tl.training_metrics->>'accuracy' as train_accuracy,
    tl.validation_metrics->>'accuracy' as val_accuracy,
    tl.training_time_seconds,
    tl.status,
    tl.started_at,
    tl.completed_at
FROM training_logs tl
ORDER BY tl.started_at DESC;

-- view: tracking eksperimen
CREATE OR REPLACE VIEW v_experiment_tracking AS
SELECT 
    el.experiment_name,
    el.model_type,
    el.approach,
    el.best_metric_name,
    el.best_metric_value,
    el.is_production,
    el.refactored_to_py,
    el.created_at
FROM experiment_logs el
ORDER BY el.best_metric_value DESC NULLS LAST;

-- view: monitoring kesehatan pipeline
CREATE OR REPLACE VIEW v_pipeline_health AS
SELECT 
    'Data Collection' as stage,
    COUNT(*) as total_runs,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_runs,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_runs,
    AVG(CASE WHEN status = 'success' THEN records_collected ELSE NULL END) as avg_records_collected
FROM collection_logs
UNION ALL
SELECT 
    'Data Processing' as stage,
    COUNT(*) as total_runs,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_runs,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_runs,
    AVG(CASE WHEN status = 'success' THEN output_records ELSE NULL END) as avg_records_processed
FROM processing_logs
UNION ALL
SELECT 
    'Model Training' as stage,
    COUNT(*) as total_runs,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_runs,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_runs,
    AVG(CASE WHEN status = 'success' THEN dataset_size ELSE NULL END) as avg_dataset_size
FROM training_logs;

-- view: summary test runs
CREATE OR REPLACE VIEW v_test_runs_summary AS
SELECT 
    tr.test_name,
    tr.test_type,
    tr.status,
    tr.records_collected,
    tr.date_range_start,
    tr.date_range_end,
    tr.started_at,
    tr.completed_at,
    EXTRACT(EPOCH FROM (tr.completed_at - tr.started_at)) as duration_seconds
FROM test_runs tr
ORDER BY tr.started_at DESC;

COMMENT ON TABLE categories IS 'master 10 kategori trending';
COMMENT ON TABLE daily_trends IS 'data trends harian google';
COMMENT ON TABLE hourly_trends IS 'data trends per jam';
COMMENT ON TABLE related_topics IS 'topik terkait trends';
COMMENT ON TABLE related_queries IS 'query pencarian terkait';
COMMENT ON TABLE predictions IS 'prediksi waktu posting';
COMMENT ON TABLE collection_logs IS 'log aktivitas pengumpulan data';
COMMENT ON TABLE model_metrics IS 'metrik performa model';
COMMENT ON TABLE processing_logs IS 'log proses cleaning augmentasi';
COMMENT ON TABLE training_logs IS 'log training model lengkap';
COMMENT ON TABLE experiment_logs IS 'log eksperimen kaggle';
COMMENT ON TABLE test_daily_trends IS 'test data trends harian';
COMMENT ON TABLE test_hourly_trends IS 'test data trends jam';
COMMENT ON TABLE test_related_topics IS 'test data topik terkait';
COMMENT ON TABLE test_related_queries IS 'test data query terkait';
COMMENT ON TABLE test_runs IS 'metadata tracking test runs';
