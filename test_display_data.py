#!/usr/bin/env python3
"""
Try sending actual display/frame data to change what's shown on screen
Since power commands don't work, maybe we need to send display content
"""
import usb.core
import usb.util
import sys
import time
import psutil

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
    print("LM360 Display Data Test")
    print("="*70)
    print("\nTrying to CHANGE what's displayed on screen...")
    print("Currently showing: LOGO")
    print("Goal: Show temperature data\n")

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected\n")

    try:
        cpu_temp, gpu_temp = get_temps()
        print(f"Current temps - CPU: {cpu_temp}°C, GPU: {gpu_temp}°C\n")
        print("="*70)
        print("WATCH YOUR SCREEN!\n")

        # Try 1: Simple text string
        print("[1] Plain ASCII text...")
        text = f"CPU {cpu_temp}C  GPU {gpu_temp}C"
        device.write(text.encode('ascii') + b'\x00' * (512 - len(text)))
        time.sleep(2)

        # Try 2: Text with command header
        print("[2] 0x55 0x50 + ASCII text...")
        data = bytes([0x55, 0x50]) + text.encode('ascii') + b'\x00' * (512 - len(text) - 2)
        device.write(data)
        time.sleep(2)

        # Try 3: Different command + text
        print("[3] 0x55 0x51 + ASCII text...")
        data = bytes([0x55, 0x51]) + text.encode('ascii') + b'\x00' * (512 - len(text) - 2)
        device.write(data)
        time.sleep(2)

        # Try 4: Command 0x02 variations (device responds to these)
        print("[4] 0x55 0x02 0x01 + temperature bytes...")
        data = bytes([0x55, 0x02, 0x01, cpu_temp, gpu_temp] + [0x00]*507)
        device.write(data)
        time.sleep(2)

        print("[5] 0x55 0x02 0x02 + temperature bytes...")
        data = bytes([0x55, 0x02, 0x02, cpu_temp, gpu_temp] + [0x00]*507)
        device.write(data)
        time.sleep(2)

        print("[6] 0x55 0x02 0x10 + temperature bytes...")
        data = bytes([0x55, 0x02, 0x10, cpu_temp, gpu_temp] + [0x00]*507)
        device.write(data)
        time.sleep(2)

        # Try 7: Mode change commands
        print("\n[7] Trying mode change commands...")
        print("  Mode 0x01...")
        device.write(bytes([0x55, 0x02, 0x01, 0x01] + [0x00]*508))
        time.sleep(1)

        print("  Mode 0x02...")
        device.write(bytes([0x55, 0x02, 0x01, 0x02] + [0x00]*508))
        time.sleep(1)

        print("  Mode 0x03...")
        device.write(bytes([0x55, 0x02, 0x01, 0x03] + [0x00]*508))
        time.sleep(1)

        # Try 8: Larger packets with structured data
        print("\n[8] Structured data packet...")
        packet = bytearray(512)
        packet[0] = 0x55  # Header
        packet[1] = 0x02  # Command
        packet[2] = 0x20  # Subcommand
        packet[3] = cpu_temp  # CPU temp
        packet[4] = gpu_temp  # GPU temp
        # Add ASCII labels
        label = b"CPU:    GPU:    "
        packet[10:10+len(label)] = label
        device.write(packet)
        time.sleep(2)

        # Try 9: Rapid updates to see if anything changes
        print("\n[9] Rapid continuous updates (15 seconds)...")
        print("  Trying different patterns rapidly...\n")

        for i in range(30):  # 30 updates over 15 seconds
            cpu_temp, gpu_temp = get_temps()

            # Rotate through different command patterns
            if i % 3 == 0:
                data = bytes([0x55, 0x02, 0x01, cpu_temp, gpu_temp] + [0x00]*507)
            elif i % 3 == 1:
                data = bytes([0x55, 0x02, 0x10, cpu_temp, gpu_temp] + [0x00]*507)
            else:
                data = bytes([0x55, 0x02, 0x20, cpu_temp, gpu_temp] + [0x00]*507)

            device.write(data)
            print(f"  Update {i+1}/30: CPU {cpu_temp}°C, GPU {gpu_temp}°C", end='\r')
            time.sleep(0.5)

        print("\n\n" + "="*70)
        print("RESULTS:")
        print("- Did the logo disappear?")
        print("- Did you see ANY numbers appear?")
        print("- Did ANYTHING change on screen?")
        print("- Or is it still just showing the logo?")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nInterrupted")
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
