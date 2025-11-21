#!/usr/bin/env python3
"""
Deepcool LM360 USB Probe Script
This script attempts to communicate with the LM360 and probe its USB protocol.
"""

import hid
import sys
import time
import psutil

# LM360 USB IDs
VENDOR_ID = 0x3633
PRODUCT_ID = 0x0026

def list_deepcool_devices():
    """List all Deepcool devices connected to the system."""
    print("=== Scanning for Deepcool devices ===")
    devices = []
    for device in hid.enumerate():
        if device['vendor_id'] == VENDOR_ID:
            devices.append(device)
            print(f"\n  Found Deepcool Device:")
            print(f"    Vendor ID:  0x{device['vendor_id']:04x}")
            print(f"    Product ID: 0x{device['product_id']:04x}")
            print(f"    Product:    {device['product_string']}")
            print(f"    Manufacturer: {device['manufacturer_string']}")
            print(f"    Path:       {device['path']}")

    if not devices:
        print("  No Deepcool devices found!")
    return devices

def get_cpu_temp():
    """Get current CPU temperature."""
    try:
        temps = psutil.sensors_temperatures()
        # Try k10temp first (AMD)
        if 'k10temp' in temps:
            return round(temps['k10temp'][0].current)
        # Try coretemp (Intel)
        elif 'coretemp' in temps:
            return round(temps['coretemp'][0].current)
        # Fallback to first available sensor
        for name, entries in temps.items():
            if entries:
                return round(entries[0].current)
    except:
        pass
    return 0

def get_cpu_usage():
    """Get current CPU usage percentage."""
    return round(psutil.cpu_percent(interval=0.1))

def try_open_device():
    """Try to open the LM360 device."""
    print("\n=== Attempting to open LM360 ===")
    try:
        h = hid.device()
        h.open(VENDOR_ID, PRODUCT_ID)
        h.set_nonblocking(1)
        print("  ✓ Successfully opened LM360!")
        return h
    except IOError as e:
        print(f"  ✗ Failed to open device: {e}")
        print("  Hint: Try running with sudo")
        return None

def probe_device_info(device):
    """Try to read device information."""
    print("\n=== Device Information ===")
    try:
        manufacturer = device.get_manufacturer_string()
        product = device.get_product_string()
        serial = device.get_serial_number_string()

        print(f"  Manufacturer: {manufacturer}")
        print(f"  Product:      {product}")
        print(f"  Serial:       {serial}")
    except Exception as e:
        print(f"  Could not read device info: {e}")

def try_existing_protocols(device):
    """Try protocols from existing Deepcool drivers."""
    print("\n=== Testing Known Protocols ===")

    # Protocol 1: Complex mode initialization (from AK series)
    print("\n  [1] Trying AK series init sequence...")
    init_data = [16, 170] + [0] * 62
    try:
        bytes_written = device.write(init_data)
        print(f"      Wrote {bytes_written} bytes")
        time.sleep(0.5)

        # Try reading response
        response = device.read(64, timeout_ms=1000)
        if response:
            print(f"      Response: {list(response)}")
        else:
            print("      No response")
    except Exception as e:
        print(f"      Error: {e}")

    # Protocol 2: Simple ASCII mode (from CH510)
    print("\n  [2] Trying CH510 ASCII protocol...")
    temp = get_cpu_temp()
    usage = get_cpu_usage()
    ascii_data = f"_HLXDATA({usage},{temp},0,0,C)".encode('ascii')
    try:
        bytes_written = device.write(ascii_data)
        print(f"      Wrote {bytes_written} bytes: {ascii_data}")
        time.sleep(0.5)

        response = device.read(64, timeout_ms=1000)
        if response:
            print(f"      Response: {list(response)}")
        else:
            print("      No response")
    except Exception as e:
        print(f"      Error: {e}")

    # Protocol 3: Complex temperature data (from AK series)
    print("\n  [3] Trying AK series temperature display...")
    temp = get_cpu_temp()
    temp_data = [16, 19, 0] + [int(d) for d in str(temp).zfill(2)] + [0] * 58
    temp_data[2] = (temp - 1) // 10 + 1  # Bar value
    try:
        bytes_written = device.write(temp_data)
        print(f"      Wrote {bytes_written} bytes")
        print(f"      Data: {temp_data[:10]}...")
        time.sleep(0.5)

        response = device.read(64, timeout_ms=1000)
        if response:
            print(f"      Response: {list(response)}")
        else:
            print("      No response")
    except Exception as e:
        print(f"      Error: {e}")

def experimental_probe(device):
    """Try experimental packet formats."""
    print("\n=== Experimental Probing ===")
    print("  This section will try various packet formats to find")
    print("  what the LM360 responds to...")

    # Experiment 1: Try different packet sizes
    print("\n  [Exp 1] Testing different packet sizes...")
    for size in [8, 16, 32, 64, 128, 256, 512]:
        try:
            data = [0x00] * size
            data[0] = 0x01  # Common USB HID report ID
            bytes_written = device.write(data)
            print(f"    Size {size}: wrote {bytes_written} bytes")
            time.sleep(0.1)
        except Exception as e:
            print(f"    Size {size}: {e}")

    # Experiment 2: Try different header bytes
    print("\n  [Exp 2] Testing different header bytes...")
    for header in [0x00, 0x01, 0x02, 0x10, 0x11, 0x20, 0xAA, 0xFF]:
        try:
            data = [header] + [0] * 63
            bytes_written = device.write(data)
            print(f"    Header 0x{header:02x}: wrote {bytes_written} bytes")
            time.sleep(0.1)

            # Check for response
            response = device.read(64, timeout_ms=100)
            if response:
                print(f"      → Response: {list(response[:8])}...")
        except Exception as e:
            print(f"    Header 0x{header:02x}: {e}")

def main():
    """Main execution function."""
    print("=" * 60)
    print("Deepcool LM360 USB Probe Script")
    print("=" * 60)

    # Step 1: List all Deepcool devices
    devices = list_deepcool_devices()

    if not any(d['product_id'] == PRODUCT_ID for d in devices):
        print("\n✗ LM360 (Product ID 0x0026) not found!")
        print("  Make sure the device is plugged in and detected by lsusb")
        sys.exit(1)

    # Step 2: Try to open the device
    device = try_open_device()
    if not device:
        sys.exit(1)

    try:
        # Step 3: Get device information
        probe_device_info(device)

        # Step 4: Try existing protocols
        try_existing_protocols(device)

        # Step 5: Experimental probing
        print("\n" + "=" * 60)
        response = input("Run experimental probing? (y/N): ")
        if response.lower() == 'y':
            experimental_probe(device)

        print("\n" + "=" * 60)
        print("Probing complete!")
        print("\nNext steps:")
        print("  1. Review the output above")
        print("  2. If no protocol worked, we need USB packet capture")
        print("  3. See FINDINGS.md for USB capture instructions")

    finally:
        device.close()
        print("\nDevice closed.")

if __name__ == "__main__":
    main()
