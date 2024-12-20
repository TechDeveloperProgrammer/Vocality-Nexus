import os
import sys
import psutil
import platform
import socket
import json
import logging
from typing import Dict, Any, List
import subprocess
import GPUtil
import redis
import sqlite3
import requests
from datetime import datetime

class SystemHealthChecker:
    """
    Comprehensive system health monitoring and diagnostic utility
    """
    
    def __init__(self, config_path: str = 'config/health_check_config.json'):
        """
        Initialize health checker with configuration
        
        :param config_path: Path to health check configuration
        """
        self.logger = self._setup_logger()
        self.config = self._load_config(config_path)
        
    def _setup_logger(self) -> logging.Logger:
        """
        Configure logging for health checks
        
        :return: Configured logger
        """
        logger = logging.getLogger('SystemHealthChecker')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load health check configuration
        
        :param config_path: Path to configuration file
        :return: Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found at {config_path}. Using default settings.")
            return {
                'critical_services': ['postgresql', 'redis', 'nginx'],
                'resource_thresholds': {
                    'cpu_usage': 80,
                    'memory_usage': 90,
                    'disk_usage': 85
                }
            }

    def check_system_resources(self) -> Dict[str, Any]:
        """
        Check system-wide resource utilization
        
        :return: Resource utilization report
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        gpu_report = self._check_gpu_resources()
        
        return {
            'cpu_usage': cpu_percent,
            'memory': {
                'total': memory.total / (1024 ** 3),  # GB
                'available': memory.available / (1024 ** 3),  # GB
                'percent': memory.percent
            },
            'disk': {
                'total': disk.total / (1024 ** 3),  # GB
                'free': disk.free / (1024 ** 3),  # GB
                'percent': disk.percent
            },
            'gpu': gpu_report
        }

    def _check_gpu_resources(self) -> List[Dict[str, Any]]:
        """
        Check GPU resources and utilization
        
        :return: GPU resource report
        """
        try:
            gpus = GPUtil.getGPUs()
            return [
                {
                    'id': gpu.id,
                    'name': gpu.name,
                    'memory_total': gpu.memoryTotal,
                    'memory_used': gpu.memoryUsed,
                    'memory_free': gpu.memoryFree,
                    'gpu_utilization': gpu.load * 100,
                    'memory_utilization': gpu.memoryUtil * 100
                }
                for gpu in gpus
            ]
        except Exception as e:
            self.logger.warning(f"GPU resource check failed: {e}")
            return []

    def check_critical_services(self) -> Dict[str, bool]:
        """
        Check status of critical services
        
        :return: Service health status
        """
        services = self.config.get('critical_services', [])
        service_status = {}
        
        for service in services:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service], 
                    capture_output=True, 
                    text=True
                )
                service_status[service] = result.stdout.strip() == 'active'
            except Exception as e:
                self.logger.error(f"Error checking service {service}: {e}")
                service_status[service] = False
        
        return service_status

    def check_database_connections(self) -> Dict[str, bool]:
        """
        Check connections to various databases
        
        :return: Database connection status
        """
        db_status = {}
        
        # PostgreSQL connection check
        try:
            # Placeholder for actual PostgreSQL connection details
            conn = sqlite3.connect('test.db')
            conn.close()
            db_status['sqlite'] = True
        except Exception as e:
            self.logger.error(f"SQLite connection error: {e}")
            db_status['sqlite'] = False
        
        # Redis connection check
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=0)
            redis_client.ping()
            db_status['redis'] = True
        except Exception as e:
            self.logger.error(f"Redis connection error: {e}")
            db_status['redis'] = False
        
        return db_status

    def check_network_connectivity(self) -> Dict[str, bool]:
        """
        Check network connectivity and external service accessibility
        
        :return: Network connectivity report
        """
        network_status = {
            'local_network': self._check_local_network(),
            'internet_connectivity': self._check_internet_connectivity(),
            'external_services': self._check_external_services()
        }
        
        return network_status

    def _check_local_network(self) -> bool:
        """
        Check local network connectivity
        
        :return: Local network status
        """
        try:
            socket.create_connection(('127.0.0.1', 80), timeout=2)
            return True
        except (socket.error, socket.timeout):
            return False

    def _check_internet_connectivity(self) -> bool:
        """
        Check internet connectivity
        
        :return: Internet connectivity status
        """
        try:
            socket.create_connection(('8.8.8.8', 53), timeout=3)
            return True
        except (socket.error, socket.timeout):
            return False

    def _check_external_services(self) -> Dict[str, bool]:
        """
        Check status of external services
        
        :return: External service connectivity
        """
        external_services = {
            'github': 'https://github.com',
            'google': 'https://www.google.com'
        }
        
        service_status = {}
        
        for name, url in external_services.items():
            try:
                response = requests.get(url, timeout=5)
                service_status[name] = response.status_code == 200
            except requests.RequestException:
                service_status[name] = False
        
        return service_status

    def generate_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive system health report
        
        :return: Detailed health report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'os': platform.platform(),
                'python_version': platform.python_version()
            },
            'resources': self.check_system_resources(),
            'services': self.check_critical_services(),
            'databases': self.check_database_connections(),
            'network': self.check_network_connectivity()
        }
        
        # Log warnings for critical thresholds
        self._log_health_warnings(report)
        
        return report

    def _log_health_warnings(self, report: Dict[str, Any]):
        """
        Log warnings for critical resource thresholds
        
        :param report: Health report dictionary
        """
        thresholds = self.config.get('resource_thresholds', {})
        
        # CPU Usage Warning
        if report['resources']['cpu_usage'] > thresholds.get('cpu_usage', 80):
            self.logger.warning(f"High CPU Usage: {report['resources']['cpu_usage']}%")
        
        # Memory Usage Warning
        if report['resources']['memory']['percent'] > thresholds.get('memory_usage', 90):
            self.logger.warning(f"High Memory Usage: {report['resources']['memory']['percent']}%")
        
        # Disk Usage Warning
        if report['resources']['disk']['percent'] > thresholds.get('disk_usage', 85):
            self.logger.warning(f"High Disk Usage: {report['resources']['disk']['percent']}%")

def main():
    """
    Main execution for system health check
    """
    health_checker = SystemHealthChecker()
    report = health_checker.generate_health_report()
    
    # Print or save report
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
