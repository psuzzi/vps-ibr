#!/usr/bin/env python3
"""
Command Line Interface for the VPS Inventory, Backup & Restore tool.
"""
import os
import sys
import click

from vps_ibr.config import load_config
from vps_ibr.inventory.collector import create_inventory
from vps_ibr.backup.manager import create_backup
from vps_ibr.restore.manager import restore_server

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='0.1.0')
def cli():
    """VPS Inventory, Backup & Restore - Manage your VPS instances with ease."""
    pass

@cli.command()
@click.option(
    '--config', '-c', 
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help='Path to configuration file',
    required=True
)
@click.option(
    '--output-dir', '-o',
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    help='Directory to store inventory results (defaults to auto-generated name)',
    default=None
)
def inventory(config, output_dir):
    """Collect inventory from configured servers."""
    try:
        click.echo(f"Loading configuration from {config}")
        conf = load_config(config)
        if not conf:
            click.echo("Failed to load configuration.", err=True)
            sys.exit(1)
            
        click.echo("Starting inventory collection...")
        output = create_inventory(conf, output_dir)
        click.echo(f"Inventory completed. Results stored in: {output}")
    except Exception as e:
        click.echo(f"Error during inventory collection: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option(
    '--config', '-c', 
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help='Path to configuration file',
    required=True
)
@click.option(
    '--server', '-s',
    help='IP of the server to backup (default: all servers)',
    default=None
)
@click.option(
    '--output-dir', '-o',
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    help='Directory to store backup results',
    default=None
)
def backup(config, server, output_dir):
    """Create backups of configured servers."""
    try:
        click.echo(f"Loading configuration from {config}")
        conf = load_config(config)
        if not conf:
            click.echo("Failed to load configuration.", err=True)
            sys.exit(1)
            
        click.echo("Starting backup process...")
        # In the future, implement create_backup
        click.echo("Backup functionality not yet implemented.")
    except Exception as e:
        click.echo(f"Error during backup process: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option(
    '--backup-dir', '-b', 
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    help='Path to backup directory',
    required=True
)
@click.option(
    '--target-ip', '-t',
    help='IP of the target server for restoration',
    required=True
)
@click.option(
    '--ssh-key', '-k',
    help='SSH key to use for the target server',
    default=None
)
def restore(backup_dir, target_ip, ssh_key):
    """Restore a server from backup."""
    try:
        click.echo(f"Preparing to restore from {backup_dir} to {target_ip}")
        # In the future, implement restore_server
        click.echo("Restore functionality not yet implemented.")
    except Exception as e:
        click.echo(f"Error during restore process: {e}", err=True)
        sys.exit(1)

def main():
    """Main entry point for the CLI."""
    cli()

if __name__ == "__main__":
    main()