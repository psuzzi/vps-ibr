#!/bin/bash
# Script to extract user information from a server
# This is used by the VPS Inventory System

# Get all regular users (UID >= 1000 and not nobody)
echo "-- USERS --"
awk -F: '$3 >= 1000 && $3 != 65534 {print $1 ":" $6}' /etc/passwd

# Get sudo users
echo "-- SUDO USERS --"
getent group sudo | cut -d: -f4
grep -v '^#' /etc/sudoers | grep -v '^Defaults' | grep 'ALL=(ALL:ALL)' | cut -d' ' -f1

# Get groups
echo "-- GROUPS --"
getent group | grep -v "^nobody" | awk -F: '$3 >= 1000 {print $1 ":" $3 ":" $4}'

# Last logins
echo "-- LAST LOGINS --"
last -n 20 | grep -v "^reboot" | grep -v "^wtmp"

# User processes
echo "-- USER PROCESSES --"
ps aux | grep -v "^root" | grep -v "^nobody" | awk '{print $1 ":" $11}' | sort | uniq

# SSH authorized keys
echo "-- SSH KEYS --"
for user in $(awk -F: '$3 >= 1000 && $3 != 65534 {print $1 ":" $6}' /etc/passwd)
do
    username=$(echo $user | cut -d: -f1)
    homedir=$(echo $user | cut -d: -f2)
    
    if [ -f "$homedir/.ssh/authorized_keys" ]; then
        echo "USER: $username"
        cat "$homedir/.ssh/authorized_keys" | wc -l
    fi
done

# Root SSH keys
if [ -f "/root/.ssh/authorized_keys" ]; then
    echo "USER: root"
    cat "/root/.ssh/authorized_keys" | wc -l
fi