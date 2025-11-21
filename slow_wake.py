#!/usr/bin/env python3
"""
Slow wake-up test - send commands one at a time with LONG delays
This gives the LCD time to initialize if there's a delay
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
        except:
            return 0

    def read(self, size=512, timeout=500):
        try:
            return self.dev.read(EP_IN, size, timeout=timeout)
        except:
            return None

    def disconnect(self):
        if self.dev:
            try:
                usb.util.release_interface(self.dev, self.interface)
                usb.util.dispose_resources(self.dev)
            except:
                pass

def test_command(device, num, name, data, wait=5):
    """Test a command and wait a while"""
    print(f"\n[{num}] {name}")
    print(f"    Data: {bytes(data[:16]).hex()}")
    result = device.write(data)
    print(f"    Wrote: {result} bytes")

    response = device.read(timeout=500)
    if response:
        print(f"    Response: {bytes(response[:16]).hex()}")

    print(f"    >>> Waiting {wait} seconds... WATCH SCREEN! <<<")
    for i in range(wait):
        print(f"        {wait-i} seconds remaining...", end='\r')
        time.sleep(1)
    print()

def main():
    print("="*70)
    print("SLOW WAKE-UP TEST - Long delays between commands")
    print("="*70)
    print("\nEach command waits 5 seconds - watch for ANY screen change!")
    print("Total time: ~2-3 minutes\n")

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected\n")
    print("="*70)
    print("WATCH YOUR SCREEN CONTINUOUSLY!\n")

    try:
        # Most likely wake commands, one at a time with long delays

        test_command(device, 1, "Hardware Reset (0xFF pattern)",
                    bytes([0xFF, 0xFF, 0xFF, 0xFF] + [0x00]*60))

        test_command(device, 2, "Init sequence start (0x55 0xAA)",
                    bytes([0x55, 0xAA] + [0x00]*62))

        test_command(device, 3, "Power ON (0x55 0x03 0x01)",
                    bytes([0x55, 0x03, 0x01] + [0x00]*61))

        test_command(device, 4, "Display Enable (0x55 0x04 0x01)",
                    bytes([0x55, 0x04, 0x01] + [0x00]*61))

        test_command(device, 5, "Backlight MAX (0x55 0x06 0xFF)",
                    bytes([0x55, 0x06, 0xFF] + [0x00]*61))

        test_command(device, 6, "Wake command (0x55 0x05 0x01)",
                    bytes([0x55, 0x05, 0x01] + [0x00]*61))

        test_command(device, 7, "Set mode (0x55 0x20 0x01)",
                    bytes([0x55, 0x20, 0x01] + [0x00]*61))

        test_command(device, 8, "Clear screen (0x55 0x10 0x00)",
                    bytes([0x55, 0x10, 0x00] + [0x00]*61))

        test_command(device, 9, "Init display (0x55 0xAA 0x55)",
                    bytes([0x55, 0xAA, 0x55] + [0x00]*61))

        test_command(device, 10, "Response echo (0x55 0x02 0x00...)",
                    bytes([0x55, 0x02, 0x00, 0x0a, 0x0a, 0x81, 0x4e] + [0x00]*57))

        # Try 64-byte packets (smaller, like when we got first response)
        print("\n" + "="*70)
        print("Now trying 64-byte packets (smaller size)")
        print("="*70)

        test_command(device, 11, "64-byte: 0x10 0xAA header",
                    bytes([0x10, 0xAA] + [0x00]*62))

        test_command(device, 12, "64-byte: 0x55 0x03 0x01",
                    bytes([0x55, 0x03, 0x01] + [0x00]*61))

        test_command(device, 13, "64-byte: 0x55 0x04 0x01",
                    bytes([0x55, 0x04, 0x01] + [0x00]*61))

        # Try the full multi-step sequence with delays
        print("\n" + "="*70)
        print("Multi-step sequence with delays between each step")
        print("="*70)

        print("\nStep 1: Reset")
        device.write(bytes([0x55, 0xAA] + [0x00]*62))
        print("  Waiting 3 seconds...")
        time.sleep(3)

        print("Step 2: Power ON")
        device.write(bytes([0x55, 0x03, 0x01] + [0x00]*61))
        print("  Waiting 3 seconds...")
        time.sleep(3)

        print("Step 3: Display Enable")
        device.write(bytes([0x55, 0x04, 0x01] + [0x00]*61))
        print("  Waiting 3 seconds...")
        time.sleep(3)

        print("Step 4: Backlight MAX")
        device.write(bytes([0x55, 0x06, 0xFF] + [0x00]*61))
        print("  Waiting 3 seconds...")
        time.sleep(3)

        print("Step 5: Init Complete")
        device.write(bytes([0x55, 0x05, 0x01] + [0x00]*61))
        print("  Waiting 5 seconds...")
        time.sleep(5)

        print("\n" + "="*70)
        print("All commands tested with 5-second delays")
        print("\nDid you see the screen turn ON at any point?")
        print("If yes, which command number? (1-13 or multi-step?)")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nInterrupted")
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
