#!/usr/bin/env python3
"""
USB Reset utility for LM360
"""
import fcntl
import sys

USBDEVFS_RESET = 0x5514

def reset_usb_device(dev_path):
    try:
        with open(dev_path, 'w') as f:
            fcntl.ioctl(f, USBDEVFS_RESET, 0)
        print(f"✓ USB device reset: {dev_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to reset: {e}")
        return False

if __name__ == "__main__":
    dev_path = "/dev/bus/usb/001/010"
    print(f"Resetting USB device: {dev_path}")
    reset_usb_device(dev_path)
