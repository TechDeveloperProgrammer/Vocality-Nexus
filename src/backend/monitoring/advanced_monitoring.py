import os
import time
import json
import logging
from typing import Dict, Any, Optional, List, Union
import psutil
import GPUtil
import requests
import asyncio
import aiohttp
import prometheus_client
from prometheus_client import Gauge, Counter, Summary
import schedule
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import slack_sdk
import telegram_send

class AdvancedMonitoringSystem:
    """
    Comprehensive system and application monitoring utility
    Supports multiple monitoring and alerting strategies
    """
    
    def __init__(self, 
                 service_name: str = 'vocality_nexus',
                 monitoring_dir: str = 'monitoring_logs',
                 prometheus_port: int = 8000):
        """
        Initialize advanced monitoring system
        
        :param service_name: Name of the monitored service
        :param monitoring_dir: Directory for storing monitoring logs
        :param prometheus_port: Port for Prometheus metrics server
        """
        # Logging configuration
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Monitoring directory
        self.monitoring_dir = monitoring_dir
        os.makedirs(monitoring_dir, exist_ok=True)
        
        # Service name
        self.service_name = service_name
        
        # Prometheus metrics
        self._setup_prometheus_metrics(prometheus_port)
        
        # Alert configurations
        self.alert_configs: Dict[str, Dict[str, Any]] = {}
        
        # Notification channels
        self.notification_channels: Dict[str, Any] = {}

    def _setup_prometheus_metrics(self, port: int):
        """
        Set up Prometheus metrics
        
        :param port: Port for Prometheus metrics server
        """
        # System metrics
        self.cpu_usage = Gauge(
            'system_cpu_usage', 
            'System CPU Usage Percentage',
            ['service']
        )
        
        self.memory_usage = Gauge(
            'system_memory_usage', 
            'System Memory Usage Percentage',
            ['service']
        )
        
        self.disk_usage = Gauge(
            'system_disk_usage', 
            'System Disk Usage Percentage',
            ['service', 'mount_point']
        )
        
        self.gpu_usage = Gauge(
            'system_gpu_usage', 
            'GPU Usage Percentage',
            ['service', 'gpu_name']
        )
        
        # Application metrics
        self.request_counter = Counter(
            'application_requests_total', 
            'Total Application Requests',
            ['service', 'endpoint', 'method', 'status']
        )
        
        self.request_latency = Summary(
            'application_request_latency_seconds', 
            'Request Latency',
            ['service', 'endpoint', 'method']
        )
        
        # Start Prometheus metrics server
        prometheus_client.start_http_server(port)

    def collect_system_metrics(self) -> Dict[str, Any]:
        """
        Collect comprehensive system metrics
        
        :return: System metrics dictionary
        """
        metrics = {
            'timestamp': time.time(),
            'cpu': {
                'usage': psutil.cpu_percent(interval=1),
                'cores': psutil.cpu_count(logical=False)
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'used': psutil.virtual_memory().used,
                'percent': psutil.virtual_memory().percent
            },
            'disk': [
                {
                    'mountpoint': part.mountpoint,
                    'total': part.total,
                    'used': part.used,
                    'percent': part.percent
                } for part in psutil.disk_partitions()
            ],
            'network': {
                'connections': len(psutil.net_connections()),
                'io_counters': dict(psutil.net_io_counters()._asdict())
            }
        }
        
        # GPU metrics
        try:
            gpus = GPUtil.getGPUs()
            metrics['gpu'] = [
                {
                    'name': gpu.name,
                    'memory_total': gpu.memoryTotal,
                    'memory_used': gpu.memoryUsed,
                    'memory_free': gpu.memoryFree,
                    'gpu_load': gpu.load * 100
                } for gpu in gpus
            ]
        except Exception:
            metrics['gpu'] = []
        
        # Update Prometheus metrics
        self.cpu_usage.labels(service=self.service_name).set(metrics['cpu']['usage'])
        self.memory_usage.labels(service=self.service_name).set(metrics['memory']['percent'])
        
        for disk in metrics['disk']:
            self.disk_usage.labels(
                service=self.service_name, 
                mount_point=disk['mountpoint']
            ).set(disk['percent'])
        
        for gpu in metrics['gpu']:
            self.gpu_usage.labels(
                service=self.service_name, 
                gpu_name=gpu['name']
            ).set(gpu['gpu_load'])
        
        return metrics

    def log_system_metrics(self, metrics: Optional[Dict[str, Any]] = None):
        """
        Log system metrics to file
        
        :param metrics: Optional pre-collected metrics
        """
        metrics = metrics or self.collect_system_metrics()
        
        log_file = os.path.join(
            self.monitoring_dir, 
            f'system_metrics_{int(time.time())}.json'
        )
        
        with open(log_file, 'w') as f:
            json.dump(metrics, f, indent=2)

    def configure_alert(self, 
                        name: str, 
                        metric: str, 
                        threshold: float, 
                        comparison: str = 'gt'):
        """
        Configure alert for specific metric
        
        :param name: Alert name
        :param metric: Metric to monitor
        :param threshold: Threshold value
        :param comparison: Comparison type (gt/lt/eq)
        """
        self.alert_configs[name] = {
            'metric': metric,
            'threshold': threshold,
            'comparison': comparison
        }

    def check_alerts(self, metrics: Optional[Dict[str, Any]] = None):
        """
        Check configured alerts
        
        :param metrics: Optional pre-collected metrics
        :return: Triggered alerts
        """
        metrics = metrics or self.collect_system_metrics()
        triggered_alerts = []
        
        for name, config in self.alert_configs.items():
            metric_value = self._get_nested_dict_value(metrics, config['metric'])
            
            if metric_value is not None:
                alert_triggered = (
                    (config['comparison'] == 'gt' and metric_value > config['threshold']) or
                    (config['comparison'] == 'lt' and metric_value < config['threshold']) or
                    (config['comparison'] == 'eq' and metric_value == config['threshold'])
                )
                
                if alert_triggered:
                    alert_details = {
                        'name': name,
                        'metric': config['metric'],
                        'current_value': metric_value,
                        'threshold': config['threshold']
                    }
                    triggered_alerts.append(alert_details)
                    self._send_alert_notifications(alert_details)
        
        return triggered_alerts

    def _get_nested_dict_value(self, 
                                dictionary: Dict[str, Any], 
                                key_path: str) -> Optional[Any]:
        """
        Retrieve nested dictionary value
        
        :param dictionary: Input dictionary
        :param key_path: Dot-separated key path
        :return: Value or None
        """
        keys = key_path.split('.')
        current = dictionary
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        
        return current

    def configure_email_alerts(self, 
                                smtp_server: str, 
                                smtp_port: int, 
                                sender_email: str, 
                                sender_password: str, 
                                recipients: List[str]):
        """
        Configure email alert notifications
        
        :param smtp_server: SMTP server address
        :param smtp_port: SMTP server port
        :param sender_email: Sender email address
        :param sender_password: Sender email password
        :param recipients: List of recipient email addresses
        """
        self.notification_channels['email'] = {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'sender_email': sender_email,
            'sender_password': sender_password,
            'recipients': recipients
        }

    def configure_slack_alerts(self, slack_token: str, channel: str):
        """
        Configure Slack alert notifications
        
        :param slack_token: Slack API token
        :param channel: Slack channel
        """
        self.notification_channels['slack'] = {
            'client': slack_sdk.WebClient(token=slack_token),
            'channel': channel
        }

    def configure_telegram_alerts(self, bot_token: str, chat_id: str):
        """
        Configure Telegram alert notifications
        
        :param bot_token: Telegram bot token
        :param chat_id: Telegram chat ID
        """
        self.notification_channels['telegram'] = {
            'bot_token': bot_token,
            'chat_id': chat_id
        }

    def _send_alert_notifications(self, alert_details: Dict[str, Any]):
        """
        Send alert notifications through configured channels
        
        :param alert_details: Alert details dictionary
        """
        # Email notifications
        if 'email' in self.notification_channels:
            self._send_email_alert(alert_details)
        
        # Slack notifications
        if 'slack' in self.notification_channels:
            self._send_slack_alert(alert_details)
        
        # Telegram notifications
        if 'telegram' in self.notification_channels:
            self._send_telegram_alert(alert_details)

    def _send_email_alert(self, alert_details: Dict[str, Any]):
        """
        Send email alert
        
        :param alert_details: Alert details dictionary
        """
        config = self.notification_channels['email']
        
        try:
            msg = MIMEMultipart()
            msg['From'] = config['sender_email']
            msg['To'] = ', '.join(config['recipients'])
            msg['Subject'] = f"Alert: {alert_details['name']}"
            
            body = json.dumps(alert_details, indent=2)
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                server.starttls()
                server.login(config['sender_email'], config['sender_password'])
                server.send_message(msg)
        
        except Exception as e:
            self.logger.error(f"Email alert failed: {e}")

    def _send_slack_alert(self, alert_details: Dict[str, Any]):
        """
        Send Slack alert
        
        :param alert_details: Alert details dictionary
        """
        config = self.notification_channels['slack']
        
        try:
            config['client'].chat_postMessage(
                channel=config['channel'],
                text=f"*Alert: {alert_details['name']}*\n```{json.dumps(alert_details, indent=2)}```"
            )
        
        except Exception as e:
            self.logger.error(f"Slack alert failed: {e}")

    def _send_telegram_alert(self, alert_details: Dict[str, Any]):
        """
        Send Telegram alert
        
        :param alert_details: Alert details dictionary
        """
        config = self.notification_channels['telegram']
        
        try:
            telegram_send.send(
                conf=None,
                token=config['bot_token'],
                text=f"*Alert: {alert_details['name']}*\n```{json.dumps(alert_details, indent=2)}```",
                chat_id=config['chat_id']
            )
        
        except Exception as e:
            self.logger.error(f"Telegram alert failed: {e}")

    def start_periodic_monitoring(self, 
                                  interval: int = 300, 
                                  log_metrics: bool = True, 
                                  check_alerts: bool = True):
        """
        Start periodic system monitoring
        
        :param interval: Monitoring interval in seconds
        :param log_metrics: Whether to log metrics
        :param check_alerts: Whether to check alerts
        """
        async def monitor():
            while True:
                metrics = self.collect_system_metrics()
                
                if log_metrics:
                    self.log_system_metrics(metrics)
                
                if check_alerts:
                    self.check_alerts(metrics)
                
                await asyncio.sleep(interval)
        
        asyncio.create_task(monitor())

def create_monitoring_system(
    service_name: str = 'vocality_nexus',
    monitoring_dir: str = 'monitoring_logs',
    prometheus_port: int = 8000
) -> AdvancedMonitoringSystem:
    """
    Factory method to create monitoring system
    
    :param service_name: Name of the monitored service
    :param monitoring_dir: Directory for storing monitoring logs
    :param prometheus_port: Port for Prometheus metrics server
    :return: Configured monitoring system
    """
    return AdvancedMonitoringSystem(
        service_name, 
        monitoring_dir, 
        prometheus_port
    )
