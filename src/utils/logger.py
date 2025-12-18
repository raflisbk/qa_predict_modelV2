"""
Logging utility for tracking all pipeline processes to database.

This module provides decorators and context managers to automatically log:
- Data collection activities
- Data processing steps
- Model training runs
- Kaggle experiments

All logs are stored in PostgreSQL for tracking and monitoring.
"""

import time
import uuid
import json
from functools import wraps
from contextlib import contextmanager
from typing import Dict, Any, Optional
from datetime import datetime

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class ProcessLogger:
    """Logger for data processing pipeline"""
    
    @staticmethod
    def log_processing(
        process_name: str,
        process_type: str,
        input_records: int,
        output_records: int,
        records_cleaned: int = 0,
        records_augmented: int = 0,
        status: str = "success",
        error_message: Optional[str] = None,
        processing_time: float = 0.0,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """Log data processing activity to database"""
        session = SessionLocal()
        try:
            query = text("""
                INSERT INTO processing_logs (
                    process_id, process_name, process_type, input_records, 
                    output_records, records_cleaned, records_augmented, 
                    status, error_message, processing_time_seconds, parameters, 
                    started_at, completed_at
                ) VALUES (
                    :process_id, :process_name, :process_type, :input_records,
                    :output_records, :records_cleaned, :records_augmented,
                    :status, :error_message, :processing_time, :parameters,
                    :started_at, :completed_at
                )
            """)
            
            session.execute(query, {
                "process_id": str(uuid.uuid4()),
                "process_name": process_name,
                "process_type": process_type,
                "input_records": input_records,
                "output_records": output_records,
                "records_cleaned": records_cleaned,
                "records_augmented": records_augmented,
                "status": status,
                "error_message": error_message,
                "processing_time": processing_time,
                "parameters": json.dumps(parameters) if parameters else None,
                "started_at": datetime.now(),
                "completed_at": datetime.now()
            })
            session.commit()
            logger.info(f"Logged processing: {process_name} - {status}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log processing: {e}")
        finally:
            session.close()


class TrainingLogger:
    """Logger for model training runs"""
    
    @staticmethod
    def log_training(
        model_name: str,
        model_type: str,
        model_architecture: str,
        dataset_size: int,
        train_size: int,
        test_size: int,
        hyperparameters: Dict[str, Any],
        training_metrics: Dict[str, float],
        validation_metrics: Dict[str, float],
        best_epoch: int = 0,
        total_epochs: int = 0,
        training_time: float = 0.0,
        model_path: Optional[str] = None,
        onnx_path: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        """Log model training run to database"""
        session = SessionLocal()
        try:
            query = text("""
                INSERT INTO training_logs (
                    training_id, model_name, model_type, model_architecture,
                    dataset_size, train_size, test_size, hyperparameters,
                    training_metrics, validation_metrics, best_epoch, total_epochs,
                    training_time_seconds, model_path, onnx_path, status,
                    error_message, started_at, completed_at
                ) VALUES (
                    :training_id, :model_name, :model_type, :model_architecture,
                    :dataset_size, :train_size, :test_size, :hyperparameters,
                    :training_metrics, :validation_metrics, :best_epoch, :total_epochs,
                    :training_time, :model_path, :onnx_path, :status,
                    :error_message, :started_at, :completed_at
                )
            """)
            
            session.execute(query, {
                "training_id": str(uuid.uuid4()),
                "model_name": model_name,
                "model_type": model_type,
                "model_architecture": model_architecture,
                "dataset_size": dataset_size,
                "train_size": train_size,
                "test_size": test_size,
                "hyperparameters": json.dumps(hyperparameters),
                "training_metrics": json.dumps(training_metrics),
                "validation_metrics": json.dumps(validation_metrics),
                "best_epoch": best_epoch,
                "total_epochs": total_epochs,
                "training_time": training_time,
                "model_path": model_path,
                "onnx_path": onnx_path,
                "status": status,
                "error_message": error_message,
                "started_at": datetime.now(),
                "completed_at": datetime.now()
            })
            session.commit()
            logger.info(f"Logged training: {model_name} - {status}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log training: {e}")
        finally:
            session.close()


class ExperimentLogger:
    """Logger for Kaggle notebook experiments"""
    
    @staticmethod
    def log_experiment(
        experiment_name: str,
        notebook_name: Optional[str] = None,
        kaggle_url: Optional[str] = None,
        description: Optional[str] = None,
        model_type: Optional[str] = None,
        approach: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None,
        best_metric_value: Optional[float] = None,
        best_metric_name: Optional[str] = None,
        is_production: bool = False,
        notes: Optional[str] = None
    ):
        """Log Kaggle experiment to database"""
        session = SessionLocal()
        try:
            query = text("""
                INSERT INTO experiment_logs (
                    experiment_id, experiment_name, notebook_name, kaggle_url,
                    description, model_type, approach, results, best_metric_value,
                    best_metric_name, is_production, refactored_to_py, notes,
                    created_at, updated_at
                ) VALUES (
                    :experiment_id, :experiment_name, :notebook_name, :kaggle_url,
                    :description, :model_type, :approach, :results, :best_metric_value,
                    :best_metric_name, :is_production, :refactored_to_py, :notes,
                    :created_at, :updated_at
                )
            """)
            
            session.execute(query, {
                "experiment_id": str(uuid.uuid4()),
                "experiment_name": experiment_name,
                "notebook_name": notebook_name,
                "kaggle_url": kaggle_url,
                "description": description,
                "model_type": model_type,
                "approach": approach,
                "results": json.dumps(results) if results else None,
                "best_metric_value": best_metric_value,
                "best_metric_name": best_metric_name,
                "is_production": is_production,
                "refactored_to_py": False,
                "notes": notes,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            session.commit()
            logger.info(f"Logged experiment: {experiment_name}")
            return session.execute(text("SELECT lastval()")).scalar()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log experiment: {e}")
            return None
        finally:
            session.close()
    
    @staticmethod
    def mark_refactored(experiment_id: int, py_module_path: str):
        """Mark experiment as refactored to .py module"""
        session = SessionLocal()
        try:
            query = text("""
                UPDATE experiment_logs 
                SET refactored_to_py = TRUE, py_module_path = :py_module_path, updated_at = :updated_at
                WHERE id = :experiment_id
            """)
            session.execute(query, {
                "experiment_id": experiment_id,
                "py_module_path": py_module_path,
                "updated_at": datetime.now()
            })
            session.commit()
            logger.info(f"Marked experiment {experiment_id} as refactored")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to mark refactored: {e}")
        finally:
            session.close()


# Decorators for automatic logging
def log_processing_step(process_name: str, process_type: str):
    """Decorator to automatically log data processing steps"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            input_records = kwargs.get('input_records', 0)
            
            try:
                result = func(*args, **kwargs)
                processing_time = time.time() - start_time
                
                # Extract output info from result
                output_records = result.get('output_records', 0) if isinstance(result, dict) else 0
                records_cleaned = result.get('records_cleaned', 0) if isinstance(result, dict) else 0
                records_augmented = result.get('records_augmented', 0) if isinstance(result, dict) else 0
                
                ProcessLogger.log_processing(
                    process_name=process_name,
                    process_type=process_type,
                    input_records=input_records,
                    output_records=output_records,
                    records_cleaned=records_cleaned,
                    records_augmented=records_augmented,
                    status="success",
                    processing_time=processing_time,
                    parameters=kwargs
                )
                return result
            except Exception as e:
                processing_time = time.time() - start_time
                ProcessLogger.log_processing(
                    process_name=process_name,
                    process_type=process_type,
                    input_records=input_records,
                    output_records=0,
                    status="failed",
                    error_message=str(e),
                    processing_time=processing_time,
                    parameters=kwargs
                )
                raise
        return wrapper
    return decorator


@contextmanager
def training_context(model_name: str, model_type: str, **kwargs):
    """Context manager for model training with automatic logging"""
    start_time = time.time()
    training_info = {
        "model_name": model_name,
        "model_type": model_type,
        **kwargs
    }
    
    try:
        yield training_info
        training_time = time.time() - start_time
        
        TrainingLogger.log_training(
            model_name=model_name,
            model_type=model_type,
            training_time=training_time,
            status="success",
            **training_info
        )
    except Exception as e:
        training_time = time.time() - start_time
        TrainingLogger.log_training(
            model_name=model_name,
            model_type=model_type,
            training_time=training_time,
            status="failed",
            error_message=str(e),
            **training_info
        )
        raise
