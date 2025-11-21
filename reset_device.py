#!/usr/bin/env python3
"""
Try to perform a USB device reset
"""
import usb.core
import usb.util
import sys
import time

VENDOR_ID = 0x3633
PRODUCT_ID = 0x0026

def main():
    print("="*70)
    print("LM360 USB Device Reset")
    print("="*70)

    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

    if device is None:
        print("✗ Device not found!")
        sys.exit(1)

    print("✓ Device found")
    print("\nAttempting USB reset...")

    try:
        device.reset()
        print("✓ USB reset successful!")
        print("\nWait 3 seconds for device to re-enumerate...")
        time.sleep(3)
        print("\nNow try running: sudo uv run lcd_probe.py")

    except Exception as e:
        print(f"✗ Reset failed: {e}")
        print("\nPhysical reset needed:")
        print("  1. Unplug the USB cable from the LM360")
        print("  2. Wait 5 seconds")
        print("  3. Plug it back in")
        print("  4. Run: sudo uv run lcd_probe.py")

if __name__ == "__main__":
    main()
