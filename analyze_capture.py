#!/usr/bin/env python3
"""
Analyze USB capture from usbmon to extract LM360 commands
"""
import sys
import re
from collections import defaultdict

def parse_usbmon_line(line):
    """Parse a usbmon line and extract relevant info"""
    # Format: address timestamp direction endpoint status length = data
    # Example: ffff8cfe802fdbc0 3868468944 S Bo:1:010:1 -115 9 = aa040003 000000dc 9b

    parts = line.strip().split()
    if len(parts) < 7:
        return None

    timestamp = parts[1]
    direction = parts[2]  # S=Submit, C=Complete
    endpoint_info = parts[3]  # e.g., Bo:1:010:1

    # Parse endpoint: Bo:bus:device:endpoint
    ep_match = re.match(r'([A-Z][io]):(\d+):(\d+):(\d+)', endpoint_info)
    if not ep_match:
        return None

    transfer_type = ep_match.group(1)  # Bo=Bulk Out, Bi=Bulk In, etc.
    bus = int(ep_match.group(2))
    device = int(ep_match.group(3))
    endpoint = int(ep_match.group(4))

    # Get data if present
    data = None
    if '=' in line:
        data_start = line.index('=') + 1
        data_hex = line[data_start:].strip()
        # Remove spaces to get continuous hex
        data_hex = data_hex.replace(' ', '')
        data = data_hex

    return {
        'timestamp': timestamp,
        'direction': direction,
        'transfer_type': transfer_type,
        'bus': bus,
        'device': device,
        'endpoint': endpoint,
        'data': data
    }

def analyze_capture(filename, target_device=10):
    """Analyze USB capture for target device"""

    print(f"Analyzing: {filename}")
    print(f"Target device: {target_device}")
    print("="*70)

    out_packets = []  # Bulk OUT (to device)
    in_packets = []   # Bulk IN (from device)

    with open(filename, 'r') as f:
        for line in f:
            parsed = parse_usbmon_line(line)
            if not parsed:
                continue

            # Only look at our target device (LM360)
            if parsed['device'] != target_device:
                continue

            # Only look at Bulk transfers (Bo/Bi)
            if not parsed['transfer_type'].startswith('B'):
                continue

            # Only look at Submit (S) commands with data
            if parsed['direction'] != 'S' or not parsed['data']:
                continue

            if parsed['transfer_type'] == 'Bo':  # Bulk OUT (to device)
                out_packets.append(parsed)
            elif parsed['transfer_type'] == 'Bi':  # Bulk IN (from device)
                in_packets.append(parsed)

    print(f"\nFound {len(out_packets)} packets sent TO device (Bulk OUT)")
    print(f"Found {len(in_packets)} packets received FROM device (Bulk IN)")
    print()

    # Group similar packets
    unique_packets = defaultdict(list)
    for pkt in out_packets:
        # Group by first 16 bytes (ignore minor variations)
        key = pkt['data'][:32] if len(pkt['data']) > 32 else pkt['data']
        unique_packets[key].append(pkt)

    print(f"Found {len(unique_packets)} unique packet patterns")
    print("="*70)
    print()

    # Show first 20 unique packets (likely initialization)
    print("FIRST 20 UNIQUE PACKET PATTERNS (Initialization):")
    print("="*70)
    for i, (pattern, packets) in enumerate(list(unique_packets.items())[:20]):
        first_pkt = packets[0]
        data_bytes = bytes.fromhex(first_pkt['data'])

        print(f"\n[{i+1}] Pattern (seen {len(packets)} times):")
        print(f"    Length: {len(data_bytes)} bytes")
        print(f"    Hex: {first_pkt['data'][:64]}{'...' if len(first_pkt['data']) > 64 else ''}")
        print(f"    Bytes: {' '.join(f'{b:02x}' for b in data_bytes[:32])}")

        # Try to interpret as ASCII if printable
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data_bytes[:32])
        print(f"    ASCII: {ascii_str}")

    # Save all unique packets to file
    output_file = filename.replace('.txt', '_analysis.txt')
    with open(output_file, 'w') as f:
        f.write("LM360 USB Packet Analysis\n")
        f.write("="*70 + "\n\n")

        for i, (pattern, packets) in enumerate(unique_packets.items()):
            first_pkt = packets[0]
            data_bytes = bytes.fromhex(first_pkt['data'])

            f.write(f"Packet {i+1} (count: {len(packets)}):\n")
            f.write(f"  Hex: {first_pkt['data']}\n")
            f.write(f"  Bytes: {' '.join(f'{b:02x}' for b in data_bytes)}\n")
            f.write(f"  Length: {len(data_bytes)}\n")
            f.write("\n")

    print(f"\n\nFull analysis saved to: {output_file}")
    print("="*70)

    return out_packets, unique_packets

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 analyze_capture.py <capture_file>")
        sys.exit(1)

    capture_file = sys.argv[1]
    analyze_capture(capture_file)
