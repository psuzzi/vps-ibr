#!/usr/bin/env python3
"""
Configuration handling for VPS Inventory, Backup & Restore.
"""
import os
import yaml
from typing import Dict, Any, Optional

def load_config(config_path: str) -> Optional[Dict[str, Any]]:
    """
    Load server configuration from YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dictionary containing configuration or None if loading fails
    """
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            
        # Validate configuration
        if not validate_config(config):
            return None
            
        return config
    except Exception as e:
        print(f"Error loading configuration file: {e}")
        return None

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the loaded configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    # Check if servers key exists and is a list
    if not config.get("servers") or not isinstance(config["servers"], list):
        print("Error: 'servers' key missing or not a list")
        return False
        
    # Check each server has at least an IP
    for i, server in enumerate(config["servers"]):
        if not isinstance(server, dict):
            print(f"Error: Server at index {i} is not a dictionary")
            return False
            
        if "ip" not in server:
            print(f"Error: Server at index {i} missing 'ip' field")
            return False
    
    # Ensure global configuration exists (create if missing)
    if "global" not in config:
        config["global"] = {}
        
    # Set defaults for global configuration
    defaults = {
        "default_ssh_key": "id_rsa",
        "ssh_key_path": "~/.ssh",
        "timeout": 30,
        "backup_root": "~/vps-backups"
    }
    
    for key, value in defaults.items():
        if key not in config["global"]:
            config["global"][key] = value
            
    # Expand paths
    config["global"]["ssh_key_path"] = os.path.expanduser(config["global"]["ssh_key_path"])
    config["global"]["backup_root"] = os.path.expanduser(config["global"]["backup_root"])
    
    return True