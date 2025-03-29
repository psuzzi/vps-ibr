#!/usr/bin/env python3
"""
Inventory collection module for VPS Inventory, Backup & Restore.
"""
import os
import shutil
import tempfile
import datetime
from typing import Dict, Any, List, Optional

from vps_ibr.utils.ssh import run_ssh_command, scp_get_file
from vps_ibr.inventory.parser import parse_bash_history

def create_inventory(config: Dict[str, Any], output_dir: Optional[str] = None) -> str:
    """
    Create inventory for all servers in config.
    
    Args:
        config: Loaded configuration dictionary
        output_dir: Optional output directory (auto-generated if None)
        
    Returns:
        Path to the created inventory directory
    """
    if not config:
        raise ValueError("Invalid configuration provided")
    
    # Create result directory
    if not output_dir:
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        result_dir = f"ibr-{timestamp}"
    else:
        result_dir = output_dir
        
    os.makedirs(result_dir, exist_ok=True)
    
    global_config = config.get("global", {})
    default_ssh_key = global_config.get("default_ssh_key", "id_rsa")
    ssh_key_path_base = os.path.expanduser(global_config.get("ssh_key_path", "~/.ssh"))
    
    for server in config.get("servers", []):
        ip = server.get("ip")
        description = server.get("description", "No description")
        ssh_key_name = server.get("ssh_key", default_ssh_key)
        ssh_key_path = os.path.join(ssh_key_path_base, ssh_key_name)
        
        if not ip:
            print("Server missing IP address, skipping.")
            continue
            
        print(f"\nProcessing server: {ip} ({description})")
        print(f"Using SSH key: {ssh_key_path}")
        
        # Create server directory with timestamp
        today = datetime.datetime.now().strftime("%Y%m%d")
        server_dir = os.path.join(result_dir, f"{ip}-{today}")
        os.makedirs(server_dir, exist_ok=True)
        
        # Save server metadata
        with open(os.path.join(server_dir, "server_info.txt"), "w") as f:
            f.write(f"IP: {ip}\n")
            f.write(f"Description: {description}\n")
            f.write(f"Inventory Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Create users directory
        os.makedirs(os.path.join(server_dir, "users"), exist_ok=True)
        
        # Get list of users
        print("  Getting list of users...")
        users = get_users(ip, ssh_key_path)
        
        # Get sudo users for reference
        sudo_users = get_sudo_users(ip, ssh_key_path)
        
        # Save list of sudo users
        with open(os.path.join(server_dir, "sudo_users.txt"), "w") as f:
            for user in sudo_users:
                f.write(f"{user}\n")
        
        # Copy bash history for each user
        print("  Copying bash history files...")
        for user in users:
            copy_bash_history(ip, ssh_key_path, user, server_dir)
            
        # Optional: Parse bash histories to detect services (placeholder for future)
        print("  Inventory collected successfully.")
        
    return result_dir

def get_users(ip: str, ssh_key_path: str) -> List[Dict[str, str]]:
    """
    Get list of users on the server with home directories.
    
    Args:
        ip: Server IP address
        ssh_key_path: Path to SSH key
        
    Returns:
        List of dictionaries with username and home directory
    """
    command = "awk -F: '$3 >= 1000 && $3 != 65534 {print $1 \":\" $6}' /etc/passwd"
    output = run_ssh_command(ip, ssh_key_path, command)
    
    users = []
    if output:
        for line in output.splitlines():
            parts = line.strip().split(":")
            if len(parts) >= 2:
                users.append({"username": parts[0], "home": parts[1]})
    
    # Always include root
    users.append({"username": "root", "home": "/root"})
    
    return users

def get_sudo_users(ip: str, ssh_key_path: str) -> List[str]:
    """
    Get list of users with sudo privileges.
    
    Args:
        ip: Server IP address
        ssh_key_path: Path to SSH key
        
    Returns:
        List of usernames with sudo privileges
    """
    # Check sudo group members
    sudo_group_cmd = "getent group sudo | cut -d: -f4"
    sudo_group = run_ssh_command(ip, ssh_key_path, sudo_group_cmd) or ""
    
    # Check sudoers file
    sudoers_cmd = "grep -v '^#' /etc/sudoers | grep -v '^Defaults' | grep 'ALL=(ALL:ALL)' | cut -d' ' -f1"
    sudoers = run_ssh_command(ip, ssh_key_path, sudoers_cmd) or ""
    
    # Combine results
    sudo_users = set()
    for user in sudo_group.split(","):
        if user.strip():
            sudo_users.add(user.strip())
            
    for user in sudoers.splitlines():
        if user.strip() and not user.strip().startswith('%'):  # Ignore group entries
            sudo_users.add(user.strip())
    
    return list(sudo_users)

def copy_bash_history(ip: str, ssh_key_path: str, user: Dict[str, str], server_dir: str) -> None:
    """
    Copy bash history for a specific user.
    
    Args:
        ip: Server IP address
        ssh_key_path: Path to SSH key
        user: User dictionary with username and home directory
        server_dir: Directory to store the history
    """
    username = user["username"]
    home_dir = user["home"]
    
    # Create user directory
    user_dir = os.path.join(server_dir, "users", username)
    os.makedirs(user_dir, exist_ok=True)
    
    # Path to bash history
    history_path = f"{home_dir}/.bash_history"
    
    # Attempt to copy the history file
    success = scp_get_file(ip, ssh_key_path, history_path, os.path.join(user_dir, "bash_history"))
    
    if success:
        print(f"  - Copied bash history for user {username}")
    else:
        print(f"  - Could not copy bash history for user {username}")