#!/usr/bin/env python3
"""
SSH utility functions for VPS Inventory, Backup & Restore.
"""
import os
import subprocess
import tempfile
import shutil
from typing import Optional, Union, List

def run_ssh_command(
    ip: str, 
    ssh_key_path: str, 
    command: str, 
    timeout: int = 30
) -> Optional[str]:
    """
    Run a command on remote server via SSH and return output.
    
    Args:
        ip: Server IP address
        ssh_key_path: Path to SSH key file
        command: Command to execute on the remote server
        timeout: Timeout in seconds for the SSH connection
        
    Returns:
        Command output as string, or None if command failed
    """
    try:
        result = subprocess.run(
            ["ssh", "-i", ssh_key_path, "-o", f"ConnectTimeout={timeout}", 
             "-o", "StrictHostKeyChecking=no", f"root@{ip}", command],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command on {ip}: {e}")
        print(f"stderr: {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        print(f"Timeout while connecting to {ip}")
        return None
    except Exception as e:
        print(f"Unexpected error while executing command on {ip}: {e}")
        return None

def scp_get_file(
    ip: str, 
    ssh_key_path: str, 
    remote_path: str, 
    local_path: str, 
    timeout: int = 30
) -> bool:
    """
    Copy a file from remote server using SCP.
    
    Args:
        ip: Server IP address
        ssh_key_path: Path to SSH key file
        remote_path: Path to file on remote server
        local_path: Path to save file locally
        timeout: Timeout in seconds for the SSH connection
        
    Returns:
        True if file was copied successfully, False otherwise
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Use SCP to copy the file
        result = subprocess.run(
            ["scp", "-i", ssh_key_path, 
             "-o", f"ConnectTimeout={timeout}", 
             "-o", "StrictHostKeyChecking=no",
             f"root@{ip}:{remote_path}", temp_path],
            check=False, capture_output=True
        )
        
        # Check if file was successfully copied
        if result.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            shutil.copy(temp_path, local_path)
            return True
        return False
    except Exception as e:
        print(f"Error copying file from {ip}:{remote_path}: {e}")
        return False
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def rsync_pull(
    ip: str,
    ssh_key_path: str,
    remote_path: str,
    local_path: str,
    exclude: List[str] = None,
    timeout: int = 30
) -> bool:
    """
    Sync a directory from remote server using rsync.
    
    Args:
        ip: Server IP address
        ssh_key_path: Path to SSH key file
        remote_path: Path to directory on remote server
        local_path: Path to save directory locally
        exclude: List of patterns to exclude
        timeout: Timeout in seconds for the SSH connection
        
    Returns:
        True if directory was synced successfully, False otherwise
    """
    try:
        # Build rsync command
        command = ["rsync", "-avz", "--delete"]
        
        # Add SSH options
        ssh_opts = f"ssh -i {ssh_key_path} -o ConnectTimeout={timeout} -o StrictHostKeyChecking=no"
        command.extend(["-e", ssh_opts])
        
        # Add exclude patterns
        if exclude:
            for pattern in exclude:
                command.extend(["--exclude", pattern])
        
        # Add source and destination
        command.append(f"root@{ip}:{remote_path}")
        command.append(local_path)
        
        # Run rsync
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error rsyncing from {ip}:{remote_path}: {e}")
        return False

def rsync_push(
    ip: str,
    ssh_key_path: str,
    local_path: str,
    remote_path: str,
    exclude: List[str] = None,
    timeout: int = 30
) -> bool:
    """
    Sync a directory to remote server using rsync.
    
    Args:
        ip: Server IP address
        ssh_key_path: Path to SSH key file
        local_path: Path to directory locally
        remote_path: Path to save directory on remote server
        exclude: List of patterns to exclude
        timeout: Timeout in seconds for the SSH connection
        
    Returns:
        True if directory was synced successfully, False otherwise
    """
    try:
        # Build rsync command
        command = ["rsync", "-avz", "--delete"]
        
        # Add SSH options
        ssh_opts = f"ssh -i {ssh_key_path} -o ConnectTimeout={timeout} -o StrictHostKeyChecking=no"
        command.extend(["-e", ssh_opts])
        
        # Add exclude patterns
        if exclude:
            for pattern in exclude:
                command.extend(["--exclude", pattern])
        
        # Add source and destination
        command.append(local_path)
        command.append(f"root@{ip}:{remote_path}")
        
        # Run rsync
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error rsyncing to {ip}:{remote_path}: {e}")
        return False