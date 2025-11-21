#!/usr/bin/env python3
"""
Test rendering to display - EXACT same approach as test_framebuffer.py but with rendered content
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
WIDTH = 320
HEIGHT = 240

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

def rgb888_to_rgb565(r, g, b):
    """Convert RGB888 to RGB565 format"""
    r5 = (r >> 3) & 0x1F
    g6 = (g >> 2) & 0x3F
    b5 = (b >> 3) & 0x1F
    rgb565 = (r5 << 11) | (g6 << 5) | b5
    return rgb565

def get_temp_color(temp):
    """Return RGB color based on temperature"""
    if temp < 40:
        return (100, 200, 255)
    elif temp < 60:
        return (100, 255, 100)
    elif temp < 75:
        return (255, 200, 50)
    elif temp < 85:
        return (255, 140, 0)
    else:
        return (255, 50, 50)

def render_simple(cpu_temp, gpu_temp, cpu_freq):
    """Render temperature display - SIMPLE version"""
    # Create image
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(20, 20, 30))
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 80)
        font_med = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 24)
    except:
        font_big = ImageFont.load_default()
        font_med = ImageFont.load_default()

    # Colors
    cpu_color = get_temp_color(cpu_temp)
    gpu_color = get_temp_color(gpu_temp)

    # Draw separator
    draw.line([(WIDTH//2, 40), (WIDTH//2, HEIGHT-10)], fill=(60, 60, 80), width=3)

    # CPU (left)
    cpu_text = f"{cpu_temp:.0f}"
    draw.text((30, 80), cpu_text, fill=cpu_color, font=font_big)
    draw.text((40, 180), "CPU °C", fill=(150, 150, 160), font=font_med)

    # GPU (right)
    gpu_text = f"{gpu_temp:.0f}"
    draw.text((190, 80), gpu_text, fill=gpu_color, font=font_big)
    draw.text((190, 180), "GPU °C", fill=(150, 150, 160), font=font_med)

    # Freq (top)
    freq_text = f"{cpu_freq:.1f}GHz"
    draw.text((WIDTH//2 - 50, 10), freq_text, fill=(180, 180, 200), font=font_med)

    # Convert to RGB565 - EXACTLY like test_framebuffer.py
    pixels = img.load()
    framebuffer = bytearray(WIDTH * HEIGHT * 2)

    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b = pixels[x, y]
            rgb565 = rgb888_to_rgb565(r, g, b)
            idx = (y * WIDTH + x) * 2
            framebuffer[idx] = rgb565 & 0xFF
            framebuffer[idx + 1] = (rgb565 >> 8) & 0xFF

    return bytes(framebuffer)

def get_temps():
    try:
        temps = psutil.sensors_temperatures()
        cpu = round(temps['coretemp'][0].current, 1) if 'coretemp' in temps else 45.0
        gpu = round(temps['nvme'][0].current, 1) if 'nvme' in temps else 38.0
        return cpu, gpu
    except:
        return 45.0, 38.0

def get_cpu_freq():
    try:
        freq = psutil.cpu_freq()
        return round(freq.current / 1000, 2) if freq else 3.0
    except:
        return 3.0

def main():
    print("="*70)
    print("Test Rendered Display - Mimicking test_framebuffer.py exactly")
    print("="*70)
    print()

    device = LM360()
    if not device.connect():
        print("Failed to connect!")
        sys.exit(1)

    print("✓ Connected\n")

    try:
        # Use EXACT same header as test_framebuffer.py
        # (we know this works!)
        header = bytes([0xaa, 0x08, 0x00, 0x00, 0x01, 0x00, 0x58, 0x02, 0x00, 0x2c, 0x01, 0xbc, 0x11])

        print("Rendering and sending frames...")
        print("Press Ctrl+C to stop\n")

        frame_count = 0
        while True:
            cpu_temp, gpu_temp = get_temps()
            cpu_freq = get_cpu_freq()

            # Render frame
            framebuffer = render_simple(cpu_temp, gpu_temp, cpu_freq)

            # Send EXACTLY like test_framebuffer.py
            device.write(header)
            device.write(framebuffer)

            frame_count += 1
            print(f"Frame {frame_count:4d} | CPU: {cpu_temp:5.1f}°C | GPU: {gpu_temp:5.1f}°C | Freq: {cpu_freq:.2f}GHz", end='\r')

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
