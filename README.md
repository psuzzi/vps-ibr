# VPS Inventory, Backup & Restore (VPS-IBR)

A comprehensive tool for managing virtual private servers - inventory tracking, backup creation, and automated restoration.

## Features

- **Inventory Collection**: Automatically collect information about users, installed services, and configurations
- **Smart Backup**: Create targeted backups based on detected services and data
- **Automated Restore**: Quickly restore a server from backups with minimal manual intervention
- **Multi-Provider Support**: Works with any VPS offering SSH key-based authentication

## Requirements

- Python 3.8+
- SSH access to target VPS instances (root or sudo privileges)
- SSH key-based authentication configured

## Setup

```bash
# Clone the repository
git clone https://github.com/psuzzi/vps-ibr.git
cd vps-ibr
```

## Installation

Installing with `pip install -e .` registers the command `vps-ibr` in your Python environment based on configurations in `setup.py` and `pyproject.toml`. This command points to the function `vps_ibr.cli:main`. The `-e` flag enables development mode, so any changes to the source code are immediately reflected when running the command.

```bash
# Install the package
pip install -e .
```

## Development 

The `quickstart.py` script creates a sample configuration file, sets up an isolated `venv` environment using dependencies from `pyproject.toml`, activates it, and runs `pip install -e .` (in the isolated environment). This is the preferred approach for development, dependency management, and iterative testing.

```bash
# Set up dev environment and install
python quickstart.py

# Later, activate the venv via command line or in your IDE
```

### Note:

- Installing with `pip install -e` registers the command-line tool in development mode, so code changes are immediately reflected when running the program with the `vps-ibr` command.
- If needed in development, you can also run the module directly:

```bash
# From vps-ibr/
python -m vps_ibr.cli inventory --config myconfig.yaml
```



## Usage

1. Create a configuration file based on the example:

```bash
cp examples/config_examples/servers_config.yaml myconfig.yaml
```

2. Edit the configuration file with your server details:

```yaml
# Example configuration (replace with your servers)
servers:
  - ip: "192.0.2.10"
    description: "Web Server"
    ssh_key: "id_rsa_example"
```

3. Run the inventory collection:

```bash
vps-ibr inventory --config myconfig.yaml
```

## Configuration

The tool uses YAML configuration files to define server details and backup preferences. See the `examples/config_examples/` directory for sample configurations.

### Server Configuration

```yaml
servers:
  - ip: "192.0.2.10"
    description: "Primary web server"
    ssh_key: "id_rsa_example"
    
global:
  default_ssh_key: "id_rsa"
  ssh_key_path: "~/.ssh"
  timeout: 30
```

## Usage

### Collecting Inventory

```bash
vps-ibr inventory --config myconfig.yaml
```

### Creating Backups

```bash
vps-ibr backup --config myconfig.yaml --server 192.0.2.10
```

### Restoring a Server

```bash
vps-ibr restore --backup-dir ibr-20250320-120000/192.0.2.10-20250320 --target-ip 192.0.2.20
```

## Project Structure

- `vps_ibr/`: Main package code
- `examples/`: Example configurations and outputs
- `tests/`: Test suite for the project

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the [MIT License](LICENSE).
