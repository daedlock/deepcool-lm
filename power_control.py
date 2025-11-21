#!/usr/bin/env python3
"""
Simple power control: python power_control.py on|off
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
            result = self.dev.write(EP_OUT, data, timeout=1000)
            return result
        except Exception as e:
            print(f"Write error: {e}")
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

def power_off(device):
    """Try all known power OFF patterns"""
    print("\n>>> SENDING POWER OFF COMMANDS <<<\n")

    commands = [
        ("0x55 0x03 0x00", bytes([0x55, 0x03, 0x00] + [0x00]*61)),
        ("0x55 0x04 0x00", bytes([0x55, 0x04, 0x00] + [0x00]*61)),
        ("0x55 0x05 0x00", bytes([0x55, 0x05, 0x00] + [0x00]*61)),
        ("0x55 0x06 0x00", bytes([0x55, 0x06, 0x00] + [0x00]*61)),
        ("0x55 0x10 0x00", bytes([0x55, 0x10, 0x00] + [0x00]*61)),
        ("0x55 0x20 0x00", bytes([0x55, 0x20, 0x00] + [0x00]*61)),
        ("0x55 0xAA 0x00", bytes([0x55, 0xAA, 0x00] + [0x00]*61)),
        ("0x55 0xFF 0x00", bytes([0x55, 0xFF, 0x00] + [0x00]*61)),
        ("0x00 (all zeros)", bytes([0x00] * 64)),
    ]

    for name, data in commands:
        print(f"Trying: {name}")
        print(f"  Data: {bytes(data[:16]).hex()}")
        result = device.write(data)
        print(f"  Wrote: {result} bytes")

        response = device.read()
        if response:
            print(f"  Response: {bytes(response[:16]).hex()}")
        else:
            print(f"  Response: None")

        print(f"  Waiting 1 second...\n")
        time.sleep(1)

    print("="*70)
    print("Did the screen turn OFF?")
    print("="*70)

def power_on(device):
    """Try all known power ON patterns"""
    print("\n>>> SENDING POWER ON COMMANDS <<<\n")

    commands = [
        ("0x55 0x03 0x01", bytes([0x55, 0x03, 0x01] + [0x00]*61)),
        ("0x55 0x04 0x01", bytes([0x55, 0x04, 0x01] + [0x00]*61)),
        ("0x55 0x05 0x01", bytes([0x55, 0x05, 0x01] + [0x00]*61)),
        ("0x55 0x06 0xFF", bytes([0x55, 0x06, 0xFF] + [0x00]*61)),
        ("0x55 0x10 0x01", bytes([0x55, 0x10, 0x01] + [0x00]*61)),
        ("0x55 0x20 0x01", bytes([0x55, 0x20, 0x01] + [0x00]*61)),
        ("0x55 0xAA 0x55", bytes([0x55, 0xAA, 0x55] + [0x00]*61)),
        ("Multi-step init", None),  # Special case
    ]

    for name, data in commands:
        if name == "Multi-step init":
            print("Trying: Multi-step initialization sequence")
            steps = [
                ("Reset", bytes([0x55, 0xAA] + [0x00]*62)),
                ("Power", bytes([0x55, 0x03, 0x01] + [0x00]*61)),
                ("Enable", bytes([0x55, 0x04, 0x01] + [0x00]*61)),
                ("Backlight", bytes([0x55, 0x06, 0xFF] + [0x00]*61)),
                ("Complete", bytes([0x55, 0x05, 0x01] + [0x00]*61)),
            ]
            for step_name, step_data in steps:
                print(f"  Step: {step_name}")
                device.write(step_data)
                time.sleep(0.3)
            print(f"  Waiting 2 seconds...\n")
            time.sleep(2)
        else:
            print(f"Trying: {name}")
            print(f"  Data: {bytes(data[:16]).hex()}")
            result = device.write(data)
            print(f"  Wrote: {result} bytes")

            response = device.read()
            if response:
                print(f"  Response: {bytes(response[:16]).hex()}")
            else:
                print(f"  Response: None")

            print(f"  Waiting 1 second...\n")
            time.sleep(1)

    print("="*70)
    print("Did the screen turn ON?")
    print("="*70)

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ['on', 'off']:
        print("Usage: sudo uv run power_control.py [on|off]")
        print("")
        print("  on  - Try to turn LCD screen ON")
        print("  off - Try to turn LCD screen OFF")
        sys.exit(1)

    command = sys.argv[1]

    print("="*70)
    print(f"LM360 LCD Power Control - {command.upper()}")
    print("="*70)

    device = LM360()
    if not device.connect():
        print("✗ Failed to connect!")
        print("Make sure you're running with: sudo uv run power_control.py on|off")
        sys.exit(1)

    print("✓ Connected\n")
    print("WATCH YOUR SCREEN CAREFULLY!\n")

    try:
        if command == 'off':
            power_off(device)
        else:
            power_on(device)

    except KeyboardInterrupt:
        print("\n\nInterrupted")
    finally:
        device.disconnect()
        print("\n✓ Disconnected")

if __name__ == "__main__":
    main()
