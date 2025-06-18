import json
import os
from typing import Dict, Any, Optional

class ConfigManager:
    """Centralized configuration management for blind control system"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Configuration file {self.config_file} not found. Using defaults.")
            return self.get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error parsing configuration file: {e}. Using defaults.")
            return self.get_default_config()
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value with dot notation support"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_default_config(self) -> Dict[str, Any]:
        """Override this method in subclasses to provide default configuration"""
        return {}

class ControllerConfig(ConfigManager):
    """Configuration manager for controller instances"""
    
    def get_default_config(self) -> Dict[str, Any]:
        return {
            "location_name": "Blind Control",
            "hub_url": "http://192.168.4.202:5001/",
            "weather_api_key": "b8c328a0f8be42ff936210148250404",
            "location": "29607",
            "cloud_threshold": 15,
            "monitoring_interval": 10,
            "schedule": {
                "lower_blinds_offset": 192,
                "raise_blinds_offset": 0
            }
        }

class HubConfig(ConfigManager):
    """Configuration manager for hub instance"""
    
    def get_default_config(self) -> Dict[str, Any]:
        return {
            "weather_api_key": "b8c328a0f8be42ff936210148250404",
            "location": "29607",
            "cloud_threshold": 15,
            "monitoring_interval": 10,
            "schedule": {
                "lower_blinds_offset": 192,
                "raise_blinds_offset": 0
            }
        }
