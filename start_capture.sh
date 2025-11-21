#!/bin/bash
# Start USB packet capture

CAPTURE_FILE="$HOME/lm360_capture_$(date +%Y%m%d_%H%M%S).txt"

echo "============================================================"
echo "Starting USB Packet Capture"
echo "============================================================"
echo
echo "Capture file: $CAPTURE_FILE"
echo
echo "This will capture ALL USB traffic on Bus 001"
echo "Press Ctrl+C to stop capturing"
echo
echo "Now go to Windows and use the Deepcool software!"
echo
echo "============================================================"

sudo cat /sys/kernel/debug/usb/usbmon/1u > "$CAPTURE_FILE"

echo
echo "Capture stopped!"
echo "Saved to: $CAPTURE_FILE"
echo "File size: $(ls -lh "$CAPTURE_FILE" | awk '{print $5}')"
