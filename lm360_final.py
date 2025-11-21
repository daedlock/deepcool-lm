#!/usr/bin/env python3
"""
Final LM360 Linux Driver
Control display modes, brightness, and zen mode
"""
import usb.core
import usb.util
import sys
import time
import psutil
import argparse

VENDOR_ID = 0x3633
PRODUCT_ID = 0x0026
EP_OUT = 0x01

class LM360Driver:
    """Deepcool LM360 LCD Display Driver"""

    # Commands from USB capture
    CMD_INIT = bytes([0xaa, 0x04, 0x00, 0x03, 0x00, 0x00, 0x00, 0xdc, 0x9b])
    CMD_MODE_1 = bytes([0xaa, 0x04, 0x00, 0x06, 0x03, 0x1d, 0x00, 0xe6, 0x0b])
    CMD_MODE_2 = bytes([0xaa, 0x04, 0x00, 0x06, 0x03, 0x47, 0x00, 0x92, 0xea])
    CMD_MODE_3 = bytes([0xaa, 0x04, 0x00, 0x06, 0x03, 0x61, 0x00, 0xd2, 0x46])

    def __init__(self):
        self.dev = None
        self.interface = 0

    def connect(self):
        """Connect to LM360 device"""
        self.dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
        if self.dev is None:
            return False

        if self.dev.is_kernel_driver_active(self.interface):
            try:
                self.dev.detach_kernel_driver(self.interface)
            except:
                pass

        try:
            self.dev.set_configuration()
            usb.util.claim_interface(self.dev, self.interface)
        except:
            return False

        return True

    def write(self, data):
        """Write data to device"""
        try:
            return self.dev.write(EP_OUT, data, timeout=1000)
        except Exception as e:
            print(f"Write error: {e}")
            return 0

    def init(self):
        """Initialize display (show logo)"""
        self.write(self.CMD_INIT)

    def set_mode_data(self):
        """Switch to data mode (system info)"""
        # Based on your testing, figure out which command is data mode
        # Try mode 1 first
        self.write(self.CMD_MODE_1)

    def set_mode_image(self):
        """Switch to image mode (custom uploaded image)"""
        # Try mode 2 or 3
        self.write(self.CMD_MODE_2)

    def set_zen_mode(self):
        """Enable zen mode"""
        self.write(self.CMD_INIT)  # You said first command opens zen mode

    def set_brightness(self, level):
        """
        Set brightness level
        Based on your testing, one of the modes changes brightness
        """
        # This is a guess - adjust based on testing
        self.write(self.CMD_MODE_3)

    def disconnect(self):
        """Disconnect from device"""
        if self.dev:
            try:
                usb.util.release_interface(self.dev, self.interface)
                usb.util.dispose_resources(self.dev)
            except:
                pass

def get_cpu_temp():
    """Get CPU temperature"""
    try:
        temps = psutil.sensors_temperatures()
        if 'k10temp' in temps:
            return round(temps['k10temp'][0].current)
        elif 'coretemp' in temps:
            return round(temps['coretemp'][0].current)
        for name, entries in temps.items():
            if entries:
                return round(entries[0].current)
    except:
        pass
    return 0

def get_gpu_temp():
    """Get GPU temperature"""
    try:
        temps = psutil.sensors_temperatures()
        if 'amdgpu' in temps:
            return round(temps['amdgpu'][0].current)
        elif 'nvidia' in temps:
            return round(temps['nvidia'][0].current)
    except:
        pass
    return 0

def main():
    parser = argparse.ArgumentParser(description='Deepcool LM360 Linux Driver')
    parser.add_argument('command', choices=['init', 'data', 'image', 'zen', 'test', 'monitor'],
                       help='Command to execute')
    parser.add_argument('--brightness', type=int, choices=range(0, 101),
                       help='Brightness level 0-100')

    args = parser.parse_args()

    print("="*70)
    print("Deepcool LM360 Linux Driver")
    print("="*70)
    print()

    driver = LM360Driver()

    if not driver.connect():
        print("✗ Failed to connect to LM360")
        print("  - Is the device plugged in? (check with: lsusb | grep 3633)")
        print("  - Are you running with sudo?")
        print("  - Is it attached to a VM? (detach it first)")
        sys.exit(1)

    print("✓ Connected to LM360")
    print()

    try:
        if args.command == 'init':
            print("Initializing display (logo/zen mode)...")
            driver.init()
            time.sleep(2)
            print("✓ Done")

        elif args.command == 'data':
            print("Switching to DATA mode (system info)...")
            driver.set_mode_data()
            time.sleep(2)
            print("✓ Done")
            print("\nIf this didn't show system data, the mode mapping is wrong.")
            print("Try: sudo uv run lm360_final.py image")

        elif args.command == 'image':
            print("Switching to IMAGE mode (custom image)...")
            driver.set_mode_image()
            time.sleep(2)
            print("✓ Done")

        elif args.command == 'zen':
            print("Enabling ZEN mode...")
            driver.set_zen_mode()
            time.sleep(2)
            print("✓ Done")

        elif args.command == 'test':
            print("Testing all modes...")
            print("\n[1] Init/Logo")
            driver.init()
            time.sleep(3)

            print("\n[2] Mode 1 (might be data mode)")
            driver.set_mode_data()
            time.sleep(3)

            print("\n[3] Mode 2 (might be image mode)")
            driver.set_mode_image()
            time.sleep(3)

            print("\n[4] Mode 3 (brightness?)")
            driver.set_brightness(100)
            time.sleep(3)

            print("\n✓ Test complete - check what you saw on screen")

        elif args.command == 'monitor':
            print("Monitoring mode - keeping display active")
            print("Press Ctrl+C to stop\n")

            driver.init()
            time.sleep(2)

            while True:
                cpu = get_cpu_temp()
                gpu = get_gpu_temp()
                print(f"CPU: {cpu}°C  GPU: {gpu}°C", end='\r')
                time.sleep(2)

    except KeyboardInterrupt:
        print("\n\nStopped")
    finally:
        driver.disconnect()
        print("\n✓ Disconnected")

if __name__ == "__main__":
    main()
