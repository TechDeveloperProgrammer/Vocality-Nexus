import time
import psutil
import torch
import numpy as np
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

class PerformanceTracker:
    """
    Advanced performance monitoring and telemetry system.
    Tracks system resources, AI model performance, and application metrics.
    """
    
    def __init__(self, session: Session):
        """
        Initialize performance tracking.
        
        :param session: SQLAlchemy database session
        """
        self.session = session
        self.start_time = time.time()
        self.performance_metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'gpu_usage': [],
            'ai_inference_times': []
        }
    
    def track_system_resources(self) -> Dict[str, Any]:
        """
        Track current system resource utilization.
        
        :return: Dictionary of system resource metrics
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        gpu_metrics = self._get_gpu_metrics() if torch.cuda.is_available() else {}
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': cpu_percent,
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            },
            'gpu_metrics': gpu_metrics
        }
    
    def track_ai_model_performance(
        self, 
        model_name: str, 
        inference_time: float, 
        input_size: int, 
        output_size: int
    ) -> None:
        """
        Track AI model inference performance.
        
        :param model_name: Name of the AI model
        :param inference_time: Time taken for inference
        :param input_size: Size of input data
        :param output_size: Size of output data
        """
        self.performance_metrics['ai_inference_times'].append({
            'model_name': model_name,
            'inference_time': inference_time,
            'input_size': input_size,
            'output_size': output_size,
            'timestamp': datetime.now().isoformat()
        })
    
    def generate_performance_report(
        self, 
        duration: timedelta = timedelta(hours=1)
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        :param duration: Time duration for the report
        :return: Performance report dictionary
        """
        current_time = datetime.now()
        
        # System Resource Analysis
        system_resources = self.track_system_resources()
        
        # AI Model Performance Analysis
        ai_performance = self._analyze_ai_performance(duration)
        
        # Bottleneck Detection
        bottlenecks = self._detect_performance_bottlenecks()
        
        return {
            'timestamp': current_time.isoformat(),
            'uptime': time.time() - self.start_time,
            'system_resources': system_resources,
            'ai_performance': ai_performance,
            'performance_bottlenecks': bottlenecks
        }
    
    def _get_gpu_metrics(self) -> Dict[str, Any]:
        """
        Retrieve GPU utilization metrics.
        
        :return: Dictionary of GPU metrics
        """
        try:
            gpu_count = torch.cuda.device_count()
            gpu_metrics = {}
            
            for i in range(gpu_count):
                gpu_metrics[f'gpu_{i}'] = {
                    'name': torch.cuda.get_device_name(i),
                    'memory_allocated': torch.cuda.memory_allocated(i),
                    'memory_cached': torch.cuda.memory_reserved(i),
                    'utilization': torch.cuda.utilization(i)
                }
            
            return gpu_metrics
        except Exception:
            return {}
    
    def _analyze_ai_performance(
        self, 
        duration: timedelta
    ) -> Dict[str, Any]:
        """
        Analyze AI model performance for a given duration.
        
        :param duration: Time duration for analysis
        :return: AI performance metrics
        """
        current_time = datetime.now()
        filtered_inferences = [
            inference for inference in self.performance_metrics['ai_inference_times']
            if current_time - datetime.fromisoformat(inference['timestamp']) <= duration
        ]
        
        if not filtered_inferences:
            return {}
        
        return {
            'total_inferences': len(filtered_inferences),
            'average_inference_time': np.mean([
                inference['inference_time'] for inference in filtered_inferences
            ]),
            'median_inference_time': np.median([
                inference['inference_time'] for inference in filtered_inferences
            ]),
            'model_performance': self._aggregate_model_performance(filtered_inferences)
        }
    
    def _aggregate_model_performance(
        self, 
        inferences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate performance metrics by model.
        
        :param inferences: List of inference metrics
        :return: Aggregated model performance
        """
        model_performance = {}
        
        for inference in inferences:
            model_name = inference['model_name']
            if model_name not in model_performance:
                model_performance[model_name] = {
                    'total_inferences': 0,
                    'total_inference_time': 0,
                    'average_input_size': 0,
                    'average_output_size': 0
                }
            
            model_performance[model_name]['total_inferences'] += 1
            model_performance[model_name]['total_inference_time'] += inference['inference_time']
            model_performance[model_name]['average_input_size'] += inference['input_size']
            model_performance[model_name]['average_output_size'] += inference['output_size']
        
        # Compute averages
        for model_name, metrics in model_performance.items():
            metrics['average_inference_time'] = (
                metrics['total_inference_time'] / metrics['total_inferences']
            )
            metrics['average_input_size'] /= metrics['total_inferences']
            metrics['average_output_size'] /= metrics['total_inferences']
        
        return model_performance
    
    def _detect_performance_bottlenecks(self) -> List[Dict[str, Any]]:
        """
        Detect potential performance bottlenecks.
        
        :return: List of detected bottlenecks
        """
        bottlenecks = []
        
        # CPU Bottleneck Detection
        if psutil.cpu_percent(interval=1) > 80:
            bottlenecks.append({
                'type': 'cpu_overload',
                'severity': 'high',
                'description': 'CPU utilization exceeds 80%'
            })
        
        # Memory Bottleneck Detection
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            bottlenecks.append({
                'type': 'memory_overload',
                'severity': 'high',
                'description': 'Memory utilization exceeds 85%'
            })
        
        # AI Model Bottleneck Detection
        ai_inferences = self.performance_metrics['ai_inference_times']
        if ai_inferences:
            avg_inference_time = np.mean([
                inference['inference_time'] for inference in ai_inferences
            ])
            
            if avg_inference_time > 0.5:  # 500ms threshold
                bottlenecks.append({
                    'type': 'ai_model_slowdown',
                    'severity': 'medium',
                    'description': f'Average AI inference time: {avg_inference_time:.2f}s'
                })
        
        return bottlenecks
