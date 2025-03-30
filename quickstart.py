#!/usr/bin/env python3
"""
Quickstart script for VPS Inventory, Backup & Restore tool.
Creates a virtual environment, installs dependencies, sets up initial config.
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path

# Server configuration template (will be converted to YAML after dependencies are installed)
SERVER_CONFIG = {
    "servers": [
        {
            "ip": "192.0.2.10",
            "description": "Web Server",
            "ssh_key": "id_rsa"
        }
    ],
    "global": {
        "default_ssh_key": "id_rsa",
        "ssh_key_path": "~/.ssh",
        "timeout": 30,
        "backup_root": "~/vps-backups"
    }
}

def print_step(message):
    """Print a step message."""
    print(f"\n>> {message}")

def run_command(command, shell=False):
    """Run a command and return success status."""
    try:
        subprocess.run(command, shell=shell, check=True)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def write_yaml_config(config_file, config_data):
    """Write YAML configuration after dependencies are installed."""
    # This function will be called from the activated virtual environment
    # where PyYAML is available
    yaml_cmd = f"python -c \"import yaml; open('{config_file}', 'w').write(yaml.dump({config_data}, default_flow_style=False))\""
    return yaml_cmd

def setup_project():
    """Set up the VPS-IBR project environment."""
    venv_name = "venv"
    config_dir = Path("config")
    
    # Create virtual environment
    print_step(f"Creating virtual environment in {venv_name}")
    if os.path.exists(venv_name):
        response = input(f"Environment exists. Recreate? (y/N): ").lower()
        if response == 'y':
            import shutil
            shutil.rmtree(venv_name)
        else:
            print("Using existing environment")
    
    if not os.path.exists(venv_name):
        if not run_command([sys.executable, "-m", "venv", venv_name]):
            return False
    
    # Install dependencies
    print_step("Installing dependencies")
    if platform.system() == "Windows":
        pip_cmd = f"{venv_name}\\Scripts\\pip"
        activate_cmd = f"{venv_name}\\Scripts\\activate"
        cmd = f"{activate_cmd} && pip install --upgrade pip && pip install -e ."
    else:
        pip_cmd = f"{venv_name}/bin/pip"
        activate_cmd = f"source {venv_name}/bin/activate"
        cmd = f"bash -c '{activate_cmd} && pip install --upgrade pip && pip install -e .'"
    
    if not run_command(cmd, shell=True):
        print("Failed to install dependencies")
        return False
    
    # Set up config directory
    print_step("Setting up configuration")
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "servers_config.yaml"
    
    if not config_file.exists():
        examples_dir = Path("examples/config_examples")
        if examples_dir.exists() and list(examples_dir.glob("*.yaml")):
            sample = next(examples_dir.glob("*.yaml"))
            import shutil
            shutil.copy(sample, config_file)
            print(f"Created configuration from example: {config_file}")
        else:
            # Generate YAML config file using Python with PyYAML inside the virtual environment
            if platform.system() == "Windows":
                yaml_cmd = f"{activate_cmd} && " + write_yaml_config(config_file, SERVER_CONFIG)
            else:
                yaml_cmd = f"bash -c '{activate_cmd} && " + write_yaml_config(config_file, SERVER_CONFIG) + "'"
            
            if not run_command(yaml_cmd, shell=True):
                # Fallback: write a JSON file if YAML fails
                with open(config_dir / "servers_config.json", 'w') as f:
                    json.dump(SERVER_CONFIG, f, indent=2)
                print(f"Created basic configuration as JSON: {config_dir / 'servers_config.json'}")
                print("Note: You'll need to convert this to YAML format manually")
            else:
                print(f"Created basic configuration: {config_file}")
    
    # Show next steps
    print_step("Setup complete!")
    if platform.system() == "Windows":
        activate_cmd = f"{venv_name}\\Scripts\\activate"
    else:
        activate_cmd = f"source {venv_name}/bin/activate"
    
    print(f"""
To activate the virtual environment:
    {activate_cmd}

To run the tool:
    vps-ibr inventory --config config/servers_config.yaml
""")
    
    return True

if __name__ == "__main__":
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)
        
    success = setup_project()
    sys.exit(0 if success else 1) 