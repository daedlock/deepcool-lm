#!/usr/bin/env python3
"""
Test different display modes from captured commands
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
    cpu_temp = 0
    gpu_temp = 0
    try:
        temps = psutil.sensors_temperatures()
        if 'k10temp' in temps:
            cpu_temp = round(temps['k10temp'][0].current)
        elif 'coretemp' in temps:
            cpu_temp = round(temps['coretemp'][0].current)
        if 'amdgpu' in temps:
            gpu_temp = round(temps['amdgpu'][0].current)
    except:
        pass
    return cpu_temp or 45, gpu_temp or 40

def main():
    print("="*70)
    print("Testing Display Modes and Temperature Updates")
    print("="*70)
    print()

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected")
    print("\nWATCH YOUR SCREEN!\n")
    print("="*70)

    try:
        # Init
        print("[1] Sending INIT command...")
        device.write(bytes([0xaa, 0x04, 0x00, 0x03, 0x00, 0x00, 0x00, 0xdc, 0x9b]))
        time.sleep(2)

        # Try mode commands from capture
        print("\n[2] Testing mode command: aa 04 00 06 03 1d 00 e6 0b")
        device.write(bytes([0xaa, 0x04, 0x00, 0x06, 0x03, 0x1d, 0x00, 0xe6, 0x0b]))
        time.sleep(3)
        input("    Press ENTER to continue...")

        print("\n[3] Testing mode command: aa 04 00 06 03 47 00 92 ea")
        device.write(bytes([0xaa, 0x04, 0x00, 0x06, 0x03, 0x47, 0x00, 0x92, 0xea]))
        time.sleep(3)
        input("    Press ENTER to continue...")

        print("\n[4] Testing mode command: aa 04 00 06 03 61 00 d2 46")
        device.write(bytes([0xaa, 0x04, 0x00, 0x06, 0x03, 0x61, 0x00, 0xd2, 0x46]))
        time.sleep(3)
        input("    Press ENTER to continue...")

        # Now send temperature updates with the captured pattern
        print("\n[5] Sending temperature updates (exact captured pattern)...")
        print("    Pattern: aa 08 00 00 01 00 58 02 00 2c 01 bc 11")
        print("    (This is 60.0°C / 30.0°C from Windows)")

        for i in range(10):
            device.write(bytes([0xaa, 0x08, 0x00, 0x00, 0x01, 0x00, 0x58, 0x02, 0x00, 0x2c, 0x01, 0xbc, 0x11]))
            print(f"    Update {i+1}/10", end='\r')
            time.sleep(1)

        print("\n\n[6] Now trying with REAL temperatures...")
        cpu_temp, gpu_temp = get_temps()
        print(f"    Current: CPU {cpu_temp}°C, GPU {gpu_temp}°C")

        # Encode temps as seen in capture (multiply by 10 for decimal)
        cpu_temp_encoded = cpu_temp * 10  # e.g., 45°C -> 450
        gpu_temp_encoded = gpu_temp * 10  # e.g., 40°C -> 400

        # Split into low/high bytes (little-endian)
        cpu_low = cpu_temp_encoded & 0xFF
        cpu_high = (cpu_temp_encoded >> 8) & 0xFF
        gpu_low = gpu_temp_encoded & 0xFF
        gpu_high = (gpu_temp_encoded >> 8) & 0xFF

        for i in range(20):
            # Update temps each iteration
            cpu_temp, gpu_temp = get_temps()
            cpu_temp_encoded = cpu_temp * 10
            gpu_temp_encoded = gpu_temp * 10
            cpu_low = cpu_temp_encoded & 0xFF
            cpu_high = (cpu_temp_encoded >> 8) & 0xFF
            gpu_low = gpu_temp_encoded & 0xFF
            gpu_high = (gpu_temp_encoded >> 8) & 0xFF

            # Send with temperatures at bytes 6-7 and 9-10
            cmd = bytes([0xaa, 0x08, 0x00, 0x00, 0x01, 0x00,
                        cpu_low, cpu_high, 0x00,
                        gpu_low, gpu_high,
                        0xbc, 0x11])

            device.write(cmd)
            print(f"    Update {i+1}/20: CPU {cpu_temp}°C ({cpu_temp_encoded}), GPU {gpu_temp}°C ({gpu_temp_encoded})", end='\r')
            time.sleep(1)

        print("\n\n" + "="*70)
        print("Did you see temperature values on screen?")
        print("Did any of the mode commands change the display?")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nInterrupted")
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
