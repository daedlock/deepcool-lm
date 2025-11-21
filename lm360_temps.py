#!/usr/bin/env python3
"""
LM360 Temperature Display Driver
Sends CPU/GPU temperatures to the LCD display
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

    def send_init(self):
        """Send init command (switches to temperature display mode)"""
        # This is the REAL init from capture - switches to temp display
        cmd = bytes([0xaa, 0x01, 0x00, 0x09, 0x29, 0x91])
        self.write(cmd)

    def send_temperatures(self, cpu_temp, gpu_temp):
        """
        Send temperature data to display
        Temps are encoded as (temp * 10) in little-endian 16-bit format
        """
        # Encode temperatures (multiply by 10 for decimal precision)
        cpu_encoded = int(cpu_temp * 10)
        gpu_encoded = int(gpu_temp * 10)

        # Convert to little-endian bytes
        cpu_low = cpu_encoded & 0xFF
        cpu_high = (cpu_encoded >> 8) & 0xFF
        gpu_low = gpu_encoded & 0xFF
        gpu_high = (gpu_encoded >> 8) & 0xFF

        # Build temperature packet
        # Format: aa 08 00 00 01 00 [cpu_low] [cpu_high] 00 [gpu_low] [gpu_high] [checksum_low] [checksum_high]
        cmd = bytes([
            0xaa, 0x08, 0x00, 0x00, 0x01, 0x00,
            cpu_low, cpu_high, 0x00,
            gpu_low, gpu_high,
            0xbc, 0x11  # Checksum from capture (might be fixed or calculated)
        ])

        self.write(cmd)

    def brightness_up(self):
        """Increase brightness"""
        cmd = bytes([0xaa, 0x04, 0x00, 0x06, 0x03, 0x61, 0x00, 0xd2, 0x46])
        self.write(cmd)

    def brightness_down(self):
        """Decrease brightness"""
        cmd = bytes([0xaa, 0x04, 0x00, 0x06, 0x03, 0x1d, 0x00, 0xe6, 0x0b])
        self.write(cmd)

    def disconnect(self):
        if self.dev:
            try:
                usb.util.release_interface(self.dev, self.interface)
                usb.util.dispose_resources(self.dev)
            except:
                pass

def get_cpu_temp():
    """Get CPU temperature"""
    try:
        temps = psutil.sensors_temperatures()
        if 'k10temp' in temps:
            return round(temps['k10temp'][0].current, 1)
        elif 'coretemp' in temps:
            # Use Package id 0 for overall CPU temp
            return round(temps['coretemp'][0].current, 1)
        for name, entries in temps.items():
            if entries and 'cpu' in name.lower():
                return round(entries[0].current, 1)
    except Exception as e:
        print(f"Error reading CPU temp: {e}")
    return 0.0

def get_gpu_temp():
    """Get GPU temperature (or fallback to other sensor)"""
    try:
        temps = psutil.sensors_temperatures()
        if 'amdgpu' in temps:
            return round(temps['amdgpu'][0].current, 1)
        elif 'nvidia' in temps:
            return round(temps['nvidia'][0].current, 1)
        # Fallback to NVMe or other sensor as "second temp"
        elif 'nvme' in temps:
            return round(temps['nvme'][0].current, 1)
        elif 'acpitz' in temps:
            return round(temps['acpitz'][0].current, 1)
    except Exception as e:
        print(f"Error reading GPU/sensor temp: {e}")
    return 0.0

def get_cpu_freq():
    """Get CPU frequency in GHz"""
    try:
        freq = psutil.cpu_freq()
        if freq:
            return round(freq.current / 1000, 2)  # Convert MHz to GHz
    except:
        pass
    return 0.0

def main():
    print("="*70)
    print("Deepcool LM360 Temperature Display Driver")
    print("="*70)
    print()

    device = LM360()

    if not device.connect():
        print("✗ Failed to connect to LM360")
        print("  Make sure:")
        print("  - Device is plugged in (lsusb | grep 3633)")
        print("  - Running with sudo")
        print("  - Not attached to VM")
        sys.exit(1)

    print("✓ Connected to LM360")
    print()

    try:
        # Send the REAL init command
        print("Initializing display for temperature mode...")
        device.send_init()
        time.sleep(1)

        print("✓ Init sent")
        print("\nStarting temperature updates...")
        print("The display should show CPU and GPU temperatures!")
        print("Press Ctrl+C to stop\n")
        print("="*70)

        update_count = 0
        while True:
            cpu_temp = get_cpu_temp()
            gpu_temp = get_gpu_temp()
            cpu_freq = get_cpu_freq()

            # Send temperature update
            device.send_temperatures(cpu_temp, gpu_temp)

            update_count += 1
            print(f"Update #{update_count:4d} | CPU: {cpu_temp:5.1f}°C | GPU: {gpu_temp:5.1f}°C | Freq: {cpu_freq:.2f}GHz", end='\r')

            time.sleep(1)  # Update every second

    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("Stopped by user")
        print(f"Sent {update_count} temperature updates")
    finally:
        device.disconnect()
        print("✓ Disconnected")

if __name__ == "__main__":
    main()
