#!/bin/bash
# Capture ONLY the mode switch commands

CAPTURE_FILE="$HOME/lm360_mode_switch_$(date +%Y%m%d_%H%M%S).txt"

echo "============================================================"
echo "Focused USB Capture - Mode Switching ONLY"
echo "============================================================"
echo
echo "This will capture USB commands when you switch modes"
echo
echo "INSTRUCTIONS:"
echo "1. Start capture (press ENTER when ready)"
echo "2. In Windows, CLICK to switch from Data Mode to Image Mode"
echo "3. Wait 2 seconds"
echo "4. CLICK to switch from Image Mode back to Data Mode"
echo "5. Wait 2 seconds"
echo "6. Come back here and press Ctrl+C"
echo
echo "Capture file: $CAPTURE_FILE"
echo "============================================================"
echo
read -p "Press ENTER to start capture..."

echo "CAPTURING! Go to Windows and switch modes NOW!"
echo "Press Ctrl+C when done..."

sudo cat /sys/kernel/debug/usb/usbmon/1u > "$CAPTURE_FILE"

echo
echo "Capture stopped!"
echo "Saved to: $CAPTURE_FILE"
echo
echo "Now run: python3 analyze_capture.py $CAPTURE_FILE"
