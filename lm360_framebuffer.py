#!/usr/bin/env python3
"""
LM360 Frame Buffer Driver
Renders temperature display and sends as RGB565 frames
"""
import usb.core
import usb.util
import sys
import time
import psutil
from PIL import Image, ImageDraw, ImageFont
import struct

VENDOR_ID = 0x3633
PRODUCT_ID = 0x0026
EP_OUT = 0x01

# Display specs (from 153600 bytes = 320x240x2)
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

    def send_init(self):
        """Send init/query command"""
        self.write(bytes([0xaa, 0x01, 0x00, 0x09, 0x29, 0x91]))

    def send_frame(self, image_data, cpu_temp=0, gpu_temp=0):
        """
        Send frame header + pixel data
        image_data: RGB565 format, 153600 bytes
        """
        # Encode temps for header
        cpu_enc = int(cpu_temp * 10)
        gpu_enc = int(gpu_temp * 10)
        cpu_low = cpu_enc & 0xFF
        cpu_high = (cpu_enc >> 8) & 0xFF
        gpu_low = gpu_enc & 0xFF
        gpu_high = (gpu_enc >> 8) & 0xFF

        # Frame header (aa 08 packet)
        header = bytes([
            0xaa, 0x08, 0x00, 0x00, 0x01, 0x00,
            cpu_low, cpu_high, 0x00,
            gpu_low, gpu_high,
            0xbc, 0x11
        ])

        # Send header
        self.write(header)

        # Send frame data (153600 bytes)
        self.write(image_data)

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
        return (100, 200, 255)  # Cool blue
    elif temp < 60:
        return (100, 255, 100)  # Green (good)
    elif temp < 75:
        return (255, 200, 50)   # Yellow (warm)
    elif temp < 85:
        return (255, 140, 0)    # Orange (hot)
    else:
        return (255, 50, 50)    # Red (critical)

def render_temperature_display(cpu_temp, gpu_temp, cpu_freq):
    """Render temperature display as RGB565 frame buffer"""
    # Create image with dark background
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(10, 10, 15))
    draw = ImageDraw.Draw(img)

    # Try to load fonts
    try:
        font_huge = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 72)
        font_large = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 28)
        font_medium = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 16)
    except:
        font_huge = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Get temperature colors
    cpu_color = get_temp_color(cpu_temp)
    gpu_color = get_temp_color(gpu_temp)

    # Draw vertical separator line
    draw.line([(WIDTH//2, 50), (WIDTH//2, HEIGHT-10)], fill=(40, 40, 50), width=2)

    # CPU SECTION (Left)
    cpu_text = f"{cpu_temp:.0f}"
    # Center the temperature text
    bbox = draw.textbbox((0, 0), cpu_text, font=font_huge)
    text_width = bbox[2] - bbox[0]
    cpu_x = (WIDTH//4) - (text_width//2)
    draw.text((cpu_x, 70), cpu_text, fill=cpu_color, font=font_huge)

    # Draw °C symbol
    draw.text((WIDTH//4 - 15, 150), "°C", fill=(150, 150, 160), font=font_large)

    # Draw label
    label_bbox = draw.textbbox((0, 0), "CPU", font=font_medium)
    label_width = label_bbox[2] - label_bbox[0]
    draw.text((WIDTH//4 - label_width//2, 195), "CPU", fill=(120, 120, 140), font=font_medium)

    # GPU/SENSOR SECTION (Right)
    gpu_text = f"{gpu_temp:.0f}"
    bbox = draw.textbbox((0, 0), gpu_text, font=font_huge)
    text_width = bbox[2] - bbox[0]
    gpu_x = (3*WIDTH//4) - (text_width//2)
    draw.text((gpu_x, 70), gpu_text, fill=gpu_color, font=font_huge)

    # Draw °C symbol
    draw.text((3*WIDTH//4 - 15, 150), "°C", fill=(150, 150, 160), font=font_large)

    # Draw label
    label_bbox = draw.textbbox((0, 0), "SENSOR", font=font_medium)
    label_width = label_bbox[2] - label_bbox[0]
    draw.text((3*WIDTH//4 - label_width//2, 195), "SENSOR", fill=(120, 120, 140), font=font_medium)

    # Draw CPU frequency at top (centered)
    freq_text = f"{cpu_freq:.2f} GHz"
    bbox = draw.textbbox((0, 0), freq_text, font=font_medium)
    text_width = bbox[2] - bbox[0]
    draw.text((WIDTH//2 - text_width//2, 15), freq_text, fill=(180, 180, 200), font=font_medium)

    # Convert to RGB565
    pixels = img.load()
    framebuffer = bytearray(WIDTH * HEIGHT * 2)

    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b = pixels[x, y]
            rgb565 = rgb888_to_rgb565(r, g, b)
            # Little-endian
            idx = (y * WIDTH + x) * 2
            framebuffer[idx] = rgb565 & 0xFF
            framebuffer[idx + 1] = (rgb565 >> 8) & 0xFF

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
    print("LM360 Frame Buffer Driver - Dynamic Temperature Display")
    print("="*70)
    print()

    device = LM360()
    if not device.connect():
        print("✗ Failed to connect!")
        sys.exit(1)

    print("✓ Connected to LM360")
    print("Initializing...")

    try:
        # Send init
        device.send_init()
        time.sleep(0.5)

        print("✓ Initialized")
        print("\nRendering and sending temperature frames...")
        print("This will update every 2 seconds")
        print("Press Ctrl+C to stop\n")
        print("="*70)

        frame_count = 0
        while True:
            cpu_temp, gpu_temp = get_temps()
            cpu_freq = get_cpu_freq()

            # Render frame
            framebuffer = render_temperature_display(cpu_temp, gpu_temp, cpu_freq)

            # Send frame
            device.send_frame(framebuffer, cpu_temp, gpu_temp)

            frame_count += 1
            print(f"Frame {frame_count:4d} | CPU: {cpu_temp:5.1f}°C | Sensor: {gpu_temp:5.1f}°C | Freq: {cpu_freq:.2f}GHz", end='\r')

            time.sleep(2)  # Update every 2 seconds

    except KeyboardInterrupt:
        print(f"\n\nStopped after {frame_count} frames")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        device.disconnect()
        print("✓ Disconnected")

if __name__ == "__main__":
    main()
