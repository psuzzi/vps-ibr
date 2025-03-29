#!/usr/bin/env python3
"""
Backup management module for VPS Inventory, Backup & Restore.
"""
import os
import json
import datetime
from typing import Dict, Any, List, Optional, Tuple

from vps_ibr.utils.ssh import run_ssh_command, rsync_pull
from vps_ibr.utils.file_utils import ensure_dir, save_json
from vps_ibr.inventory.parser import analyze_server_history

# Service-specific backup handlers
SERVICE_BACKUP_HANDLERS = {
    "nginx": {
        "paths": ["/etc/nginx/", "/var/www/"],
        "commands": ["nginx -T"]
    },
    "apache2": {
        "paths": ["/etc/apache2/", "/var/www/"],
        "commands": ["apache2ctl -S"]
    },
    "mysql": {
        "paths": ["/etc/mysql/"],
        "commands": ["mysqldump --all-databases > /tmp/all_databases.sql"],
        "files": ["/tmp/all_databases.sql"]
    },
    "postgresql": {
        "paths": ["/etc/postgresql/"],
        "commands": ["pg_dumpall -U postgres > /tmp/pg_dumpall.sql"],
        "files": ["/tmp/pg_dumpall.sql"]
    },
    "docker": {
        "paths": ["/var/lib/docker/volumes/", "/etc/docker/"],
        "commands": ["docker ps", "docker volume ls"]
    },
    "nodejs": {
        "paths": ["/etc/nodejs/", "/var/www/"],
        "commands": []
    }
}

def create_backup(
    config: Dict[str, Any], 
    server_ip: Optional[str] = None,
    output_dir: Optional[str] = None
) -> str:
    """
    Create backup for servers based on inventory data.
    
    Args:
        config: Configuration dictionary
        server_ip: Optional specific server IP to backup (all servers if None)
        output_dir: Optional output directory path
        
    Returns:
        Path to created backup directory
    """
    if not config:
        raise ValueError("Invalid configuration provided")
    
    # Create backup directory
    if not output_dir:
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = f"ibr-{timestamp}"
    else:
        backup_dir = output_dir
        
    os.makedirs(backup_dir, exist_ok=True)
    
    global_config = config.get("global", {})
    default_ssh_key = global_config.get("default_ssh_key", "id_rsa")
    ssh_key_path_base = os.path.expanduser(global_config.get("ssh_key_path", "~/.ssh"))
    
    # Filter servers if specific IP provided
    servers = [s for s in config.get("servers", []) if server_ip is None or s.get("ip") == server_ip]
    
    if server_ip and not servers:
        print(f"Server with IP {server_ip} not found in configuration.")
        return backup_dir
    
    for server in servers:
        ip = server.get("ip")
        description = server.get("description", "No description")
        ssh_key_name = server.get("ssh_key", default_ssh_key)
        ssh_key_path = os.path.join(ssh_key_path_base, ssh_key_name)
        
        if not ip:
            print("Server missing IP address, skipping.")
            continue
            
        print(f"\nBacking up server: {ip} ({description})")
        print(f"Using SSH key: {ssh_key_path}")
        
        # Create server directory with timestamp
        today = datetime.datetime.now().strftime("%Y%m%d")
        server_dir = os.path.join(backup_dir, f"{ip}-{today}")
        os.makedirs(server_dir, exist_ok=True)
        
        # Save server metadata
        with open(os.path.join(server_dir, "server_info.txt"), "w") as f:
            f.write(f"IP: {ip}\n")
            f.write(f"Description: {description}\n")
            f.write(f"Backup Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # First, look for inventory data
        inventory_data = find_inventory_for_server(ip)
        services_detected = []
        
        if inventory_data:
            print(f"Found existing inventory for {ip}, using for targeted backup")
            server_analysis = analyze_server_history(inventory_data)
            
            # Save analysis as backup metadata
            save_json(server_analysis, os.path.join(server_dir, "server_analysis.json"))
            
            # Extract services from analysis
            if "services" in server_analysis:
                services_detected = server_analysis["services"]
        else:
            print(f"No existing inventory found for {ip}, performing basic backup")
        
        # Perform service-specific backups
        for service in services_detected:
            # Check if we have a handler for this service
            if service in SERVICE_BACKUP_HANDLERS:
                handler = SERVICE_BACKUP_HANDLERS[service]
                backup_service(ip, ssh_key_path, service, handler, server_dir)
        
        # Backup home directories for all users
        backup_user_homes(ip, ssh_key_path, server_dir)
        
        # Backup important system configurations
        backup_system_configs(ip, ssh_key_path, server_dir)
        
        print(f"Backup completed for {ip}")
    
    return backup_dir

def find_inventory_for_server(ip: str) -> Optional[str]:
    """
    Find the most recent inventory directory for a server.
    
    Args:
        ip: Server IP
        
    Returns:
        Path to inventory directory or None if not found
    """
    # Look in current directory for inventory folders
    inventory_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and d.startswith('ibr-')]
    inventory_dirs.sort(reverse=True)  # Most recent first
    
    for inv_dir in inventory_dirs:
        # Check if this inventory contains our server
        server_dirs = [d for d in os.listdir(inv_dir) if d.startswith(f"{ip}-")]
        if server_dirs:
            # Return most recent
            server_dirs.sort(reverse=True)
            return os.path.join(inv_dir, server_dirs[0])
    
    return None

