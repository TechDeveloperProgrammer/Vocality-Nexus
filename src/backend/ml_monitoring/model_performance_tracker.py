import os
import time
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import torch
import torch.nn as nn
import pandas as pd
from sklearn.metrics import (
    mean_squared_error, 
    mean_absolute_error, 
    r2_score, 
    precision_score, 
    recall_score, 
    f1_score
)
import mlflow
import mlflow.pytorch

class ModelPerformanceTracker:
    """
    Comprehensive machine learning model performance monitoring and tracking system
    """
    
    def __init__(self, 
                 model_name: str, 
                 log_dir: str = 'model_logs',
                 mlflow_tracking_uri: Optional[str] = None):
        """
        Initialize performance tracker
        
        :param model_name: Name of the ML model
        :param log_dir: Directory for storing performance logs
        :param mlflow_tracking_uri: Optional MLflow tracking server URI
        """
        self.model_name = model_name
        self.log_dir = log_dir
        self.logger = logging.getLogger(f'{model_name}_performance_tracker')
        
        # Create log directory if not exists
        os.makedirs(log_dir, exist_ok=True)
        
        # MLflow configuration
        if mlflow_tracking_uri:
            mlflow.set_tracking_uri(mlflow_tracking_uri)
        mlflow.set_experiment(model_name)
        
        # Performance metrics storage
        self.performance_history: List[Dict[str, Any]] = []

    def track_inference_performance(self, 
                                    model: nn.Module, 
                                    dataloader: torch.utils.data.DataLoader,
                                    task_type: str = 'regression') -> Dict[str, float]:
        """
        Track model inference performance
        
        :param model: PyTorch model
        :param dataloader: DataLoader with test/validation data
        :param task_type: Type of ML task (regression/classification)
        :return: Performance metrics dictionary
        """
        model.eval()
        device = next(model.parameters()).device
        
        start_time = time.time()
        
        true_labels = []
        predicted_labels = []
        inference_times = []
        
        with torch.no_grad():
            for batch in dataloader:
                # Prepare batch data
                inputs, labels = batch
                inputs, labels = inputs.to(device), labels.to(device)
                
                # Measure inference time
                batch_start_time = time.time()
                outputs = model(inputs)
                batch_inference_time = time.time() - batch_start_time
                inference_times.append(batch_inference_time)
                
                # Process predictions based on task type
                if task_type == 'regression':
                    predictions = outputs.cpu().numpy()
                    true_labels.extend(labels.cpu().numpy())
                    predicted_labels.extend(predictions)
                elif task_type == 'classification':
                    predictions = torch.argmax(outputs, dim=1).cpu().numpy()
                    true_labels.extend(labels.cpu().numpy())
                    predicted_labels.extend(predictions)
        
        total_inference_time = time.time() - start_time
        
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics(
            true_labels, 
            predicted_labels, 
            task_type, 
            inference_times
        )
        
        # Log metrics with MLflow
        with mlflow.start_run():
            for key, value in metrics.items():
                mlflow.log_metric(key, value)
        
        # Store performance history
        self._store_performance_history(metrics)
        
        return metrics

    def _calculate_performance_metrics(self, 
                                       true_labels: List[float], 
                                       predicted_labels: List[float], 
                                       task_type: str,
                                       inference_times: List[float]) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics
        
        :param true_labels: Ground truth labels
        :param predicted_labels: Model predictions
        :param task_type: Type of ML task
        :param inference_times: List of inference times
        :return: Performance metrics dictionary
        """
        metrics = {
            'total_samples': len(true_labels),
            'avg_inference_time_ms': np.mean(inference_times) * 1000,
            'total_inference_time_ms': np.sum(inference_times) * 1000,
            'inference_time_std_ms': np.std(inference_times) * 1000
        }
        
        if task_type == 'regression':
            metrics.update({
                'mse': mean_squared_error(true_labels, predicted_labels),
                'mae': mean_absolute_error(true_labels, predicted_labels),
                'r2_score': r2_score(true_labels, predicted_labels)
            })
        
        elif task_type == 'classification':
            metrics.update({
                'precision': precision_score(true_labels, predicted_labels, average='weighted'),
                'recall': recall_score(true_labels, predicted_labels, average='weighted'),
                'f1_score': f1_score(true_labels, predicted_labels, average='weighted')
            })
        
        return metrics

    def _store_performance_history(self, metrics: Dict[str, float]):
        """
        Store performance metrics in history
        
        :param metrics: Performance metrics dictionary
        """
        metrics['timestamp'] = time.time()
        self.performance_history.append(metrics)
        
        # Persist performance history
        history_file = os.path.join(
            self.log_dir, 
            f'{self.model_name}_performance_history.json'
        )
        
        with open(history_file, 'w') as f:
            json.dump(self.performance_history, f, indent=2)

    def detect_performance_drift(self, 
                                 window_size: int = 5, 
                                 drift_threshold: float = 0.2) -> Dict[str, bool]:
        """
        Detect performance drift across different metrics
        
        :param window_size: Number of recent performance records to analyze
        :param drift_threshold: Threshold for detecting significant drift
        :return: Dictionary indicating drift for different metrics
        """
        if len(self.performance_history) < window_size:
            return {}
        
        recent_metrics = self.performance_history[-window_size:]
        drift_status = {}
        
        # Drift detection for different metrics
        drift_metrics = {
            'regression': ['mse', 'mae', 'r2_score'],
            'classification': ['precision', 'recall', 'f1_score']
        }
        
        for metric_type, metrics in drift_metrics.items():
            for metric in metrics:
                metric_values = [record.get(metric, 0) for record in recent_metrics if metric in record]
                
                if len(metric_values) == window_size:
                    drift = np.std(metric_values) / np.mean(metric_values)
                    drift_status[metric] = drift > drift_threshold
        
        return drift_status

    def export_performance_report(self, 
                                  output_format: str = 'json') -> str:
        """
        Export comprehensive performance report
        
        :param output_format: Output format (json/csv/html)
        :return: Performance report
        """
        if output_format == 'json':
            return json.dumps(self.performance_history, indent=2)
        
        elif output_format == 'csv':
            df = pd.DataFrame(self.performance_history)
            return df.to_csv(index=False)
        
        elif output_format == 'html':
            df = pd.DataFrame(self.performance_history)
            return df.to_html(index=False)
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

def create_model_performance_tracker(
    model_name: str, 
    log_dir: str = 'model_logs', 
    mlflow_tracking_uri: Optional[str] = None
) -> ModelPerformanceTracker:
    """
    Factory method to create model performance tracker
    
    :param model_name: Name of the ML model
    :param log_dir: Directory for storing performance logs
    :param mlflow_tracking_uri: Optional MLflow tracking server URI
    :return: Configured model performance tracker
    """
    return ModelPerformanceTracker(
        model_name, 
        log_dir, 
        mlflow_tracking_uri
    )
