-- ============================================
-- Monitoring Dashboard Queries
-- ============================================

-- Query 1: Pipeline Health Overview
SELECT * FROM v_pipeline_health;

-- Query 2: Recent Data Collection Status
SELECT 
    data_type,
    keyword,
    category,
    status,
    records_collected,
    started_at,
    completed_at,
    EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
FROM collection_logs
ORDER BY started_at DESC
LIMIT 20;

-- Query 3: Data Processing Pipeline Status
SELECT * FROM v_processing_pipeline_status LIMIT 20;

-- Query 4: Model Training Summary
SELECT * FROM v_training_summary LIMIT 10;

-- Query 5: Best Performing Experiments
SELECT 
    experiment_name,
    model_type,
    approach,
    best_metric_name,
    best_metric_value,
    is_production,
    refactored_to_py,
    created_at
FROM v_experiment_tracking
LIMIT 10;

-- Query 6: Failed Processes (Last 24 hours)
SELECT 
    'Collection' as process_type,
    data_type as process_name,
    status,
    error_message,
    started_at
FROM collection_logs
WHERE status = 'failed' AND started_at > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT 
    'Processing' as process_type,
    process_name,
    status,
    error_message,
    started_at
FROM processing_logs
WHERE status = 'failed' AND started_at > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT 
    'Training' as process_type,
    model_name as process_name,
    status,
    error_message,
    started_at
FROM training_logs
WHERE status = 'failed' AND started_at > NOW() - INTERVAL '24 hours'
ORDER BY started_at DESC;

-- Query 7: Model Performance Comparison
SELECT 
    tl.model_name,
    tl.model_type,
    tl.validation_metrics->>'accuracy' as accuracy,
    tl.validation_metrics->>'top3_accuracy' as top3_accuracy,
    tl.training_time_seconds,
    tl.dataset_size,
    tl.completed_at
FROM training_logs tl
WHERE tl.status = 'success'
ORDER BY (tl.validation_metrics->>'accuracy')::float DESC;

-- Query 8: Data Quality Metrics
SELECT 
    process_type,
    AVG(CASE WHEN output_records > 0 THEN (output_records::float / input_records::float) * 100 ELSE 0 END) as avg_retention_rate,
    AVG(CASE WHEN records_cleaned > 0 THEN (records_cleaned::float / input_records::float) * 100 ELSE 0 END) as avg_cleaning_rate,
    AVG(processing_time_seconds) as avg_processing_time,
    COUNT(*) as total_runs
FROM processing_logs
WHERE status = 'success'
GROUP BY process_type;

-- Query 9: Experiment Refactoring Status
SELECT 
    COUNT(*) as total_experiments,
    SUM(CASE WHEN refactored_to_py THEN 1 ELSE 0 END) as refactored_count,
    SUM(CASE WHEN is_production THEN 1 ELSE 0 END) as production_count,
    ROUND(SUM(CASE WHEN refactored_to_py THEN 1 ELSE 0 END)::numeric / COUNT(*)::numeric * 100, 2) as refactoring_percentage
FROM experiment_logs;

-- Query 10: Daily Trends Data Coverage
SELECT 
    category,
    COUNT(DISTINCT keyword) as unique_keywords,
    COUNT(DISTINCT date) as days_covered,
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    AVG(interest_value) as avg_interest
FROM daily_trends
GROUP BY category
ORDER BY unique_keywords DESC;

-- Query 11: Hourly Trends Data Coverage
SELECT 
    category,
    COUNT(DISTINCT keyword) as unique_keywords,
    COUNT(DISTINCT DATE(datetime)) as days_covered,
    MIN(datetime) as earliest_datetime,
    MAX(datetime) as latest_datetime,
    AVG(interest_value) as avg_interest
FROM hourly_trends
GROUP BY category
ORDER BY unique_keywords DESC;

-- Query 12: Top Predictions by Category
SELECT 
    p.category,
    p.model_name,
    p.predicted_day,
    p.predicted_hour_start,
    p.predicted_hour_end,
    p.confidence_score,
    p.prediction_date
FROM predictions p
WHERE p.rank = 1
ORDER BY p.prediction_date DESC, p.category;
