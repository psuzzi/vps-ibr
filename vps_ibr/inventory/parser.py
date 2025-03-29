#!/usr/bin/env python3
"""
Parser module for bash history and installed services detection.
"""
import re
import os
from typing import Dict, List, Set, Any, Tuple

# Regular expressions for common package managers and commands
PACKAGE_PATTERNS = {
    "apt": [
        r"apt(-get)?\s+install\s+([a-zA-Z0-9\-\.]+)",
        r"apt(-get)?\s+install\s+(-y\s+)?([a-zA-Z0-9\-\.]+)"
    ],
    "yum": [
        r"yum\s+install\s+([a-zA-Z0-9\-\.]+)",
        r"yum\s+install\s+(-y\s+)?([a-zA-Z0-9\-\.]+)"
    ],
    "dnf": [
        r"dnf\s+install\s+([a-zA-Z0-9\-\.]+)",
        r"dnf\s+install\s+(-y\s+)?([a-zA-Z0-9\-\.]+)"
    ],
    "pip": [
        r"pip\s+install\s+([a-zA-Z0-9\-\.]+)",
        r"pip3\s+install\s+([a-zA-Z0-9\-\.]+)"
    ],
    "npm": [
        r"npm\s+install\s+(-g\s+)?([a-zA-Z0-9\-\.@/]+)"
    ],
    "docker": [
        r"docker\s+run\s+.*\s+([a-zA-Z0-9\-\./]+:[a-zA-Z0-9\-\.]+)",
        r"docker\s+pull\s+([a-zA-Z0-9\-\./]+:[a-zA-Z0-9\-\.]+)"
    ]
}

# Patterns for service management
SERVICE_PATTERNS = [
    r"systemctl\s+(start|enable|restart|status)\s+([a-zA-Z0-9\-\.]+)",
    r"service\s+([a-zA-Z0-9\-\.]+)\s+(start|restart|stop|status)"
]

# Patterns for user management
USER_PATTERNS = [
    r"useradd\s+(-m\s+)?([a-zA-Z0-9\-\_]+)",
    r"adduser\s+([a-zA-Z0-9\-\_]+)"
]

def parse_bash_history(history_file: str) -> Dict[str, Any]:
    """
    Parse bash history file to detect installed packages, services, and users.
    
    Args:
        history_file: Path to bash history file
        
    Returns:
        Dictionary with detected packages, services, and users
    """
    if not os.path.exists(history_file) or os.path.getsize(history_file) == 0:
        return {
            "packages": {},
            "services": [],
            "users": []
        }
    
    with open(history_file, 'r', encoding='utf-8', errors='ignore') as f:
        history_content = f.readlines()
    
    # Initialize result dictionary
    result = {
        "packages": {},
        "services": [],
        "users": []
    }
    
    # Extract packages by package manager
    for pkg_manager, patterns in PACKAGE_PATTERNS.items():
        result["packages"][pkg_manager] = find_matches(history_content, patterns)
    
    # Extract services
    result["services"] = find_matches(history_content, SERVICE_PATTERNS)
    
    # Extract users
    result["users"] = find_matches(history_content, USER_PATTERNS)
    
    return result

def find_matches(lines: List[str], patterns: List[str]) -> List[str]:
    """
    Find matches in lines using regex patterns.
    
    Args:
        lines: List of text lines to search
        patterns: List of regex patterns to match
        
    Returns:
        List of unique matches
    """
    matches = set()
    
    for line in lines:
        line = line.strip()
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                # Get the last group which should be the item name
                item = match.group(match.lastindex or 1).strip()
                if item:
                    matches.add(item)
    
    return sorted(list(matches))

def analyze_server_history(server_dir: str) -> Dict[str, Any]:
    """
    Analyze all bash histories in a server directory to identify services and configurations.
    
    Args:
        server_dir: Path to server directory containing user histories
        
    Returns:
        Dictionary with consolidated analysis
    """
    users_dir = os.path.join(server_dir, "users")
    if not os.path.exists(users_dir):
        return {}
    
    server_analysis = {
        "packages": {},
        "services": set(),
        "users_created": set(),
        "by_user": {}
    }
    
    # Check each user's bash history
    for user in os.listdir(users_dir):
        user_dir = os.path.join(users_dir, user)
        history_file = os.path.join(user_dir, "bash_history")
        
        if os.path.exists(history_file):
            user_analysis = parse_bash_history(history_file)
            
            # Store user-specific analysis
            server_analysis["by_user"][user] = user_analysis
            
            # Consolidate packages
            for pkg_manager, packages in user_analysis["packages"].items():
                if pkg_manager not in server_analysis["packages"]:
                    server_analysis["packages"][pkg_manager] = set()
                server_analysis["packages"][pkg_manager].update(packages)
            
            # Consolidate services
            server_analysis["services"].update(user_analysis["services"])
            
            # Consolidate users
            server_analysis["users_created"].update(user_analysis["users"])
    
    # Convert sets to sorted lists for clean output
    for pkg_manager in server_analysis["packages"]:
        server_analysis["packages"][pkg_manager] = sorted(list(server_analysis["packages"][pkg_manager]))
    
    server_analysis["services"] = sorted(list(server_analysis["services"]))
    server_analysis["users_created"] = sorted(list(server_analysis["users_created"]))
    
    return server_analysis