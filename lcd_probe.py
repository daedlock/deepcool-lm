#!/usr/bin/env python3
"""
Advanced LCD Activation Probe for Deepcool LM360
Trying various LCD wake-up and initialization commands
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

    def read(self, size=512, timeout=1000):
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

def test_sequence(device, name, data, wait=0.5):
    """Test a command sequence and check response"""
    print(f"\n{name}")
    print(f"  Data: {bytes(data[:20]).hex()}{'...' if len(data) > 20 else ''}")
    result = device.write(data)
    print(f"  Wrote: {result} bytes")
    time.sleep(wait)

    response = device.read(timeout=500)
    if response:
        print(f"  Response: {bytes(response[:20]).hex()}")
        return response
    else:
        print(f"  Response: None")
        return None

def main():
    print("="*70)
    print("LM360 LCD Activation Probe")
    print("="*70)

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected\n")
    print("Testing LCD activation sequences...")
    print("WATCH YOUR SCREEN for any changes!")
    print("="*70)

    try:
        # Sequence 1: USB control transfer style init
        print("\n[1] USB Control-like init sequence...")
        test_sequence(device, "  1a. Device info request",
                     bytes([0x55, 0x01, 0x00, 0x00] + [0x00]*60))

        # Sequence 2: LCD power on patterns
        print("\n[2] LCD Power/Enable sequences...")
        test_sequence(device, "  2a. Power ON (0x55 0x03)",
                     bytes([0x55, 0x03, 0x01] + [0x00]*61))
        test_sequence(device, "  2b. Display Enable",
                     bytes([0x55, 0x04, 0x01] + [0x00]*61))
        test_sequence(device, "  2c. Wake command",
                     bytes([0x55, 0x05, 0x01] + [0x00]*61))

        # Sequence 3: Try the response pattern as command
        print("\n[3] Echo back device response...")
        test_sequence(device, "  3a. Send back: 55 02 00 0a 0a 81 4e",
                     bytes([0x55, 0x02, 0x00, 0x0a, 0x0a, 0x81, 0x4e] + [0x00]*57))

        # Sequence 4: Common LCD init patterns
        print("\n[4] Common LCD initialization patterns...")
        test_sequence(device, "  4a. Clear screen",
                     bytes([0x55, 0x10, 0x00] + [0x00]*61))
        test_sequence(device, "  4b. Set mode",
                     bytes([0x55, 0x20, 0x01] + [0x00]*61))
        test_sequence(device, "  4c. Init display",
                     bytes([0x55, 0xAA, 0x55] + [0x00]*61))

        # Sequence 5: Try longer init sequences
        print("\n[5] Multi-byte command sequences...")
        test_sequence(device, "  5a. Init sequence 1",
                     bytes([0x55, 0x02, 0x01, 0x00, 0x00, 0x00, 0x01] + [0x00]*57))
        test_sequence(device, "  5b. Init sequence 2",
                     bytes([0x02, 0x01, 0x00, 0x55] + [0x00]*60))

        # Sequence 6: Try setting brightness/backlight
        print("\n[6] Backlight/Brightness commands...")
        test_sequence(device, "  6a. Backlight ON (max)",
                     bytes([0x55, 0x06, 0xFF] + [0x00]*61))
        test_sequence(device, "  6b. Brightness 100%",
                     bytes([0x55, 0x07, 0x64] + [0x00]*61))

        # Sequence 7: Frame buffer / image data header
        print("\n[7] Frame buffer initialization...")
        test_sequence(device, "  7a. Frame start",
                     bytes([0x55, 0x50, 0x00, 0x00] + [0x00]*60))
        test_sequence(device, "  7b. Image data header",
                     bytes([0x55, 0x51, 0x01, 0x00] + [0x00]*60))

        # Sequence 8: Try sending a full 512-byte init packet
        print("\n[8] Full 512-byte initialization...")
        init_512 = bytearray([0x55, 0x02, 0x01] + [0x00]*509)
        test_sequence(device, "  8a. 512-byte init", init_512)

        # Sequence 9: Multi-step initialization
        print("\n[9] Multi-step initialization sequence...")
        print("  9a. Step 1: Reset")
        device.write(bytes([0x55, 0xAA] + [0x00]*62))
        time.sleep(0.2)

        print("  9b. Step 2: Power ON")
        device.write(bytes([0x55, 0x03, 0x01] + [0x00]*61))
        time.sleep(0.2)

        print("  9c. Step 3: Enable")
        device.write(bytes([0x55, 0x04, 0x01] + [0x00]*61))
        time.sleep(0.2)

        print("  9d. Step 4: Init complete")
        response = test_sequence(device, "     Final init",
                                bytes([0x55, 0x05, 0x01] + [0x00]*61))

        # Sequence 10: Try command 0x02 with different sub-commands
        print("\n[10] Command 0x02 variations (device seems to respond to this)...")
        for subcmd in [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x10, 0x20, 0xFF]:
            test_sequence(device, f"  10.{subcmd:02x}. Cmd 0x55 0x02 0x{subcmd:02x}",
                         bytes([0x55, 0x02, subcmd] + [0x00]*61), wait=0.3)

        print("\n" + "="*70)
        print("Did you see ANYTHING on the screen?")
        print("If yes, note which sequence number showed something!")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nInterrupted")
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
