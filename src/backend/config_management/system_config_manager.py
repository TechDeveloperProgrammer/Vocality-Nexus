import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, Union, List
import toml
import jsonschema
from dotenv import load_dotenv
import socket
import platform
import psutil

class AdvancedSystemConfigManager:
    """
    Comprehensive system configuration management utility
    Supports multiple configuration formats, validation, and dynamic updates
    """
    
    def __init__(self, 
                 config_dir: str = 'config',
                 env_file: Optional[str] = None):
        """
        Initialize system configuration manager
        
        :param config_dir: Directory containing configuration files
        :param env_file: Optional path to .env file
        """
        # Logging configuration
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Configuration directory
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        
        # Configuration cache
        self._config_cache: Dict[str, Any] = {}
        
        # Configuration schemas
        self._config_schemas: Dict[str, Dict[str, Any]] = {}

    def load_config(self, 
                    config_name: str, 
                    config_type: str = 'yaml') -> Dict[str, Any]:
        """
        Load configuration from file
        
        :param config_name: Name of configuration file
        :param config_type: Configuration file type
        :return: Parsed configuration dictionary
        """
        # Check cache first
        if config_name in self._config_cache:
            return self._config_cache[config_name]
        
        # Determine file path
        file_extensions = {
            'yaml': ['.yaml', '.yml'],
            'json': ['.json'],
            'toml': ['.toml']
        }
        
        for ext in file_extensions.get(config_type, []):
            config_path = os.path.join(self.config_dir, f'{config_name}{ext}')
            
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        if config_type == 'yaml':
                            config = yaml.safe_load(f)
                        elif config_type == 'json':
                            config = json.load(f)
                        elif config_type == 'toml':
                            config = toml.load(f)
                    
                    # Validate configuration if schema exists
                    if config_name in self._config_schemas:
                        self.validate_config(config, self._config_schemas[config_name])
                    
                    # Cache configuration
                    self._config_cache[config_name] = config
                    return config
                
                except Exception as e:
                    self.logger.error(f"Error loading {config_path}: {e}")
        
        raise FileNotFoundError(f"No configuration found for {config_name}")

    def save_config(self, 
                    config: Dict[str, Any], 
                    config_name: str, 
                    config_type: str = 'yaml') -> None:
        """
        Save configuration to file
        
        :param config: Configuration dictionary
        :param config_name: Name of configuration file
        :param config_type: Configuration file type
        """
        # Validate configuration if schema exists
        if config_name in self._config_schemas:
            self.validate_config(config, self._config_schemas[config_name])
        
        # Determine file path
        file_extensions = {
            'yaml': '.yaml',
            'json': '.json',
            'toml': '.toml'
        }
        
        config_path = os.path.join(
            self.config_dir, 
            f'{config_name}{file_extensions.get(config_type, ".yaml")}'
        )
        
        try:
            with open(config_path, 'w') as f:
                if config_type == 'yaml':
                    yaml.safe_dump(config, f, default_flow_style=False)
                elif config_type == 'json':
                    json.dump(config, f, indent=2)
                elif config_type == 'toml':
                    toml.dump(config, f)
            
            # Update cache
            self._config_cache[config_name] = config
            
            self.logger.info(f"Configuration saved to {config_path}")
        
        except Exception as e:
            self.logger.error(f"Error saving configuration to {config_path}: {e}")

    def register_config_schema(self, 
                               config_name: str, 
                               schema: Dict[str, Any]) -> None:
        """
        Register JSON schema for configuration validation
        
        :param config_name: Name of configuration
        :param schema: JSON schema dictionary
        """
        self._config_schemas[config_name] = schema

    def validate_config(self, 
                        config: Dict[str, Any], 
                        schema: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate configuration against schema
        
        :param config: Configuration to validate
        :param schema: Optional JSON schema
        :return: Whether configuration is valid
        """
        try:
            jsonschema.validate(instance=config, schema=schema)
            return True
        except jsonschema.ValidationError as e:
            self.logger.error(f"Configuration validation error: {e}")
            return False

    def get_environment_info(self) -> Dict[str, Any]:
        """
        Retrieve comprehensive system environment information
        
        :return: Dictionary of system details
        """
        return {
            'hostname': socket.gethostname(),
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            },
            'cpu': {
                'physical_cores': psutil.cpu_count(logical=False),
                'total_cores': psutil.cpu_count(logical=True),
                'cpu_freq': psutil.cpu_freq().current,
                'cpu_usage': psutil.cpu_percent(interval=1)
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'used': psutil.virtual_memory().used,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'network': {
                'interfaces': self._get_network_interfaces()
            },
            'environment_variables': dict(os.environ)
        }

    def _get_network_interfaces(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve network interface details
        
        :return: Dictionary of network interfaces
        """
        interfaces = {}
        for interface, addresses in psutil.net_if_addrs().items():
            interfaces[interface] = {
                'addresses': [
                    {
                        'family': addr.family.name,
                        'address': addr.address,
                        'netmask': addr.netmask
                    } for addr in addresses
                ]
            }
        return interfaces

    def update_config_from_env(self, 
                                config: Dict[str, Any], 
                                prefix: str = 'VOCALITY_') -> Dict[str, Any]:
        """
        Update configuration with environment variables
        
        :param config: Configuration dictionary
        :param prefix: Prefix for environment variables
        :return: Updated configuration
        """
        updated_config = config.copy()
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                try:
                    # Attempt type conversion
                    if value.lower() in ['true', 'false']:
                        converted_value = value.lower() == 'true'
                    elif value.isdigit():
                        converted_value = int(value)
                    elif self._is_float(value):
                        converted_value = float(value)
                    else:
                        converted_value = value
                    
                    # Update nested configuration
                    self._update_nested_dict(updated_config, config_key, converted_value)
                
                except Exception as e:
                    self.logger.warning(f"Could not convert env var {key}: {e}")
        
        return updated_config

    def _update_nested_dict(self, 
                             config: Dict[str, Any], 
                             key: str, 
                             value: Any) -> None:
        """
        Update nested dictionary
        
        :param config: Configuration dictionary
        :param key: Key to update (can be dot-separated)
        :param value: Value to set
        """
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        
        current[keys[-1]] = value

    def _is_float(self, value: str) -> bool:
        """
        Check if string can be converted to float
        
        :param value: String to check
        :return: Whether string is a valid float
        """
        try:
            float(value)
            return True
        except ValueError:
            return False

def create_system_config_manager(
    config_dir: str = 'config', 
    env_file: Optional[str] = None
) -> AdvancedSystemConfigManager:
    """
    Factory method to create system configuration manager
    
    :param config_dir: Directory containing configuration files
    :param env_file: Optional path to .env file
    :return: Configured system configuration manager
    """
    return AdvancedSystemConfigManager(
        config_dir, 
        env_file
    )
