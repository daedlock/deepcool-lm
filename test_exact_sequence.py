#!/usr/bin/env python3
"""
Test EXACT sequence from Windows capture
"""
import usb.core
import usb.util
import sys
import time
import psutil

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

def get_temps():
    try:
        temps = psutil.sensors_temperatures()
        cpu = round(temps['coretemp'][0].current, 1) if 'coretemp' in temps else 0.0
        gpu = round(temps['nvme'][0].current, 1) if 'nvme' in temps else 0.0
        return cpu, gpu
    except:
        return 0.0, 0.0

def main():
    print("="*70)
    print("Testing EXACT Windows Sequence")
    print("="*70)
    print()

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected")
    print("\nSending EXACT sequence from Windows:\n")

    try:
        # Step 1: Brightness
        print("[1] Brightness up: aa 04 00 06 03 61 00 d2 46")
        device.write(bytes([0xaa, 0x04, 0x00, 0x06, 0x03, 0x61, 0x00, 0xd2, 0x46]))
        time.sleep(0.5)

        # Step 2: Unknown command
        print("[2] Command: aa 01 00 09 29 91")
        device.write(bytes([0xaa, 0x01, 0x00, 0x09, 0x29, 0x91]))
        time.sleep(0.5)

        # Step 3: Start sending EXACT temperature packet from Windows
        print("[3] Sending Windows temperature packet...")
        print("    (60.0°C / 30.0°C from Windows VM)")
        print()

        # Send exact packet from Windows 5 times
        for i in range(5):
            device.write(bytes([0xaa, 0x08, 0x00, 0x00, 0x01, 0x00, 0x58, 0x02, 0x00, 0x2c, 0x01, 0xbc, 0x11]))
            print(f"    Sent exact Windows packet #{i+1}")
            time.sleep(1)

        print("\n" + "="*70)
        print("Did you see 60°C / 30°C on the display?")
        response = input("(y/n): ")

        if response.lower() == 'y':
            print("\n✓ SUCCESS! Now trying with YOUR real temperatures...\n")

            cpu, gpu = get_temps()
            print(f"Your temps: CPU {cpu}°C, GPU/NVMe {gpu}°C")

            # Encode temps
            cpu_encoded = int(cpu * 10)
            gpu_encoded = int(gpu * 10)
            cpu_low = cpu_encoded & 0xFF
            cpu_high = (cpu_encoded >> 8) & 0xFF
            gpu_low = gpu_encoded & 0xFF
            gpu_high = (gpu_encoded >> 8) & 0xFF

            print(f"Encoded: CPU={cpu_encoded} (0x{cpu_high:02x}{cpu_low:02x}), GPU={gpu_encoded} (0x{gpu_high:02x}{gpu_low:02x})")

            for i in range(20):
                cmd = bytes([0xaa, 0x08, 0x00, 0x00, 0x01, 0x00,
                            cpu_low, cpu_high, 0x00,
                            gpu_low, gpu_high,
                            0xbc, 0x11])
                device.write(cmd)
                print(f"    Update {i+1}/20: CPU {cpu}°C, GPU {gpu}°C        ", end='\r')
                time.sleep(1)

            print("\n\nDid YOUR temperatures show correctly?")

        else:
            print("\nThe exact Windows sequence didn't work.")
            print("The display might need to be in a specific state first.")
            print("Try unplugging and replugging the USB cable.")

    except KeyboardInterrupt:
        print("\n\nStopped")
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
