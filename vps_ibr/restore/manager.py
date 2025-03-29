#!/usr/bin/env python3
"""
Restore management module for VPS Inventory, Backup & Restore.
"""
import os
import json
import yaml
import shutil
import datetime
from typing import Dict, Any, List, Optional, Tuple

from vps_ibr.utils.ssh import run_ssh_command, rsync_push
from vps_ibr.utils.file_utils import ensure_dir, load_json

# Service-specific restore handlers
SERVICE_RESTORE_HANDLERS = {
    "nginx": {
        "paths": ["/etc/nginx/", "/var/www/"],
        "restart_cmd": "systemctl restart nginx"
    },
    "apache2": {
        "paths": ["/etc/apache2/", "/var/www/"],
        "restart_cmd": "systemctl restart apache2"
    },
    "mysql": {
        "paths": ["/etc/mysql/"],
        "pre_restore_cmd": "systemctl stop mysql",
        "post_restore_cmd": "mysql < /tmp/all_databases.sql && systemctl start mysql",
        "files": [
            {"src": "files/all_databases.sql", "dst": "/tmp/all_databases.sql"}
        ]
    },
    "postgresql": {
        "paths": ["/etc/postgresql/"],
        "pre_restore_cmd": "systemctl stop postgresql",
        "post_restore_cmd": "su - postgres -c 'psql < /tmp/pg_dumpall.sql' && systemctl start postgresql",
        "files": [
            {"src": "files/pg_dumpall.sql", "dst": "/tmp/pg_dumpall.sql"}
        ]
    },
    "docker": {
        "paths": ["/etc/docker/"],
        "post_restore_cmd": "systemctl restart docker"
    }
}

def restore_server(backup_dir: str, target_ip: str, ssh_key: Optional[str] = None) -> bool:
    """
    Restore a server from backup.
    
    Args:
        backup_dir: Path to backup directory
        target_ip: Target server IP
        ssh_key: Optional SSH key to use (default: id_rsa)
        
    Returns:
        True if restoration was successful, False otherwise
    """
    if not os.path.exists(backup_dir) or not os.path.isdir(backup_dir):
        print(f"Error: Backup directory {backup_dir} does not exist")
        return False
    
    # Determine SSH key
    ssh_key_path = os.path.expanduser(f"~/.ssh/{ssh_key if ssh_key else 'id_rsa'}")
    if not os.path.exists(ssh_key_path):
        print(f"Error: SSH key {ssh_key_path} does not exist")
        return False
    
    print(f"Starting restoration to {target_ip} using backup {backup_dir}")
    print(f"Using SSH key: {ssh_key_path}")
    
    # Check SSH connectivity
    test_cmd = "echo 'SSH connection successful'"
    test_result = run_ssh_command(target_ip, ssh_key_path, test_cmd)
    if not test_result:
        print(f"Error: Could not connect to {target_ip} using SSH key {ssh_key_path}")
        return False
    
    # Load backup summary if available
    summary_path = os.path.join(backup_dir, "backup_summary.json")
    summary = None
    if os.path.exists(summary_path):
        summary = load_json(summary_path)
    
    # Create restoration log
    log_file = os.path.join(backup_dir, "restore_log.txt")
    with open(log_file, 'w') as f:
        f.write(f"Restoration started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Target server: {target_ip}\n")
        f.write(f"Backup directory: {backup_dir}\n\n")
    
    # Restore system configurations first
    system_restore_success = restore_system_configs(target_ip, ssh_key_path, backup_dir, log_file)
    
    # Restore services if available
    services_dir = os.path.join(backup_dir, "services")
    services_restored = []
    
    if os.path.exists(services_dir):
        for service in os.listdir(services_dir):
            service_dir = os.path.join(services_dir, service)
            if os.path.isdir(service_dir):
                service_success = restore_service(
                    target_ip, ssh_key_path, service, service_dir, log_file
                )
                if service_success:
                    services_restored.append(service)
    
    # Restore user home directories
    homes_dir = os.path.join(backup_dir, "homes")
    users_restored = []
    
    if os.path.exists(homes_dir):
        for user in os.listdir(homes_dir):
            user_dir = os.path.join(homes_dir, user)
            if os.path.isdir(user_dir):
                # Ensure user exists
                create_user_cmd = f"id {user} >/dev/null 2>&1 || useradd -m {user}"
                run_ssh_command(target_ip, ssh_key_path, create_user_cmd)
                
                # Get user's home directory
                home_cmd = f"getent passwd {user} | cut -d: -f6"
                home_dir = run_ssh_command(target_ip, ssh_key_path, home_cmd)
                
                if home_dir:
                    # Restore home directory
                    log_message(log_file, f"Restoring home directory for user {user}")
                    rsync_push(target_ip, ssh_key_path, f"{user_dir}/", f"{home_dir}/")
                    users_restored.append(user)
    
    # Complete the restore log
    with open(log_file, 'a') as f:
        f.write("\nRestoration completed.\n")
        f.write(f"Completed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Services restored:\n")
        for service in services_restored:
            f.write(f"  - {service}\n")
        f.write("\n")
        
        f.write("Users restored:\n")
        for user in users_restored:
            f.write(f"  - {user}\n")
    
    print(f"\nRestoration completed. See {log_file} for details.")
    return True

