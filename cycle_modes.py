#!/usr/bin/env python3
"""
Cycle through all captured display modes
"""
import usb.core
import usb.util
import sys
import time

VENDOR_ID = 0x3633
PRODUCT_ID = 0x0026
EP_OUT = 0x01

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

    def disconnect(self):
        if self.dev:
            try:
                usb.util.release_interface(self.dev, self.interface)
                usb.util.dispose_resources(self.dev)
            except:
                pass

def main():
    print("="*70)
    print("LM360 Display Mode Cycler")
    print("="*70)
    print()

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected")
    print("\nThis will cycle through all captured modes")
    print("Watch your screen to see what each mode displays!")
    print()
    print("="*70)

    # All modes from capture
    modes = [
        ("Init/Logo", bytes([0xaa, 0x04, 0x00, 0x03, 0x00, 0x00, 0x00, 0xdc, 0x9b])),
        ("Mode 1 (03 1d)", bytes([0xaa, 0x04, 0x00, 0x06, 0x03, 0x1d, 0x00, 0xe6, 0x0b])),
        ("Mode 2 (03 47)", bytes([0xaa, 0x04, 0x00, 0x06, 0x03, 0x47, 0x00, 0x92, 0xea])),
        ("Mode 3 (03 61)", bytes([0xaa, 0x04, 0x00, 0x06, 0x03, 0x61, 0x00, 0xd2, 0x46])),
    ]

    try:
        for i, (name, cmd) in enumerate(modes):
            print(f"\n[{i+1}] {name}")
            print(f"    Command: {' '.join(f'{b:02x}' for b in cmd)}")
            device.write(cmd)
            print(f"    Sent! Check screen...")
            time.sleep(3)

            if i < len(modes) - 1:
                input("    Press ENTER for next mode...")

        print("\n\n" + "="*70)
        print("Mode cycling complete!")
        print()
        print("SUMMARY:")
        print("- Mode 0: Logo/Init (aa 04 00 03)")
        print("- Mode 1: ??? (aa 04 00 06 03 1d)")
        print("- Mode 2: ??? (aa 04 00 06 03 47)")
        print("- Mode 3: ??? (aa 04 00 06 03 61)")
        print()
        print("Tell me what each mode displayed!")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nInterrupted")
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
