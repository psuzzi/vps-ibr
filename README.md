# VPS Inventory, Backup & Restore (VPS-IBR)

A comprehensive tool for managing virtual private servers - inventory tracking, backup creation, and automated restoration.

## Features

- **Inventory Collection**: Automatically collect information about users, installed services, and configurations
- **Smart Backup**: Create targeted backups based on detected services and data
- **Automated Restore**: Quickly restore a server from backups with minimal manual intervention
- **Multi-Provider Support**: Works with DigitalOcean, IONOS, and other VPS providers

## Installation

```bash
# Clone the repository
git clone https://github.com/psuzzi/vps-ibr.git
cd vps-ibr

# Install the package
pip install -e .
```

### Note for Users: 
- The installation step with `pip install -e` registers the command-line entry point `vpr-ibs` in your environment, making it available from anywhere. 

### Note for Developers:
- The installation process uses the `setup.py` and `pyproject.toml` files to register the entry point defined in the project configuration: `vps-ibr = "vps_ibr.cli:main"`.
- If you want to run it directly during development, you can execute the cli module directly:
    ```bash
    # From vps-ibr/
    python -m vps_ibr.cli inventory --config myconfig.yaml
    ```

## Requirements

- Python 3.8+
- SSH access to target VPS instances (root or sudo privileges)
- SSH key-based authentication configured

## Quick Start

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
