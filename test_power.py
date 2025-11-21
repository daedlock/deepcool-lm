#!/usr/bin/env python3
"""
Test LCD Power ON and OFF commands
"""
import usb.core
import usb.util
import sys
import time

VENDOR_ID = 0x3633
PRODUCT_ID = 0x0026
EP_OUT = 0x01
EP_IN = 0x81

class LM360:
    def __init__(self):
        self.dev = None
        self.interface = 0

    def connect(self):
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
        try:
            return self.dev.write(EP_OUT, data, timeout=1000)
        except Exception as e:
            print(f"    Error: {e}")
            return 0

    def read(self, size=512, timeout=1000):
        try:
            return self.dev.read(EP_IN, size, timeout=timeout)
        except:
            return None

    def test_command(self, name, data, wait=1):
        print(f"{name}")
        print(f"  Sending: {bytes(data[:16]).hex()}")
        result = self.write(data)
        print(f"  Wrote: {result} bytes")

        response = self.read(timeout=500)
        if response:
            print(f"  Response: {bytes(response[:16]).hex()}")
        else:
            print(f"  Response: None")

        time.sleep(wait)

    def disconnect(self):
        if self.dev:
            try:
                usb.util.release_interface(self.dev, self.interface)
                usb.util.dispose_resources(self.dev)
            except:
                pass

def main():
    print("="*70)
    print("LM360 LCD Power Control Test")
    print("="*70)
    print("\nWATCH YOUR SCREEN CAREFULLY!\n")

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected\n")
    print("="*70)

    try:
        # Test OFF commands
        print("\n>>> TESTING POWER OFF COMMANDS <<<\n")

        print("[OFF 1] Command 0x55 0x03 0x00 (Power OFF)")
        device.test_command("  ", bytes([0x55, 0x03, 0x00] + [0x00]*61), wait=2)

        print("[OFF 2] Command 0x55 0x04 0x00 (Display Disable)")
        device.test_command("  ", bytes([0x55, 0x04, 0x00] + [0x00]*61), wait=2)

        print("[OFF 3] Command 0x55 0x05 0x00 (Sleep)")
        device.test_command("  ", bytes([0x55, 0x05, 0x00] + [0x00]*61), wait=2)

        print("[OFF 4] Command 0x55 0x06 0x00 (Backlight OFF)")
        device.test_command("  ", bytes([0x55, 0x06, 0x00] + [0x00]*61), wait=2)

        print("[OFF 5] Command 0x55 0x10 0x00 (Clear/Off)")
        device.test_command("  ", bytes([0x55, 0x10, 0x00] + [0x00]*61), wait=2)

        input("\nPress ENTER to test POWER ON commands...")

        # Test ON commands
        print("\n>>> TESTING POWER ON COMMANDS <<<\n")

        print("[ON 1] Command 0x55 0x03 0x01 (Power ON)")
        device.test_command("  ", bytes([0x55, 0x03, 0x01] + [0x00]*61), wait=2)

        print("[ON 2] Command 0x55 0x04 0x01 (Display Enable)")
        device.test_command("  ", bytes([0x55, 0x04, 0x01] + [0x00]*61), wait=2)

        print("[ON 3] Command 0x55 0x05 0x01 (Wake)")
        device.test_command("  ", bytes([0x55, 0x05, 0x01] + [0x00]*61), wait=2)

        print("[ON 4] Command 0x55 0x06 0xFF (Backlight MAX)")
        device.test_command("  ", bytes([0x55, 0x06, 0xFF] + [0x00]*61), wait=2)

        print("[ON 5] Command 0x55 0x10 0x01 (Enable)")
        device.test_command("  ", bytes([0x55, 0x10, 0x01] + [0x00]*61), wait=2)

        # Try multi-step sequence
        input("\nPress ENTER to test MULTI-STEP SEQUENCE...")

        print("\n>>> MULTI-STEP POWER ON SEQUENCE <<<\n")
        print("Step 1: Reset")
        device.test_command("  ", bytes([0x55, 0xAA] + [0x00]*62), wait=0.5)

        print("Step 2: Power ON")
        device.test_command("  ", bytes([0x55, 0x03, 0x01] + [0x00]*61), wait=0.5)

        print("Step 3: Display Enable")
        device.test_command("  ", bytes([0x55, 0x04, 0x01] + [0x00]*61), wait=0.5)

        print("Step 4: Backlight MAX")
        device.test_command("  ", bytes([0x55, 0x06, 0xFF] + [0x00]*61), wait=0.5)

        print("Step 5: Init Complete")
        device.test_command("  ", bytes([0x55, 0x05, 0x01] + [0x00]*61), wait=2)

        print("\n" + "="*70)
        print("RESULTS:")
        print("Did the screen turn OFF with any command?")
        print("Did it turn back ON with any command?")
        print("Note which commands worked!")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nInterrupted")
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
