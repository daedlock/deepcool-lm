#!/usr/bin/env python3
"""
Brute force search for mode switch commands
Try systematic variations of the aa 04 00 06 pattern
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

def calculate_checksum(data):
    """Calculate checksum (last 2 bytes) - simple XOR method"""
    checksum = 0
    for b in data[:-2]:
        checksum ^= b
    # Return 2-byte checksum (low, high)
    return checksum & 0xFF, (checksum >> 8) & 0xFF

def main():
    print("="*70)
    print("Brute Force Mode Search")
    print("="*70)
    print("\nTrying systematic command variations...")
    print("Watch your screen for ANY changes!\n")

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected\n")

    try:
        # First, init to known state
        print("Initializing to logo...")
        device.write(bytes([0xaa, 0x04, 0x00, 0x03, 0x00, 0x00, 0x00, 0xdc, 0x9b]))
        time.sleep(2)

        # Try variations of aa 04 00 06 XX XX...
        # Pattern: aa 04 00 06 [param1] [param2] 00 [checksum_low] [checksum_high]

        print("\nTrying aa 04 00 06 commands with different parameters...")
        print("Press Ctrl+C if you see something change!\n")

        test_count = 0
        for param1 in range(0, 16):  # 00-0F
            for param2 in range(0, 256, 16):  # 00, 10, 20, ..., F0
                # Build command
                cmd = bytearray([0xaa, 0x04, 0x00, 0x06, param1, param2, 0x00, 0x00, 0x00])

                # Try to calculate checksum similar to captured commands
                # For now, use captured checksum patterns
                cmd[7] = 0xe6
                cmd[8] = 0x0b

                test_count += 1
                print(f"[{test_count:3d}] aa 04 00 06 {param1:02x} {param2:02x} 00 ... ", end="")

                device.write(bytes(cmd))
                time.sleep(0.5)

                print("sent", end="\r")

        print(f"\n\nTried {test_count} variations")
        print("\nDid you see the display change at any point?")
        print("If yes, note the command number!")

    except KeyboardInterrupt:
        print("\n\nStopped by user")
        response = input("Did you see a change? Which command number? (or 'no'): ")
        if response.lower() != 'no':
            print(f"\nGreat! Command #{response} might be the mode switch!")
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
