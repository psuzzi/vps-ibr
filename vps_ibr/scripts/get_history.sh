#!/bin/bash
# Script to safely extract bash history for a user
# This is used by the VPS Inventory System

# Check if a username was provided
if [ -z "$1" ]; then
    echo "Usage: $0 <username>"
    exit 1
fi

USERNAME="$1"
HISTORY_FILE=""

# Find the user's home directory
USER_HOME=$(getent passwd "$USERNAME" | cut -d: -f6)

if [ -z "$USER_HOME" ]; then
    echo "Error: User $USERNAME not found"
    exit 1
fi

# Check for bash history file
if [ -f "$USER_HOME/.bash_history" ]; then
    HISTORY_FILE="$USER_HOME/.bash_history"
elif [ -f "$USER_HOME/.history" ]; then
    HISTORY_FILE="$USER_HOME/.history"
fi

if [ -z "$HISTORY_FILE" ]; then
    echo "No history file found for user $USERNAME"
    exit 0
fi

# Check if we can read the history file
if [ ! -r "$HISTORY_FILE" ]; then
    echo "Cannot read history file for user $USERNAME"
    exit 1
fi

# Output the history file
cat "$HISTORY_FILE"