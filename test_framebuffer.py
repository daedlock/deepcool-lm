#!/usr/bin/env python3
"""
Test framebuffer with different patterns
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
            return self.dev.write(EP_OUT, data, timeout=5000)
        except Exception as e:
            print(f"Write error: {e}")
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
    print("Framebuffer Format Test")
    print("="*70)
    print()

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected\n")

    try:
        # Test 1: Send exact Windows sequence (black screen)
        print("[1] Sending exact Windows sequence (black frame)...")
        header = bytes([0xaa, 0x08, 0x00, 0x00, 0x01, 0x00, 0x58, 0x02, 0x00, 0x2c, 0x01, 0xbc, 0x11])
        framebuffer = bytes([0x00] * 153600)  # All black

        device.write(header)
        device.write(framebuffer)
        print("    Sent header + black frame")
        time.sleep(3)

        # Test 2: All white
        print("\n[2] Sending all WHITE frame...")
        framebuffer_white = bytes([0xFF] * 153600)  # All white
        device.write(header)
        device.write(framebuffer_white)
        print("    Sent header + white frame")
        time.sleep(3)

        # Test 3: Red screen (RGB565: 0xF800)
        print("\n[3] Sending RED frame...")
        # RGB565 red = 0xF800 = 11111 000000 00000
        framebuffer_red = bytearray()
        for _ in range(320 * 240):
            framebuffer_red.append(0x00)  # Low byte
            framebuffer_red.append(0xF8)  # High byte
        device.write(header)
        device.write(bytes(framebuffer_red))
        print("    Sent header + red frame")
        time.sleep(3)

        # Test 4: Green screen (RGB565: 0x07E0)
        print("\n[4] Sending GREEN frame...")
        framebuffer_green = bytearray()
        for _ in range(320 * 240):
            framebuffer_green.append(0xE0)  # Low byte
            framebuffer_green.append(0x07)  # High byte
        device.write(header)
        device.write(bytes(framebuffer_green))
        print("    Sent header + green frame")
        time.sleep(3)

        # Test 5: Blue screen (RGB565: 0x001F)
        print("\n[5] Sending BLUE frame...")
        framebuffer_blue = bytearray()
        for _ in range(320 * 240):
            framebuffer_blue.append(0x1F)  # Low byte
            framebuffer_blue.append(0x00)  # High byte
        device.write(header)
        device.write(bytes(framebuffer_blue))
        print("    Sent header + blue frame")
        time.sleep(3)

        # Test 6: Half-and-half (top white, bottom black)
        print("\n[6] Sending SPLIT frame (top white, bottom black)...")
        framebuffer_split = bytearray()
        for y in range(240):
            for x in range(320):
                if y < 120:
                    framebuffer_split.append(0xFF)  # White
                    framebuffer_split.append(0xFF)
                else:
                    framebuffer_split.append(0x00)  # Black
                    framebuffer_split.append(0x00)
        device.write(header)
        device.write(bytes(framebuffer_split))
        print("    Sent header + split frame")
        time.sleep(3)

        print("\n" + "="*70)
        print("Did you see ANY colors on the display?")
        print("- Test 1: Black (might look like nothing)")
        print("- Test 2: White (should be bright)")
        print("- Test 3: Red")
        print("- Test 4: Green")
        print("- Test 5: Blue")
        print("- Test 6: Split (top white, bottom black)")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nStopped")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
