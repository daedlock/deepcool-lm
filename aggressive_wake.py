#!/usr/bin/env python3
"""
Aggressive wake-up attempts for LM360
Try EVERYTHING to wake the screen back up
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

def main():
    print("="*70)
    print("AGGRESSIVE WAKE-UP SEQUENCE FOR LM360")
    print("="*70)
    print("\nTrying EVERYTHING to wake the screen...\n")

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected\n")
    print("WATCH YOUR SCREEN!\n")
    print("="*70)

    try:
        # Strategy 1: Hardware reset commands
        print("\n[1] Hardware Reset Commands")
        reset_cmds = [
            bytes([0xFF, 0xFF, 0xFF, 0xFF] + [0x00]*60),  # All 1s reset
            bytes([0xAA, 0x55, 0xAA, 0x55] + [0x00]*60),  # Alternating pattern
            bytes([0x00, 0x00, 0x00, 0x00] + [0x00]*60),  # All 0s
        ]
        for i, cmd in enumerate(reset_cmds):
            print(f"  {i+1}. {bytes(cmd[:8]).hex()}")
            device.write(cmd)
            time.sleep(0.5)

        # Strategy 2: All possible wake combinations
        print("\n[2] Wake Command Matrix (0x55 + all combinations)")
        for cmd1 in [0x03, 0x04, 0x05, 0x06, 0x10, 0x20, 0xAA]:
            for cmd2 in [0x01, 0xFF, 0xAA, 0x55]:
                data = bytes([0x55, cmd1, cmd2] + [0x00]*61)
                print(f"  0x55 0x{cmd1:02x} 0x{cmd2:02x}", end="\r")
                device.write(data)
                time.sleep(0.1)
        print("\n  Tested all combinations")

        # Strategy 3: Continuous wake packets
        print("\n[3] Continuous Wake Packets (10 seconds)")
        wake_patterns = [
            bytes([0x55, 0x03, 0x01] + [0x00]*61),
            bytes([0x55, 0x04, 0x01] + [0x00]*61),
            bytes([0x55, 0x05, 0x01] + [0x00]*61),
            bytes([0x55, 0x06, 0xFF] + [0x00]*61),
        ]
        for i in range(40):  # 10 seconds, 4 patterns, rotate
            device.write(wake_patterns[i % 4])
            print(f"  Attempt {i+1}/40", end="\r")
            time.sleep(0.25)
        print("\n")

        # Strategy 4: Init sequence from lcd_probe that worked
        print("\n[4] Repeating ALL commands from lcd_probe.py")
        all_commands = []

        # All the commands from lcd_probe
        all_commands.append(("Init 1", bytes([0x55, 0x01, 0x00, 0x00] + [0x00]*60)))
        all_commands.append(("Power ON", bytes([0x55, 0x03, 0x01] + [0x00]*61)))
        all_commands.append(("Display Enable", bytes([0x55, 0x04, 0x01] + [0x00]*61)))
        all_commands.append(("Wake", bytes([0x55, 0x05, 0x01] + [0x00]*61)))
        all_commands.append(("Echo response", bytes([0x55, 0x02, 0x00, 0x0a, 0x0a, 0x81, 0x4e] + [0x00]*57)))
        all_commands.append(("Clear screen", bytes([0x55, 0x10, 0x00] + [0x00]*61)))
        all_commands.append(("Set mode", bytes([0x55, 0x20, 0x01] + [0x00]*61)))
        all_commands.append(("Init display", bytes([0x55, 0xAA, 0x55] + [0x00]*61)))
        all_commands.append(("Init seq 1", bytes([0x55, 0x02, 0x01, 0x00, 0x00, 0x00, 0x01] + [0x00]*57)))
        all_commands.append(("Init seq 2", bytes([0x02, 0x01, 0x00, 0x55] + [0x00]*60)))
        all_commands.append(("Backlight MAX", bytes([0x55, 0x06, 0xFF] + [0x00]*61)))
        all_commands.append(("Brightness 100%", bytes([0x55, 0x07, 0x64] + [0x00]*61)))
        all_commands.append(("Frame start", bytes([0x55, 0x50, 0x00, 0x00] + [0x00]*60)))
        all_commands.append(("Image header", bytes([0x55, 0x51, 0x01, 0x00] + [0x00]*60)))

        for name, cmd in all_commands:
            print(f"  {name}")
            device.write(cmd)
            time.sleep(0.5)

        # Strategy 5: Multi-step init (repeat 3 times)
        print("\n[5] Multi-Step Init Sequence (x3 repetitions)")
        for rep in range(3):
            print(f"  Repetition {rep+1}/3")
            device.write(bytes([0x55, 0xAA] + [0x00]*62))
            time.sleep(0.2)
            device.write(bytes([0x55, 0x03, 0x01] + [0x00]*61))
            time.sleep(0.2)
            device.write(bytes([0x55, 0x04, 0x01] + [0x00]*61))
            time.sleep(0.2)
            device.write(bytes([0x55, 0x06, 0xFF] + [0x00]*61))
            time.sleep(0.2)
            device.write(bytes([0x55, 0x05, 0x01] + [0x00]*61))
            time.sleep(1)

        # Strategy 6: Send 512-byte init packets
        print("\n[6] Large 512-byte Init Packets")
        for header in [0x01, 0x02, 0x55, 0xAA, 0xFF]:
            data = bytearray(512)
            data[0] = header
            data[1] = 0x55
            print(f"  Header: 0x{header:02x}")
            device.write(data)
            time.sleep(0.5)

        # Strategy 7: Try command 0x02 with ALL subcodes (device responds to 0x02)
        print("\n[7] Command 0x02 Full Subcode Scan")
        for subcode in range(256):
            data = bytes([0x55, 0x02, subcode] + [0x00]*61)
            device.write(data)
            print(f"  Trying 0x55 0x02 0x{subcode:02x}", end="\r")
            time.sleep(0.05)
        print("\n")

        # Strategy 8: Blast with data
        print("\n[8] Data Flood (might trigger display)")
        for i in range(100):
            data = bytes([0x55, 0x02, i % 256, 45, 40] + [0x00]*59)  # With temp data
            device.write(data)
            print(f"  Packet {i+1}/100", end="\r")
            time.sleep(0.05)
        print("\n")

        # Strategy 9: Try exact working sequence from before
        print("\n[9] Testing Header Variations (like working probe)")
        for header in [0x00, 0x01, 0x02, 0x03, 0x10, 0x11, 0x20, 0xAA, 0xFF]:
            data = bytes([header] + [0x00] * 63)
            device.write(data)
            response = device.read(timeout=200)
            if response:
                print(f"  0x{header:02x} -> Response: {bytes(response[:7]).hex()}")
                # If we get response, try multiple times
                for _ in range(5):
                    device.write(data)
                    time.sleep(0.2)
            time.sleep(0.3)

        print("\n" + "="*70)
        print("If screen is STILL OFF after all this:")
        print("1. The device needs physical power cycle (USB unplug)")
        print("2. OR there's a specific wake sequence we haven't found yet")
        print("\nIs the screen ON now? (y/n)")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nInterrupted")
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