def backup_service(
    ip: str, 
    ssh_key_path: str, 
    service: str, 
    handler: Dict[str, Any], 
    server_dir: str
) -> None:
    """
    Backup a specific service using its handler.
    
    Args:
        ip: Server IP
        ssh_key_path: Path to SSH key
        service: Service name
        handler: Service handler configuration
        server_dir: Directory to store backup
    """
    print(f"  Backing up service: {service}")
    
    # Create service directory
    service_dir = os.path.join(server_dir, "services", service)
    ensure_dir(service_dir)
    
    # Backup paths
    for path in handler.get("paths", []):
        print(f"    Backing up path: {path}")
        # Create local directory structure
        local_path = os.path.join(service_dir, "files", path.lstrip('/'))
        ensure_dir(os.path.dirname(local_path))
        
        # Use rsync to copy files
        rsync_pull(ip, ssh_key_path, path, local_path)
    
    # Run commands and save output
    for cmd in handler.get("commands", []):
        print(f"    Running command: {cmd}")
        cmd_name = cmd.split()[0]
        output = run_ssh_command(ip, ssh_key_path, cmd)
        
        if output:
            with open(os.path.join(service_dir, f"{cmd_name}_output.txt"), 'w') as f:
                f.write(output)
    
    # Backup specific files
    for file_path in handler.get("files", []):
        print(f"    Backing up file: {file_path}")
        # Use the filename for the local path
        local_file = os.path.join(service_dir, "files", os.path.basename(file_path))
        ensure_dir(os.path.dirname(local_file))
        
        # Use SCP to copy the file
        run_ssh_command(ip, ssh_key_path, f"scp {file_path} root@localhost:/tmp/")
        run_ssh_command(ip, ssh_key_path, f"rm {file_path}")  # Clean up temporary dump files

def backup_user_homes(ip: str, ssh_key_path: str, server_dir: str) -> None:
    """
    Backup home directories for all users.
    
    Args:
        ip: Server IP
        ssh_key_path: Path to SSH key
        server_dir: Directory to store backup
    """
    print("  Backing up user home directories")
    
    # Get list of users with home directories
    user_cmd = "awk -F: '$3 >= 1000 && $3 != 65534 {print $1 \":\" $6}' /etc/passwd"
    output = run_ssh_command(ip, ssh_key_path, user_cmd)
    
    if not output:
        return
    
    # Create homes directory
    homes_dir = os.path.join(server_dir, "homes")
    ensure_dir(homes_dir)
    
    for line in output.splitlines():
        parts = line.strip().split(":")
        if len(parts) >= 2:
            username = parts[0]
            home_dir = parts[1]
            
            print(f"    Backing up home directory for user: {username}")
            
            # Create user directory
            user_backup_dir = os.path.join(homes_dir, username)
            ensure_dir(user_backup_dir)
            
            # Use rsync to copy home directory, excluding large and cache dirs
            exclude = [
                ".cache", 
                "node_modules", 
                ".venv", 
                "venv", 
                "env", 
                "__pycache__",
                "tmp",
                "temp"
            ]
            rsync_pull(ip, ssh_key_path, f"{home_dir}/", user_backup_dir, exclude)

