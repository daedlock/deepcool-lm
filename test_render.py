#!/usr/bin/env python3
"""
Test the rendering function independently
"""
from PIL import Image, ImageDraw, ImageFont

WIDTH = 320
HEIGHT = 240

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

    # Save as PNG to verify rendering
    img.save("/tmp/test_render.png")
    print("✓ Saved rendered image to /tmp/test_render.png")

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

if __name__ == "__main__":
    print("Testing render function...")
    print("Rendering with: CPU=55°C, GPU=42°C, Freq=3.6GHz")

    fb = render_temperature_display(55.0, 42.0, 3.6)

    print(f"✓ Framebuffer size: {len(fb)} bytes (expected 153600)")

    # Check if it's not all zeros
    non_zero = sum(1 for b in fb if b != 0)
    print(f"✓ Non-zero bytes: {non_zero}/{len(fb)}")

    if non_zero > 0:
        print("✓ Framebuffer contains data")
    else:
        print("✗ WARNING: Framebuffer is all zeros!")
