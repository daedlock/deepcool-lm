#!/bin/bash
set -e

echo "=========================================="
echo "  Deepcool LM Series LCD Driver Uninstaller"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: This script must be run as root"
    echo "   Please run: sudo ./uninstall.sh"
    exit 1
fi

# Stop and remove old lm360 service
if systemctl is-active --quiet lm360.service 2>/dev/null; then
    echo "🛑 Stopping old lm360 service..."
    systemctl stop lm360.service
fi
if systemctl is-enabled --quiet lm360.service 2>/dev/null; then
    systemctl disable lm360.service
fi
if [ -f /etc/systemd/system/lm360.service ]; then
    rm /etc/systemd/system/lm360.service
fi
if [ -f /usr/local/bin/lm360 ]; then
    rm /usr/local/bin/lm360
fi

# Stop deepcool-lm service if running
if systemctl is-active --quiet deepcool-lm.service 2>/dev/null; then
    echo "🛑 Stopping service..."
    systemctl stop deepcool-lm.service
    echo "✓ Service stopped"
fi

# Disable service if enabled
if systemctl is-enabled --quiet deepcool-lm.service 2>/dev/null; then
    echo "🔓 Disabling service..."
    systemctl disable deepcool-lm.service
    echo "✓ Service disabled"
fi

# Remove systemd service
if [ -f /etc/systemd/system/deepcool-lm.service ]; then
    echo "🗑️  Removing systemd service..."
    rm /etc/systemd/system/deepcool-lm.service
    systemctl daemon-reload
    echo "✓ Service removed"
fi

# Remove CLI tool
if [ -f /usr/local/bin/deepcool-lm ]; then
    echo "🗑️  Removing CLI tool..."
    rm /usr/local/bin/deepcool-lm
    echo "✓ CLI tool removed"
fi

# Remove socket files
rm -f /var/run/lm360.sock /var/run/deepcool-lm.sock 2>/dev/null || true

echo ""
echo "=========================================="
echo "  Uninstallation Complete!"
echo "=========================================="
echo ""
echo "All Deepcool LM series driver components have been removed."
echo "The display will return to default behavior or turn off."
echo ""