def backup_system_configs(ip: str, ssh_key_path: str, server_dir: str) -> None:
    """
    Backup important system configuration files.
    
    Args:
        ip: Server IP
        ssh_key_path: Path to SSH key
        server_dir: Directory to store backup
    """
    print("  Backing up system configuration files")
    
    # Create system directory
    system_dir = os.path.join(server_dir, "system")
    ensure_dir(system_dir)
    
    # List of important directories to backup
    system_paths = [
        "/etc/",
        "/var/spool/cron/",
        "/var/log/"
    ]
    
    for path in system_paths:
        print(f"    Backing up system path: {path}")
        # Create local directory structure
        local_path = os.path.join(system_dir, path.lstrip('/'))
        ensure_dir(os.path.dirname(local_path))
        
        # Use rsync to copy files
        exclude = ["*.log", "*.gz", "*.old", "*.bak"]
        rsync_pull(ip, ssh_key_path, path, local_path, exclude)
    
    # Capture system information
    system_commands = [
        "uname -a",
        "lsb_release -a",
        "df -h",
        "free -m",
        "netstat -tulpn",
        "ps aux",
        "dpkg -l",
        "systemctl list-units --type=service",
        "ss -tulpn",
        "ifconfig -a"
    ]
    
    # Run commands and save output
    for cmd in system_commands:
        cmd_name = cmd.split()[0].replace('-', '_')
        output = run_ssh_command(ip, ssh_key_path, cmd)
        
        if output:
            with open(os.path.join(system_dir, f"{cmd_name}_output.txt"), 'w') as f:
                f.write(output)
    
    # Create a backup summary
    create_backup_summary(server_dir)

def create_backup_summary(server_dir: str) -> None:
    """
    Create a summary of the backup.
    
    Args:
        server_dir: Server backup directory
    """
    summary = {
        "backup_date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "services": [],
        "users": [],
        "backup_size": 0
    }
    
    # Get services
    services_dir = os.path.join(server_dir, "services")
    if os.path.exists(services_dir):
        summary["services"] = [svc for svc in os.listdir(services_dir) 
                              if os.path.isdir(os.path.join(services_dir, svc))]
    
    # Get users
    homes_dir = os.path.join(server_dir, "homes")
    if os.path.exists(homes_dir):
        summary["users"] = [user for user in os.listdir(homes_dir) 
                           if os.path.isdir(os.path.join(homes_dir, user))]
    
    # Calculate backup size
    summary["backup_size"] = get_dir_size(server_dir)
    
    # Save summary
    save_json(summary, os.path.join(server_dir, "backup_summary.json"))
    
    # Create human-readable summary
    with open(os.path.join(server_dir, "backup_summary.txt"), 'w') as f:
        f.write(f"Backup Date: {summary['backup_date']}\n\n")
        
        f.write(f"Backup Size: {format_size(summary['backup_size'])}\n\n")
        
        f.write("Backed Up Services:\n")
        for service in summary['services']:
            f.write(f"  - {service}\n")
        f.write("\n")
        
        f.write("Backed Up Users:\n")
        for user in summary['users']:
            f.write(f"  - {user}\n")

def get_dir_size(path: str) -> int:
    """
    Calculate the total size of a directory in bytes.
    
    Args:
        path: Directory path
        
    Returns:
        Size in bytes
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            file_path = os.path.join(dirpath, f)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
    return total_size

def format_size(size_bytes: int) -> str:
    """
    Format bytes to human-readable size.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    # Define units and thresholds
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    
    # Handle zero size
    if size_bytes == 0:
        return "0 B"
    
    # Calculate the appropriate unit
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024.0
        i += 1
    
    # Format with two decimal places
    return f"{size_bytes:.2f} {units[i]}"