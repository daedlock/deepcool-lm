#!/bin/bash
set -e

echo "=========================================="
echo "  Deepcool LM Series LCD Driver Installer"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: This script must be run as root"
    echo "   Please run: sudo ./install.sh"
    exit 1
fi

# Download files if not present (for curl | bash installation)
REPO_URL="https://raw.githubusercontent.com/daedlock/deepcool-lm/main"
TEMP_DIR=$(mktemp -d)

download_file() {
    local file=$1
    if [ ! -f "$file" ]; then
        echo "📥 Downloading $file..."
        curl -fsSL "$REPO_URL/$file" -o "$TEMP_DIR/$file"
        FILE_SOURCE="$TEMP_DIR"
    else
        FILE_SOURCE="."
    fi
}

# Check if we need to download files
if [ ! -f "deepcool-lm" ] || [ ! -f "deepcool-lm.service" ]; then
    echo "📥 Downloading driver files from GitHub..."
    download_file "deepcool-lm"
    download_file "deepcool-lm.service"
else
    FILE_SOURCE="."
fi

# Check for lm_sensors
echo "🔍 Checking for lm_sensors..."
if ! systemctl is-enabled --quiet lm_sensors.service 2>/dev/null; then
    echo "⚠️  Warning: lm_sensors service not found or not enabled"
    echo "   Temperature monitoring requires lm_sensors"
    echo ""
    echo "   To install and configure lm_sensors:"
    echo "   - Arch: sudo pacman -S lm_sensors && sudo sensors-detect"
    echo "   - Ubuntu: sudo apt install lm-sensors && sudo sensors-detect"
    echo ""
    read -p "   Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ lm_sensors service found"
fi

# Check if device is connected
echo "🔍 Checking for Deepcool LM series device..."
if ! lsusb | grep -q "3633:0026"; then
    echo "⚠️  Warning: Deepcool LM series device not detected (VID:PID 3633:0026)"
    echo "   Make sure your LM series cooler is plugged in (tested: LM360)"
    read -p "   Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Deepcool LM series device detected"
fi

# Stop old service if running
if systemctl is-active --quiet lm360.service 2>/dev/null; then
    echo "🛑 Stopping old lm360 service..."
    systemctl stop lm360.service
    systemctl disable lm360.service 2>/dev/null || true
fi

# Stop new service if running
if systemctl is-active --quiet deepcool-lm.service 2>/dev/null; then
    echo "🛑 Stopping existing service..."
    systemctl stop deepcool-lm.service
fi

# Install CLI tool
echo "📦 Installing deepcool-lm CLI tool..."
cp "$FILE_SOURCE/deepcool-lm" /usr/local/bin/deepcool-lm
chmod +x /usr/local/bin/deepcool-lm
echo "✓ Installed to /usr/local/bin/deepcool-lm"

# Install systemd service
echo "📦 Installing systemd service..."
cp "$FILE_SOURCE/deepcool-lm.service" /etc/systemd/system/deepcool-lm.service
systemctl daemon-reload
echo "✓ Service installed"

# Ask to enable and start service
echo ""
read -p "Enable service to start on boot? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    systemctl enable deepcool-lm.service
    echo "✓ Service enabled for startup"
fi

echo ""
read -p "Start service now? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    systemctl start deepcool-lm.service
    sleep 1
    if systemctl is-active --quiet deepcool-lm.service; then
        echo "✓ Service started successfully"
    else
        echo "❌ Service failed to start. Check logs with: journalctl -u deepcool-lm -n 50"
    fi
fi

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "Usage:"
echo "  Start service:     sudo systemctl start deepcool-lm"
echo "  Stop service:      sudo systemctl stop deepcool-lm"
echo "  Service status:    sudo systemctl status deepcool-lm"
echo "  View logs:         sudo journalctl -u deepcool-lm -f"
echo ""
echo "CLI Commands:"
echo "  System monitor:    sudo deepcool-lm monitor"
echo "  Display image:     sudo deepcool-lm image /path/to/image.jpg"
echo "  Display color:     sudo deepcool-lm solid --color 255 0 0"
echo "  Brightness up:     sudo deepcool-lm brightness up"
echo "  Brightness down:   sudo deepcool-lm brightness down"
echo ""
echo "Run 'deepcool-lm --help' for more options"
echo ""

# Cleanup temp directory if we downloaded files
if [ "$FILE_SOURCE" = "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
fi
