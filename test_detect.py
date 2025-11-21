#!/usr/bin/env python3
"""
Simple test to detect and open the LM360
"""
import hid
import sys

VENDOR_ID = 0x3633
PRODUCT_ID = 0x0026

print("=" * 60)
print("Testing LM360 Detection")
print("=" * 60)

# List all HID devices
print("\n1. Enumerating all HID devices from vendor 0x3633...")
devices = hid.enumerate(VENDOR_ID, 0)

if not devices:
    print("   ERROR: No devices found with vendor ID 0x3633")
    print("   Make sure the LM360 is connected and showing in lsusb")
    sys.exit(1)

print(f"   Found {len(devices)} device(s):")
for i, d in enumerate(devices):
    print(f"\n   Device {i+1}:")
    print(f"     Vendor ID:  0x{d['vendor_id']:04x}")
    print(f"     Product ID: 0x{d['product_id']:04x}")
    print(f"     Product:    {d['product_string']}")
    print(f"     Manufacturer: {d['manufacturer_string']}")
    print(f"     Path:       {d['path']}")
    print(f"     Interface:  {d['interface_number']}")

# Check for LM360 specifically
lm360_devices = [d for d in devices if d['product_id'] == PRODUCT_ID]

if not lm360_devices:
    print(f"\n   ERROR: No LM360 (PID 0x{PRODUCT_ID:04x}) found")
    print("   Available product IDs:", [f"0x{d['product_id']:04x}" for d in devices])
    sys.exit(1)

print(f"\n2. Found LM360! Attempting to open device...")

try:
    h = hid.device()
    h.open(VENDOR_ID, PRODUCT_ID)
    print("   ✓ Successfully opened LM360!")

    # Get device info
    print("\n3. Reading device information...")
    try:
        manufacturer = h.get_manufacturer_string()
        product = h.get_product_string()
        serial = h.get_serial_number_string()

        print(f"   Manufacturer: {manufacturer}")
        print(f"   Product:      {product}")
        print(f"   Serial:       {serial}")
    except Exception as e:
        print(f"   Warning: Could not read strings: {e}")

    h.close()
    print("\n✓ SUCCESS: Device detected and opened successfully!")
    print("\nNext step: Run initialization sequence to show logo")

except IOError as e:
    print(f"   ✗ FAILED to open device: {e}")
    print("\n   This usually means:")
    print("   1. Permission denied - Try running with: sudo -E python3 test_detect.py")
    print("   2. Device is busy - Another program might be using it")
    print("   3. Wrong interface - Device has multiple HID interfaces")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ Unexpected error: {e}")
    sys.exit(1)

print("=" * 60)
