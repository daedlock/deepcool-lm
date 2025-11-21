#!/usr/bin/env python3
"""
Deepcool LM360 USB Bulk Transfer Driver
This device uses Vendor Specific Class with Bulk transfers, NOT HID
"""
import usb.core
import usb.util
import sys
import time
import psutil

# LM360 USB IDs
VENDOR_ID = 0x3633
PRODUCT_ID = 0x0026

# USB Endpoints (from lsusb -v)
EP_OUT = 0x01  # Bulk OUT endpoint
EP_IN = 0x81   # Bulk IN endpoint

class LM360:
    def __init__(self):
        self.dev = None
        self.interface = 0

    def connect(self):
        """Find and connect to the LM360 device"""
        print("Searching for LM360...")

        # Find device
        self.dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

        if self.dev is None:
            print("✗ LM360 not found! Make sure it's plugged in.")
            return False

        print(f"✓ Found LM360: {self.dev.manufacturer} {self.dev.product}")
        print(f"  Serial: {self.dev.serial_number}")

        # Detach kernel driver if active
        if self.dev.is_kernel_driver_active(self.interface):
            print("  Detaching kernel driver...")
            try:
                self.dev.detach_kernel_driver(self.interface)
                print("  ✓ Kernel driver detached")
            except usb.core.USBError as e:
                print(f"  Warning: Could not detach kernel driver: {e}")

        # Set configuration
        try:
            self.dev.set_configuration()
            print("  ✓ Configuration set")
        except usb.core.USBError as e:
            print(f"  Warning: Could not set configuration: {e}")

        # Claim interface
        try:
            usb.util.claim_interface(self.dev, self.interface)
            print("  ✓ Interface claimed")
        except usb.core.USBError as e:
            print(f"  ✗ Could not claim interface: {e}")
            return False

        print("✓ Successfully connected to LM360!\n")
        return True

    def write(self, data):
        """Write data to the device via bulk OUT endpoint"""
        try:
            bytes_written = self.dev.write(EP_OUT, data, timeout=1000)
            return bytes_written
        except usb.core.USBError as e:
            print(f"Write error: {e}")
            return 0

    def read(self, size=512, timeout=1000):
        """Read data from the device via bulk IN endpoint"""
        try:
            data = self.dev.read(EP_IN, size, timeout=timeout)
            return data
        except usb.core.USBTimeoutError:
            return None
        except usb.core.USBError as e:
            print(f"Read error: {e}")
            return None

    def send_init(self):
        """Send initialization sequence - trying various patterns"""
        print("Attempting initialization sequences...\n")

        # Try 1: Simple init pattern
        print("[1] Trying simple init (512 bytes, all zeros with header)...")
        init1 = bytes([0x00] * 512)
        result = self.write(init1)
        print(f"    Wrote {result} bytes")
        time.sleep(0.5)
        response = self.read(timeout=500)
        if response:
            print(f"    Response: {bytes(response[:20]).hex()}")
        else:
            print("    No response")

        # Try 2: Init with different header
        print("\n[2] Trying init with 0x01 header...")
        init2 = bytes([0x01] + [0x00] * 511)
        result = self.write(init2)
        print(f"    Wrote {result} bytes")
        time.sleep(0.5)
        response = self.read(timeout=500)
        if response:
            print(f"    Response: {bytes(response[:20]).hex()}")
        else:
            print("    No response")

        # Try 3: Different packet size
        print("\n[3] Trying smaller packet (64 bytes)...")
        init3 = bytes([0x10, 0xAA] + [0x00] * 62)
        result = self.write(init3)
        print(f"    Wrote {result} bytes")
        time.sleep(0.5)
        response = self.read(timeout=500)
        if response:
            print(f"    Response: {bytes(response[:20]).hex()}")
        else:
            print("    No response")

        # Try 4: Pattern similar to MYSTIQUE series (LCD devices)
        print("\n[4] Trying LCD-style init pattern...")
        init4 = bytes([0x02, 0x01, 0x00, 0x00] + [0x00] * 508)
        result = self.write(init4)
        print(f"    Wrote {result} bytes")
        time.sleep(0.5)
        response = self.read(timeout=500)
        if response:
            print(f"    Response: {bytes(response[:20]).hex()}")
        else:
            print("    No response")

    def probe_commands(self):
        """Probe different command patterns"""
        print("\n" + "="*60)
        print("PROBING COMMAND PATTERNS")
        print("="*60 + "\n")

        # Test different command headers
        headers = [0x00, 0x01, 0x02, 0x03, 0x10, 0x11, 0x20, 0xAA, 0xFF]

        for header in headers:
            data = bytes([header] + [0x00] * 63)
            print(f"Testing header 0x{header:02x}...", end=" ")
            result = self.write(data)
            time.sleep(0.1)
            response = self.read(timeout=100)
            if response:
                print(f"✓ Response: {bytes(response[:10]).hex()}...")
            else:
                print("No response")

    def disconnect(self):
        """Release the device"""
        if self.dev:
            try:
                usb.util.release_interface(self.dev, self.interface)
                usb.util.dispose_resources(self.dev)
                print("\n✓ Device disconnected")
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
    return 45  # Default

def main():
    print("="*60)
    print("Deepcool LM360 USB Bulk Transfer Driver")
    print("="*60 + "\n")

    device = LM360()

    if not device.connect():
        print("\nFailed to connect. Make sure you're running with sudo!")
        print("Command: sudo -E python3 lm360_driver.py")
        sys.exit(1)

    try:
        # Send initialization sequences
        device.send_init()

        # Probe for working commands
        print("\n" + "="*60)
        user_input = input("Do you want to probe more commands? (y/N): ")
        if user_input.lower() == 'y':
            device.probe_commands()

        print("\n" + "="*60)
        print("Check your LCD screen - did anything appear?")
        print("If you saw the logo or any change, we found the init sequence!")
        print("="*60)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
