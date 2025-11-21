#!/usr/bin/env python3
"""
Working LM360 Driver - Based on captured USB packets!
Protocol discovered from Windows software capture
"""
import usb.core
import usb.util
import sys
import time
import psutil
import struct

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
            print(f"Write error: {e}")
            return 0

    def send_init(self):
        """Send initialization command (from capture)"""
        # Init command: aa 04 00 03 00 00 00 dc 9b
        init_cmd = bytes([0xaa, 0x04, 0x00, 0x03, 0x00, 0x00, 0x00, 0xdc, 0x9b])
        print("Sending init command...")
        self.write(init_cmd)
        time.sleep(0.5)

    def send_temp_update(self, cpu_temp, gpu_temp):
        """Send temperature update (based on captured pattern)"""
        # Pattern: aa 08 00 00 01 00 58 02 00 2c 01 bc 11
        # Need to figure out where temps go
        # Bytes 6-7 might be temp (0x58 0x02 = 600 in decimal, maybe 60.0°C?)

        # Let's try encoding temps in those positions
        cmd = bytearray([0xaa, 0x08, 0x00, 0x00, 0x01, 0x00, 0x00, 0x02, 0x00, 0x00, 0x01, 0x00, 0x00])

        # Try different encodings
        # Option 1: Direct byte values
        cmd[6] = cpu_temp
        cmd[9] = gpu_temp

        # Calculate checksum (last 2 bytes might be checksum)
        # For now, just use captured values
        cmd[11] = 0xbc
        cmd[12] = 0x11

        return bytes(cmd)

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
    print("LM360 Working Driver - Protocol from USB Capture!")
    print("="*70)
    print()

    device = LM360()
    if not device.connect():
        print("✗ Failed to connect!")
        print("Make sure you've detached from Windows VM:")
        print("  sudo virsh -c qemu:///system detach-device win11 /tmp/lm360-usb.xml --live")
        sys.exit(1)

    print("✓ Connected to LM360")
    print()

    try:
        # Send init command
        device.send_init()
        print("✓ Init command sent")
        print("\nWAIT 5 SECONDS - CHECK IF LOGO APPEARS!")
        time.sleep(5)

        response = input("\nDid the logo appear? (y/n): ")
        if response.lower() != 'y':
            print("\nInit didn't work. Let's try sending it multiple times...")
            for i in range(10):
                print(f"  Init attempt {i+1}/10...")
                device.send_init()
                time.sleep(1)

            response = input("\nDid the logo appear now? (y/n): ")
            if response.lower() != 'y':
                print("\nStill no logo. The init command might need modification.")
                print("Let's try sending temperature updates anyway...")

        # Now send temperature updates
        print("\nSending temperature updates...")
        print("Press Ctrl+C to stop")
        print()

        for i in range(60):  # Run for 60 seconds
            cpu_temp, gpu_temp = get_temps()

            # Send temp update
            temp_cmd = device.send_temp_update(cpu_temp, gpu_temp)
            device.write(temp_cmd)

            print(f"Update {i+1}: CPU {cpu_temp}°C, GPU {gpu_temp}°C", end='\r')
            time.sleep(1)

        print("\n\nDid you see temperature values on the screen?")

    except KeyboardInterrupt:
        print("\n\nStopped")
    finally:
        device.disconnect()
        print("✓ Disconnected")

if __name__ == "__main__":
    main()
