#!/usr/bin/env python3
"""
Unit tests for the inventory module.
"""
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from vps_ibr.inventory.collector import get_users, get_sudo_users, copy_bash_history
from vps_ibr.inventory.parser import parse_bash_history
# from vps_ibr.utils.file_utils import ensure_dir, save_json  # In backup/manager.py
# from vps_ibr.utils.file_utils import ensure_dir, load_json  # In restore/manager.py

class TestInventoryCollector(unittest.TestCase):
    """Tests for the inventory collector module."""

    @patch('vps_ibr.utils.ssh.run_ssh_command')
    def test_get_users(self, mock_run_ssh_command):
        """Test getting users from a server."""
        # Mock SSH command output
        mock_run_ssh_command.return_value = (
            "user1:/home/user1\n"
            "user2:/home/user2\n"
        )
        
        # Call function
        users = get_users('192.0.2.10', '/path/to/key')
        
        # Check results
        self.assertEqual(len(users), 3)  # 2 regular users + root
        self.assertEqual(users[0]['username'], 'user1')
        self.assertEqual(users[0]['home'], '/home/user1')
        self.assertEqual(users[1]['username'], 'user2')
        self.assertEqual(users[1]['home'], '/home/user2')
        self.assertEqual(users[2]['username'], 'root')
        self.assertEqual(users[2]['home'], '/root')
        
        # Verify SSH command
        mock_run_ssh_command.assert_called_once()
        args, _ = mock_run_ssh_command.call_args
        self.assertEqual(args[0], '192.0.2.10')
        self.assertEqual(args[1], '/path/to/key')
        self.assertIn('awk', args[2])

    @patch('vps_ibr.utils.ssh.run_ssh_command')
    def test_get_sudo_users(self, mock_run_ssh_command):
        """Test getting sudo users from a server."""
        # Mock SSH command outputs
        mock_run_ssh_command.side_effect = [
            "user1,user2",  # Output from sudo group
            "user3"         # Output from sudoers file
        ]
        
        # Call function
        sudo_users = get_sudo_users('192.0.2.10', '/path/to/key')
        
        # Check results
        self.assertEqual(len(sudo_users), 3)
        self.assertIn('user1', sudo_users)
        self.assertIn('user2', sudo_users)
        self.assertIn('user3', sudo_users)
        
        # Verify SSH commands
        self.assertEqual(mock_run_ssh_command.call_count, 2)

    def test_parse_bash_history(self):
        """Test parsing bash history."""
        # Create a temporary bash history file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            f.write("apt-get update\n")
            f.write("apt-get install nginx\n")
            f.write("systemctl start nginx\n")
            f.write("useradd -m testuser\n")
            history_file = f.name
        
        try:
            # Parse the history file
            result = parse_bash_history(history_file)
            
            # Check the results
            self.assertIn('apt', result['packages'])
            self.assertIn('nginx', result['packages']['apt'])
            self.assertIn('nginx', result['services'])
            self.assertIn('testuser', result['users'])
        finally:
            # Clean up the temporary file
            os.unlink(history_file)

if __name__ == '__main__':
    unittest.main()