#!/bin/bash
# USB Packet Capture Setup Script

set -e

echo "============================================================"
echo "LM360 USB Packet Capture Setup"
echo "============================================================"
echo

# Check if LM360 is connected
echo "[1] Checking for LM360..."
if ! lsusb | grep -q "3633:0026"; then
    echo "ERROR: LM360 not found! Make sure it's plugged in."
    exit 1
fi
echo "✓ LM360 detected"
echo

# Check USB monitoring
echo "[2] Checking usbmon..."
if ! lsmod | grep -q usbmon; then
    echo "Loading usbmon module..."
    sudo modprobe usbmon
fi
echo "✓ usbmon loaded"
echo

# Create USB device XML
echo "[3] Creating USB passthrough config..."
cat > /tmp/lm360-usb.xml <<'EOF'
<hostdev mode='subsystem' type='usb'>
  <source>
    <vendor id='0x3633'/>
    <product id='0x0026'/>
  </source>
</hostdev>
EOF
echo "✓ Config created at /tmp/lm360-usb.xml"
echo

# Check if win11 VM exists
echo "[4] Checking for win11 VM..."
if ! virsh list --all | grep -q "win11"; then
    echo "ERROR: VM 'win11' not found!"
    echo "Available VMs:"
    virsh list --all
    exit 1
fi
echo "✓ win11 VM found"
echo

# Start VM if not running
echo "[5] Starting win11 VM..."
if virsh list | grep -q "win11.*running"; then
    echo "✓ VM already running"
else
    virsh start win11
    echo "✓ VM started"
    echo "Waiting 10 seconds for VM to boot..."
    sleep 10
fi
echo

# Attach USB device to VM
echo "[6] Attaching LM360 to Windows VM..."
if sudo virsh attach-device win11 /tmp/lm360-usb.xml --live; then
    echo "✓ USB device attached to VM"
else
    echo "Warning: Attach may have failed, check manually"
fi
echo

# Verify device is passed through
echo "[7] Verifying passthrough..."
echo "On Linux host, LM360 should NOT appear in lsusb:"
if lsusb | grep -q "3633:0026"; then
    echo "⚠ WARNING: Device still visible on host (may not be passed through)"
else
    echo "✓ Device passed to VM successfully"
fi
echo

echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo
echo "NEXT STEPS:"
echo
echo "1. Open your Windows VM (virt-manager or RDP)"
echo "2. In Windows, open Device Manager and look for 'DC LM-Series'"
echo "3. Download software from: www.cryoex.com"
echo "4. Install and run the Deepcool software"
echo
echo "While you're doing that, run this in ANOTHER TERMINAL:"
echo "  sudo cat /sys/kernel/debug/usb/usbmon/1u > ~/lm360_capture.txt"
echo
echo "Or use the automated capture script:"
echo "  ./start_capture.sh"
echo
echo "When done, detach USB:"
echo "  sudo virsh detach-device win11 /tmp/lm360-usb.xml --live"
echo
