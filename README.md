# Deepcool LM Series LCD Driver for Linux

A comprehensive Linux driver for Deepcool LM series AIO coolers with LCD displays (320x240). Features a polished system monitoring interface with real-time CPU/GPU temperature display, CPU usage tracking, and custom image support.

![LM360 Display](https://img.shields.io/badge/Resolution-320x240-blue) ![License](https://img.shields.io/badge/License-MIT-green)

> **Note**: This driver is designed for Deepcool LM series coolers. Currently tested and confirmed working on **LM360** only. Other LM series models (LM240, LM280, etc.) may work but have not been tested. Contributions and testing reports are welcome!

## Features

- 🎨 **Polished System Monitor** - Beautiful dual-panel interface with CPU and GPU stats
- 🌡️ **Temperature Monitoring** - Real-time CPU and GPU temperature display with color gradients
- 📊 **Usage Tracking** - CPU usage percentage with animated progress bars
- ⚡ **CPU Frequency** - Current CPU frequency display
- 🖼️ **Custom Images** - Display any image on the LCD (auto-resized to 320x240)
- 🔆 **Brightness Control** - Adjust display brightness
- 🔄 **Persistent State** - Service maintains display mode (monitor/image/color)
- 🎯 **Clean UI** - Modern design with rounded borders, icons, and smooth progress bars
- 🔌 **IPC Communication** - CLI communicates with running service without conflicts

## Display Preview

The monitor interface features:
- **CPU Section** (Top): Temperature, usage %, frequency, and usage progress bar
- **GPU Section** (Bottom): Temperature with visual temperature gradient
- **Color-coded Temps**: Cool blue (< 40°C) → Green (< 60°C) → Yellow (< 75°C) → Orange (< 85°C) → Red (85°C+)
- **Rounded Containers**: Modern card-based layout with 8px rounded corners
- **Icons**: Visual indicators (⚙ for CPU, ▣ for GPU)

## Installation

### Arch Linux (AUR)

```bash
yay -S deepcool-lm
```

The service will automatically start if your device is connected!

### Other Distributions

```bash
curl -fsSL https://raw.githubusercontent.com/daedlock/deepcool-lm/main/install.sh | sudo bash
```

Or download and run manually:
```bash
curl -O https://raw.githubusercontent.com/daedlock/deepcool-lm/main/install.sh
chmod +x install.sh
sudo ./install.sh
```

## Post-Installation Setup

### Configure Temperature Sensors

The driver requires `lm_sensors` for temperature monitoring:

```bash
sudo sensors-detect  # Answer YES to save configuration
sudo systemctl enable --now lm_sensors
```

### Install Dependencies (Non-AUR)

If installing via `install.sh`, ensure these are installed first:

```bash
# Arch Linux
sudo pacman -S lm_sensors python-pyusb python-psutil python-pillow

# Ubuntu/Debian
sudo apt install lm-sensors python3-usb python3-psutil python3-pil

# Fedora
sudo dnf install lm_sensors python3-pyusb python3-psutil python3-pillow
```

## Usage

### Systemd Service (Recommended)

The service runs the system monitor automatically in the background:

```bash
# Start the service
sudo systemctl start deepcool-lm

# Enable on boot
sudo systemctl enable deepcool-lm

# Check status
sudo systemctl status deepcool-lm

# View logs
sudo journalctl -u deepcool-lm -f

# Stop the service
sudo systemctl stop deepcool-lm
```

### CLI Commands

The `deepcool-lm` command provides various functions. When the service is running, commands communicate via IPC without conflicts:

#### System Monitor
```bash
# Start monitoring (when service is not running)
sudo deepcool-lm monitor

# Switch back to monitoring mode (when service is running)
sudo deepcool-lm monitor
```

#### Display Custom Image
```bash
# Display any image (will be resized to 320x240)
# Image persists until you switch modes
sudo deepcool-lm image /path/to/photo.jpg
sudo deepcool-lm image ~/wallpaper.png
```

#### Display Solid Color
```bash
# Black screen
sudo deepcool-lm solid --color 0 0 0

# Red screen
sudo deepcool-lm solid --color 255 0 0

# Custom RGB color
sudo deepcool-lm solid --color 100 150 200
```

#### Brightness Control
```bash
# Increase brightness
sudo deepcool-lm brightness up

# Decrease brightness
sudo deepcool-lm brightness down
```

#### Show Help
```bash
deepcool-lm --help
```

### Usage Examples

**Typical workflow:**
```bash
# Service is running showing CPU/GPU monitoring

# Display a custom image
sudo deepcool-lm image ~/my-image.jpg
# Image stays on screen

# Switch back to monitoring
sudo deepcool-lm monitor
# Back to CPU/GPU stats

# Adjust brightness while monitoring
sudo deepcool-lm brightness up
```

## Uninstallation

```bash
sudo ./uninstall.sh
```

This will:
- Stop and disable the systemd service
- Remove the service file
- Remove the CLI tool
- Clean up socket files

## Technical Details

### Compatibility
- **Tested Models**: Deepcool LM360
- **Likely Compatible**: Other LM series models (LM240, LM280, etc.) with USB VID:PID `3633:0026`
- **Status**: Untested on other LM series models - please report compatibility!

### Device Information
- **Vendor ID**: `0x3633`
- **Product ID**: `0x0026`
- **Display**: 320x240 RGB565
- **Protocol**: USB Bulk Transfer
- **Endpoint**: `0x01` (OUT)

### Frame Format
- **Header**: 13 bytes (`aa 08 00 00 01 00 58 02 00 2c 01 bc 11`)
- **Framebuffer**: 153,600 bytes (320 × 240 × 2)
- **Pixel Format**: RGB565 little-endian

### IPC Communication
- **Socket**: `/var/run/deepcool-lm.sock`
- **Protocol**: Unix domain socket with JSON commands
- **Supported actions**: monitor, image, solid, brightness_up, brightness_down

### Temperature Sources
- **CPU**: `coretemp` sensor (first core)
- **GPU**: `nvme` sensor (if available)

The driver uses `psutil.sensors_temperatures()` to read system temperatures. You can check available sensors with:

```bash
sensors
```

## Troubleshooting

### Device Not Found
```bash
# Check if device is detected
lsusb | grep 3633

# Should show: Bus XXX Device XXX: ID 3633:0026
```

### Permission Denied
Make sure you're running with `sudo`:
```bash
sudo deepcool-lm monitor
```

### Service Won't Start
Check logs for errors:
```bash
sudo journalctl -u deepcool-lm -n 50
```

### Screen Goes Black When CLI Stops
This is expected behavior when running CLI directly. Use the systemd service for persistent display:
```bash
sudo systemctl start deepcool-lm
sudo systemctl enable deepcool-lm  # Start on boot
```

### Missing Temperature Sensors
If temps show as 0°C, check available sensors:
```bash
sensors
```

You may need to load kernel modules:
```bash
sudo modprobe coretemp  # For Intel CPUs
```

## Development

### Project Structure
```
coolmaster-driver/
├── deepcool-lm              # Main CLI tool (standalone executable)
├── deepcool-lm.service      # Systemd service file
├── install.sh               # Installation script
├── uninstall.sh             # Uninstallation script
├── PKGBUILD                 # Arch Linux package build
├── deepcool-lm-driver.install # AUR install hooks
└── README.md                # This file
```

### Building Custom Layouts

The `render_monitor_display()` function in `deepcool-lm` can be customized to create different layouts. Key functions:

- `draw_rounded_rect()` - Draw rounded rectangles
- `get_temp_color()` - Get color based on temperature
- `rgb_to_framebuffer()` - Convert PIL image to RGB565

Example of adding a custom element:
```python
# In render_monitor_display()
draw.text((160, 120), "Custom Text", fill=(255, 255, 255), font=fonts['small'])
```

## Credits

This driver was developed through reverse engineering the USB protocol used by the official Windows software.

## License

MIT License - Feel free to use and modify

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Changelog

### v1.0.0
- Initial release
- System monitoring with CPU/GPU temperature
- Custom image display with persistent state
- Solid color display
- Brightness control
- IPC communication for conflict-free CLI usage
- Systemd service integration
- Polished UI with rounded borders and progress bars
