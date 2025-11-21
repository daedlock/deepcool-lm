#!/usr/bin/env python3
"""
Now that the screen is ON, let's try to send temperature data!
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
            print(f"Write error: {e}")
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
    """Get CPU and GPU temperatures"""
    cpu_temp = 0
    gpu_temp = 0

    try:
        temps = psutil.sensors_temperatures()
        # CPU
        if 'k10temp' in temps:
            cpu_temp = round(temps['k10temp'][0].current)
        elif 'coretemp' in temps:
            cpu_temp = round(temps['coretemp'][0].current)

        # GPU (try amdgpu or nvidia)
        if 'amdgpu' in temps:
            gpu_temp = round(temps['amdgpu'][0].current)
        elif 'nvidia' in temps:
            gpu_temp = round(temps['nvidia'][0].current)
    except:
        pass

    return cpu_temp or 45, gpu_temp or 40

def main():
    print("="*70)
    print("LM360 Temperature Display Test")
    print("="*70)
    print("Screen should already be showing logo...")
    print()

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected\n")

    try:
        cpu_temp, gpu_temp = get_temps()
        print(f"Current temps - CPU: {cpu_temp}°C, GPU: {gpu_temp}°C\n")

        # Try different temperature data formats
        print("Trying to send temperature data...")
        print("WATCH YOUR SCREEN for any changes!\n")

        # Format 1: Simple ASCII text
        print("[1] ASCII text format...")
        text1 = f"CPU:{cpu_temp}C GPU:{gpu_temp}C".encode('ascii')
        device.write(text1 + b'\x00' * (64 - len(text1)))
        time.sleep(2)

        # Format 2: Command with temperature values
        print("[2] Command 0x55 0x10 with temp data...")
        data2 = bytes([0x55, 0x10, cpu_temp, gpu_temp] + [0x00]*60)
        device.write(data2)
        time.sleep(2)

        # Format 3: Different command
        print("[3] Command 0x55 0x20 with temp data...")
        data3 = bytes([0x55, 0x20, cpu_temp, gpu_temp] + [0x00]*60)
        device.write(data3)
        time.sleep(2)

        # Format 4: Multi-byte temperature format
        print("[4] Multi-byte format with 0x55 0x30...")
        data4 = bytes([0x55, 0x30, 0x01, cpu_temp, 0x02, gpu_temp] + [0x00]*58)
        device.write(data4)
        time.sleep(2)

        # Format 5: Try the response pattern with temps
        print("[5] Modified response pattern with temps...")
        data5 = bytes([0x55, 0x02, cpu_temp, gpu_temp, 0x0a, 0x81, 0x4e] + [0x00]*57)
        device.write(data5)
        time.sleep(2)

        # Format 6: Larger packet with temperature data
        print("[6] 512-byte packet with temp data at start...")
        data6 = bytearray([0x55, 0x50] + [0x00]*510)
        data6[2] = cpu_temp
        data6[3] = gpu_temp
        device.write(data6)
        time.sleep(2)

        # Format 7: Text display command
        print("[7] Text display command attempt...")
        data7 = bytes([0x55, 0x60, 0x00, 0x00] + list(f"CPU {cpu_temp}C".encode('ascii')) + [0x00]*50)
        device.write(data7)
        time.sleep(2)

        # Format 8: Try sending continuous data
        print("\n[8] Continuous temperature updates (10 seconds)...")
        print("Updating every second...")
        for i in range(10):
            cpu_temp, gpu_temp = get_temps()

            # Try multiple formats rapidly
            device.write(bytes([0x55, 0x10, cpu_temp, gpu_temp] + [0x00]*60))
            time.sleep(0.3)
            device.write(bytes([0x55, 0x20, cpu_temp, gpu_temp] + [0x00]*60))
            time.sleep(0.7)

            print(f"  Update {i+1}/10: CPU {cpu_temp}°C, GPU {gpu_temp}°C")

        print("\n" + "="*70)
        print("Did you see ANY temperature values on the screen?")
        print("Or did the display change in any way?")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\nInterrupted")
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
