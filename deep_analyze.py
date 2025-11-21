#!/usr/bin/env python3
"""
Deep analysis - find temperature data patterns
"""
import sys

def analyze_temp_packets(filename):
    """Look at the frequent update packets in detail"""

    print("="*70)
    print("DEEP ANALYSIS - Temperature Update Packets")
    print("="*70)
    print()

    # Read all lines
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Find all packets to device 010 on endpoint 1 (Bulk OUT)
    packets = []
    for line in lines:
        if 'Bo:1:010:1' in line and ' S ' in line and '=' in line:
            # Extract the hex data
            data_part = line.split('=')[1].strip()
            # Remove spaces
            data_hex = data_part.replace(' ', '')
            packets.append(data_hex)

    print(f"Found {len(packets)} packets sent to device")
    print()

    # Look at packets starting with 'aa08' (the frequent update pattern)
    aa08_packets = [p for p in packets if p.startswith('aa08')]
    print(f"Found {len(aa08_packets)} packets starting with 'aa08'")
    print()

    # Show variations
    print("First 50 'aa08' packets (looking for patterns):")
    print("="*70)

    unique_variations = {}
    for i, pkt in enumerate(aa08_packets[:100]):
        if pkt not in unique_variations:
            unique_variations[pkt] = []
        unique_variations[pkt].append(i)

    print(f"\nFound {len(unique_variations)} unique variations in first 100 packets")
    print()

    for pkt, indices in list(unique_variations.items())[:20]:
        bytes_data = bytes.fromhex(pkt)
        print(f"Pattern (seen at indices {indices[:5]}...):")
        print(f"  Hex: {pkt}")
        print(f"  Bytes: {' '.join(f'{b:02x}' for b in bytes_data)}")

        # Try to interpret bytes
        if len(bytes_data) >= 13:
            print(f"  Byte[6-7]: {bytes_data[6]:02x} {bytes_data[7]:02x} = {bytes_data[6]} / {bytes_data[7]*256 + bytes_data[6]}")
            print(f"  Byte[9-10]: {bytes_data[9]:02x} {bytes_data[10]:02x} = {bytes_data[9]} / {bytes_data[10]*256 + bytes_data[9]}")
        print()

    # Show all unique aa08 packets
    print("="*70)
    print("ALL UNIQUE aa08 PACKETS:")
    print("="*70)
    for i, pkt in enumerate(unique_variations.keys()):
        bytes_data = bytes.fromhex(pkt)
        print(f"{i+1}. {' '.join(f'{b:02x}' for b in bytes_data)}")

    # Look for packets with other headers too
    print("\n" + "="*70)
    print("OTHER PACKET TYPES:")
    print("="*70)

    other_packets = [p for p in packets if not p.startswith('aa08') and not p.startswith('00000000') and not p.startswith('ffffffff')]
    unique_other = list(set(other_packets))

    for pkt in unique_other[:20]:
        bytes_data = bytes.fromhex(pkt)
        count = packets.count(pkt)
        print(f"Count {count:4d}: {' '.join(f'{b:02x}' for b in bytes_data)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 deep_analyze.py <capture_file>")
        sys.exit(1)

    analyze_temp_packets(sys.argv[1])
