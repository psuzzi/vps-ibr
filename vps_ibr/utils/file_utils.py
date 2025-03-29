#!/usr/bin/env python3
"""
File utility functions for VPS Inventory, Backup & Restore.
"""
import os
import shutil
import json
import yaml
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

def ensure_dir(path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        The directory path
    """
    os.makedirs(path, exist_ok=True)
    return path

def create_timestamp_dir(base_dir: str, prefix: str = "ibr") -> str:
    """
    Create a timestamped directory.
    
    Args:
        base_dir: Base directory
        prefix: Directory name prefix
        
    Returns:
        Path to created directory
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dir_path = os.path.join(base_dir, f"{prefix}-{timestamp}")
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def save_json(data: Dict[str, Any], filepath: str, indent: int = 2) -> bool:
    """
    Save data as JSON file.
    
    Args:
        data: Data to save
        filepath: Path to save file
        indent: JSON indentation level
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        print(f"Error saving JSON file {filepath}: {e}")
        return False

def load_json(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load data from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded data or None if loading failed
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {filepath}: {e}")
        return None

def save_yaml(data: Dict[str, Any], filepath: str) -> bool:
    """
    Save data as YAML file.
    
    Args:
        data: Data to save
        filepath: Path to save file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
        return True
    except Exception as e:
        print(f"Error saving YAML file {filepath}: {e}")
        return False

def copy_directory(src: str, dst: str, exclude: List[str] = None) -> bool:
    """
    Copy a directory with exclusions.
    
    Args:
        src: Source directory
        dst: Destination directory
        exclude: List of patterns to exclude
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert exclude patterns to function for filtering
        def filter_func(src, names):
            if not exclude:
                return []
            excluded = set()
            for name in names:
                for pattern in exclude:
                    if pattern in name:
                        excluded.add(name)
            return excluded
        
        # Copy directory
        shutil.copytree(src, dst, ignore=filter_func, dirs_exist_ok=True)
        return True
    except Exception as e:
        print(f"Error copying directory {src} to {dst}: {e}")
        return False

def find_servers_in_backup(backup_dir: str) -> List[str]:
    """
    Find server directories in a backup directory.
    
    Args:
        backup_dir: Backup directory path
        
    Returns:
        List of server IPs found in backup
    """
    if not os.path.exists(backup_dir):
        return []
    
    servers = []
    
    # Look for directories matching IP-date pattern
    ip_pattern = r'\d+\.\d+\.\d+\.\d+-\d+'
    
    for item in os.listdir(backup_dir):
        item_path = os.path.join(backup_dir, item)
        if os.path.isdir(item_path) and '-' in item:
            # Extract IP from directory name
            ip = item.split('-')[0]
            if all(part.isdigit() for part in ip.split('.')):
                servers.append(ip)
    
    return servers