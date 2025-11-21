#!/usr/bin/env python3
"""
LM360 Temperature Display - WORKING VERSION
Based EXACTLY on test_framebuffer.py structure
"""
import usb.core
import usb.util
import sys
import time
import psutil
from PIL import Image, ImageDraw, ImageFont

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
            return self.dev.write(EP_OUT, data, timeout=5000)
        except Exception as e:
            print(f"Write error: {e}")
            return 0

    def disconnect(self):
        if self.dev:
            try:
                usb.util.release_interface(self.dev, self.interface)
                usb.util.dispose_resources(self.dev)
            except:
                pass

def render_temps_to_framebuffer(cpu_temp, gpu_temp, cpu_freq):
    """
    Render temperature display and return framebuffer
    EXACTLY like test_framebuffer.py builds framebuffers
    """
    # Create 320x240 image
    img = Image.new('RGB', (320, 240), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 70)
        font_med = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 24)
    except:
        font_big = ImageFont.load_default()
        font_med = ImageFont.load_default()

    # Draw separator line
    draw.line([(160, 40), (160, 230)], fill=(100, 100, 100), width=2)

    # Draw CPU temp (left)
    draw.text((20, 80), f"{cpu_temp:.0f}", fill=(0, 255, 0), font=font_big)
    draw.text((30, 170), "CPU °C", fill=(150, 150, 150), font=font_med)

    # Draw GPU temp (right)
    draw.text((180, 80), f"{gpu_temp:.0f}", fill=(0, 255, 255), font=font_big)
    draw.text((180, 170), "GPU °C", fill=(150, 150, 150), font=font_med)

    # Draw freq at top
    draw.text((110, 10), f"{cpu_freq:.1f}GHz", fill=(200, 200, 200), font=font_med)

    # Convert to RGB565 framebuffer - EXACTLY like test_framebuffer.py
    framebuffer = bytearray()
    pixels = img.load()

    for y in range(240):
        for x in range(320):
            r, g, b = pixels[x, y]
            # Convert to RGB565
            r5 = (r >> 3) & 0x1F
            g6 = (g >> 2) & 0x3F
            b5 = (b >> 3) & 0x1F
            rgb565 = (r5 << 11) | (g6 << 5) | b5
            # Append as little-endian
            framebuffer.append(rgb565 & 0xFF)        # Low byte
            framebuffer.append((rgb565 >> 8) & 0xFF)  # High byte

    return bytes(framebuffer)

def get_temps():
    try:
        temps = psutil.sensors_temperatures()
        cpu = round(temps['coretemp'][0].current, 1) if 'coretemp' in temps else 0.0
        gpu = round(temps['nvme'][0].current, 1) if 'nvme' in temps else 0.0
        return cpu, gpu
    except:
        return 0.0, 0.0

def get_cpu_freq():
    try:
        freq = psutil.cpu_freq()
        return round(freq.current / 1000, 2) if freq else 0.0
    except:
        return 0.0

def main():
    print("="*70)
    print("LM360 Temperature Display - WORKING VERSION")
    print("="*70)
    print()

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected\n")

    try:
        # EXACT header from test_framebuffer.py that WORKS
        header = bytes([0xaa, 0x08, 0x00, 0x00, 0x01, 0x00, 0x58, 0x02, 0x00, 0x2c, 0x01, 0xbc, 0x11])

        print("Sending temperature frames...")
        print("Press Ctrl+C to stop\n")

        frame_count = 0
        while True:
            cpu_temp, gpu_temp = get_temps()
            cpu_freq = get_cpu_freq()

            # Render framebuffer
            framebuffer = render_temps_to_framebuffer(cpu_temp, gpu_temp, cpu_freq)

            # Send EXACTLY like test_framebuffer.py
            device.write(header)
            device.write(framebuffer)

            frame_count += 1
            print(f"Frame {frame_count:4d} | CPU: {cpu_temp:5.1f}°C | GPU: {gpu_temp:5.1f}°C | {cpu_freq:.2f}GHz", end='\r')

            time.sleep(2)

    except KeyboardInterrupt:
        print(f"\n\nStopped after {frame_count} frames")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
