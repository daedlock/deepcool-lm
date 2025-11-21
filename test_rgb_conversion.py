#!/usr/bin/env python3
"""
Test RGB565 conversion to find the bug
"""

def rgb888_to_rgb565_OLD(r, g, b):
    """Current (possibly broken) conversion"""
    r5 = (r >> 3) & 0x1F
    g6 = (g >> 2) & 0x3F
    b5 = (b >> 3) & 0x1F
    rgb565 = (r5 << 11) | (g6 << 5) | b5
    return rgb565

# Test with pure red (255, 0, 0)
r, g, b = 255, 0, 0
rgb565 = rgb888_to_rgb565_OLD(r, g, b)
low = rgb565 & 0xFF
high = (rgb565 >> 8) & 0xFF

print("Testing RGB888 to RGB565 conversion:")
print(f"RGB(255, 0, 0) -> RGB565: 0x{rgb565:04X}")
print(f"Low byte: 0x{low:02X}, High byte: 0x{high:02X}")
print(f"Expected: Low=0x00, High=0xF8")
print()

# Test with pure green
r, g, b = 0, 255, 0
rgb565 = rgb888_to_rgb565_OLD(r, g, b)
low = rgb565 & 0xFF
high = (rgb565 >> 8) & 0xFF
print(f"RGB(0, 255, 0) -> RGB565: 0x{rgb565:04X}")
print(f"Low byte: 0x{low:02X}, High byte: 0x{high:02X}")
print(f"Expected: Low=0xE0, High=0x07")
print()

# Test with pure blue
r, g, b = 0, 0, 255
rgb565 = rgb888_to_rgb565_OLD(r, g, b)
low = rgb565 & 0xFF
high = (rgb565 >> 8) & 0xFF
print(f"RGB(0, 0, 255) -> RGB565: 0x{rgb565:04X}")
print(f"Low byte: 0x{low:02X}, High byte: 0x{high:02X}")
print(f"Expected: Low=0x1F, High=0x00")
print()

# Test with white
r, g, b = 255, 255, 255
rgb565 = rgb888_to_rgb565_OLD(r, g, b)
low = rgb565 & 0xFF
high = (rgb565 >> 8) & 0xFF
print(f"RGB(255, 255, 255) -> RGB565: 0x{rgb565:04X}")
print(f"Low byte: 0x{low:02X}, High byte: 0x{high:02X}")
print(f"Expected: Low=0xFF, High=0xFF")