def log_message(log_file: str, message: str) -> None:
    """
    Add a message to the restoration log.
    
    Args:
        log_file: Path to log file
        message: Message to log
    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)

def restore_system_configs(
    target_ip: str, 
    ssh_key_path: str, 
    backup_dir: str, 
    log_file: str
) -> bool:
    """
    Restore system configuration files.
    
    Args:
        target_ip: Target server IP
        ssh_key_path: Path to SSH key
        backup_dir: Path to backup directory
        log_file: Path to log file
        
    Returns:
        True if successful, False otherwise
    """
    system_dir = os.path.join(backup_dir, "system")
    if not os.path.exists(system_dir):
        log_message(log_file, "No system configuration backup found, skipping")
        return False
    
    log_message(log_file, "Restoring system configurations")
    
    # Restore /etc directory
    etc_dir = os.path.join(system_dir, "etc")
    if os.path.exists(etc_dir):
        log_message(log_file, "  Restoring /etc directory")
        rsync_push(target_ip, ssh_key_path, f"{etc_dir}/", "/etc/")
    
    # Restore cron jobs
    cron_dir = os.path.join(system_dir, "var/spool/cron")
    if os.path.exists(cron_dir):
        log_message(log_file, "  Restoring cron jobs")
        rsync_push(target_ip, ssh_key_path, f"{cron_dir}/", "/var/spool/cron/")
    
    return True

def restore_service(
    target_ip: str, 
    ssh_key_path: str, 
    service: str, 
    service_dir: str, 
    log_file: str
) -> bool:
    """
    Restore a specific service.
    
    Args:
        target_ip: Target server IP
        ssh_key_path: Path to SSH key
        service: Service name
        service_dir: Path to service backup directory
        log_file: Path to log file
        
    Returns:
        True if successful, False otherwise
    """
    log_message(log_file, f"Restoring service: {service}")
    
    # Check if we have a handler for this service
    handler = SERVICE_RESTORE_HANDLERS.get(service)
    
    # Run pre-restore command if available
    if handler and "pre_restore_cmd" in handler:
        pre_cmd = handler["pre_restore_cmd"]
        log_message(log_file, f"  Running pre-restore command: {pre_cmd}")
        run_ssh_command(target_ip, ssh_key_path, pre_cmd)
    
    # Restore files directory
    files_dir = os.path.join(service_dir, "files")
    if os.path.exists(files_dir):
        if handler and "paths" in handler:
            # Restore to specific paths
            for path in handler["paths"]:
                src_path = os.path.join(files_dir, path.lstrip('/'))
                if os.path.exists(src_path):
                    log_message(log_file, f"  Restoring {path}")
                    rsync_push(target_ip, ssh_key_path, f"{src_path}/", f"{path}/")
        else:
            # No specific paths, try to infer from directory structure
            for item in os.listdir(files_dir):
                if os.path.isdir(os.path.join(files_dir, item)):
                    # Assume top-level directories in files_dir correspond to system directories
                    src_path = os.path.join(files_dir, item)
                    dst_path = f"/{item}/"
                    log_message(log_file, f"  Restoring {dst_path}")
                    rsync_push(target_ip, ssh_key_path, f"{src_path}/", dst_path)
    
    # Restore specific files if defined in handler
    if handler and "files" in handler:
        for file_info in handler["files"]:
            src = file_info["src"]
            dst = file_info["dst"]
            src_path = os.path.join(service_dir, src)
            
            if os.path.exists(src_path):
                log_message(log_file, f"  Copying file {src} to {dst}")
                # Ensure directory exists
                dst_dir = os.path.dirname(dst)
                run_ssh_command(target_ip, ssh_key_path, f"mkdir -p {dst_dir}")
                
                # Use SCP to copy the file
                with open(src_path, 'rb') as f:
                    content = f.read()
                    
                # Temporary file approach
                tmp_path = f"/tmp/{os.path.basename(dst)}"
                with open("/tmp/temp_file", 'wb') as f:
                    f.write(content)
                
                # Using SCP to copy to the server
                subprocess.run(
                    ["scp", "-i", ssh_key_path, "/tmp/temp_file", f"root@{target_ip}:{tmp_path}"],
                    check=False
                )
                
                # Move to final destination
                run_ssh_command(target_ip, ssh_key_path, f"mv {tmp_path} {dst}")
                
                # Clean up
                os.remove("/tmp/temp_file")
    
    # Install package if needed
    install_cmd = None
    if service in ["nginx", "apache2", "mysql", "postgresql", "docker"]:
        # Check if the service is already installed
        check_cmd = f"which {service} >/dev/null 2>&1 || echo 'not_installed'"
        check_result = run_ssh_command(target_ip, ssh_key_path, check_cmd)
        
        if check_result == "not_installed":
            # Try to detect package manager and install
            apt_cmd = "which apt >/dev/null 2>&1"
            yum_cmd = "which yum >/dev/null 2>&1"
            
            if run_ssh_command(target_ip, ssh_key_path, apt_cmd):
                install_cmd = f"apt update && apt install -y {service}"
            elif run_ssh_command(target_ip, ssh_key_path, yum_cmd):
                install_cmd = f"yum install -y {service}"
    
    if install_cmd:
        log_message(log_file, f"  Installing {service}: {install_cmd}")
        run_ssh_command(target_ip, ssh_key_path, install_cmd)
    
    # Run post-restore command if available
    if handler and "post_restore_cmd" in handler:
        post_cmd = handler["post_restore_cmd"]
        log_message(log_file, f"  Running post-restore command: {post_cmd}")
        run_ssh_command(target_ip, ssh_key_path, post_cmd)
    elif handler and "restart_cmd" in handler:
        restart_cmd = handler["restart_cmd"]
        log_message(log_file, f"  Restarting service: {restart_cmd}")
        run_ssh_command(target_ip, ssh_key_path, restart_cmd)
    
    return True