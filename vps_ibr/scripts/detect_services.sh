#!/bin/bash
# Script to detect running services and installed packages
# This is used by the VPS Inventory System

echo "-- RUNNING SERVICES --"
# Try systemctl if available
if command -v systemctl >/dev/null 2>&1; then
    systemctl list-units --type=service --state=running | grep '\.service' | awk '{print $1}'
# Try service command as fallback
elif command -v service >/dev/null 2>&1; then
    service --status-all 2>&1 | grep '\[ + \]' | awk '{print $4}'
# Last resort, check processes
else
    ps aux | grep -v grep | awk '{print $11}' | sort | uniq
fi

echo "-- ENABLED SERVICES --"
if command -v systemctl >/dev/null 2>&1; then
    systemctl list-unit-files --type=service --state=enabled | grep '\.service' | awk '{print $1}'
fi

echo "-- LISTENING PORTS --"
if command -v ss >/dev/null 2>&1; then
    ss -tulpn | grep LISTEN
elif command -v netstat >/dev/null 2>&1; then
    netstat -tulpn | grep LISTEN
fi

echo "-- PACKAGE MANAGER --"
if command -v apt >/dev/null 2>&1; then
    echo "APT"
elif command -v yum >/dev/null 2>&1; then
    echo "YUM"
elif command -v dnf >/dev/null 2>&1; then
    echo "DNF"
elif command -v pacman >/dev/null 2>&1; then
    echo "PACMAN"
elif command -v apk >/dev/null 2>&1; then
    echo "APK"
else
    echo "UNKNOWN"
fi

echo "-- WEB SERVERS --"
if command -v nginx >/dev/null 2>&1; then
    echo "NGINX:$(nginx -v 2>&1 | cut -d'/' -f2)"
    echo "-- NGINX SITES --"
    find /etc/nginx/sites-enabled/ -type f -or -type l | xargs basename 2>/dev/null || echo "None"
fi

if command -v apache2 >/dev/null 2>&1 || command -v httpd >/dev/null 2>&1; then
    APACHE_CMD="apache2"
    [ -x "$(command -v httpd)" ] && APACHE_CMD="httpd"
    echo "APACHE:$($APACHE_CMD -v | head -n1 | grep -o 'Apache.*/[0-9.]*' | cut -d'/' -f2)"
    echo "-- APACHE SITES --"
    if [ -d "/etc/apache2/sites-enabled/" ]; then
        find /etc/apache2/sites-enabled/ -type f -or -type l | xargs basename 2>/dev/null || echo "None"
    elif [ -d "/etc/httpd/conf.d/" ]; then
        find /etc/httpd/conf.d/ -name "*.conf" | xargs basename 2>/dev/null || echo "None"
    fi
fi

echo "-- DATABASES --"
if command -v mysql >/dev/null 2>&1 || command -v mariadb >/dev/null 2>&1; then
    DB_CMD="mysql"
    [ -x "$(command -v mariadb)" ] && DB_CMD="mariadb"
    echo "MYSQL:$($DB_CMD --version | head -n1 | grep -o 'Distrib [0-9.]*' | cut -d' ' -f2)"
    echo "-- MYSQL DATABASES --"
    echo "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys');" | sudo mysql -N 2>/dev/null || echo "Cannot list databases"
fi

if command -v psql >/dev/null 2>&1; then
    echo "POSTGRESQL:$(psql --version | grep -o '[0-9.]*' | head -n1)"
    echo "-- POSTGRESQL DATABASES --"
    sudo -u postgres psql -c "SELECT datname FROM pg_database WHERE datistemplate = false;" 2>/dev/null || echo "Cannot list databases"
fi

echo "-- CONTAINERIZATION --"
if command -v docker >/dev/null 2>&1; then
    echo "DOCKER:$(docker --version | cut -d' ' -f3 | tr -d ',')"
    echo "-- DOCKER CONTAINERS --"
    docker ps --format "{{.Names}}" 2>/dev/null || echo "Cannot list containers"
fi

if command -v podman >/dev/null 2>&1; then
    echo "PODMAN:$(podman --version | cut -d' ' -f3)"
fi

if command -v kubectl >/dev/null 2>&1; then
    echo "KUBERNETES:$(kubectl version --client 2>/dev/null | grep -o 'GitVersion:\"v[0-9.]*\"' | head -n1 | cut -d'"' -f2 | tr -d 'v')"
fi

echo "-- PROGRAMMING LANGUAGES --"
if command -v python3 >/dev/null 2>&1; then
    echo "PYTHON:$(python3 --version 2>&1 | cut -d' ' -f2)"
fi

if command -v python2 >/dev/null 2>&1; then
    echo "PYTHON2:$(python2 --version 2>&1 | cut -d' ' -f2)"
fi

if command -v node >/dev/null 2>&1; then
    echo "NODEJS:$(node --version | tr -d 'v')"
fi

if command -v ruby >/dev/null 2>&1; then
    echo "RUBY:$(ruby --version | cut -d' ' -f2)"
fi

if command -v php >/dev/null 2>&1; then
    echo "PHP:$(php --version | head -n1 | grep -o 'PHP [0-9.]*' | cut -d' ' -f2)"
fi

if command -v go >/dev/null 2>&1; then
    echo "GO:$(go version | grep -o 'go[0-9.]*' | tr -d 'go')"
fi

echo "-- CRON JOBS --"
find /var/spool/cron/ -type f 2>/dev/null | xargs cat 2>/dev/null || echo "None"
cat /etc/crontab 2>/dev/null
find /etc/cron.d/ -type f 2>/dev/null | xargs cat 2>/dev/null

echo "-- CUSTOM SERVICES --"
# Look for custom systemd services
find /etc/systemd/system/ -name "*.service" -type f 2>/dev/null | sort

# Look for init.d scripts
find /etc/init.d/ -type f -executable 2>/dev/null | sort

echo "-- END OF SERVICE DETECTION --"