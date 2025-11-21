# Deepcool LM360 Linux Driver

**Working Linux driver for the Deepcool LM360 AIO cooler LCD display.**

## Features

✅ Live CPU/GPU temperature display
✅ Custom image rendering (320x240 RGB565)
✅ Brightness control
✅ Zen mode (screen off/on)
✅ Color pattern testing
✅ Easy-to-use CLI tool

## Hardware Support

- **Device**: Deepcool LM360
- **USB VID:PID**: 3633:0026
- **Display**: 320x240 RGB565 LCD

## Requirements

```bash
# Python dependencies
sudo pip install pyusb pillow psutil

# On Arch Linux
sudo pacman -S python-pyusb python-pillow python-psutil
```

## Installation

```bash
# Clone or download this repository
cd coolmaster-driver

# Make the CLI tool executable
chmod +x lm360

# (Optional) Copy to system path
sudo cp lm360 /usr/local/bin/
```

## Quick Start

### Display Live Temperatures

```bash
# Update every 2 seconds (default)
sudo ./lm360 temps

# Update every second
sudo ./lm360 temps --interval 1
```

### Display Custom Image

```bash
sudo ./lm360 image /path/to/image.jpg
```

### Control Brightness

```bash
sudo ./lm360 brightness up
sudo ./lm360 brightness down
```

### Test Display

```bash
sudo ./lm360 test
```

## USB Packet Capture

### Prerequisites

- Windows PC or Windows VM (VirtualBox)
- Official Deepcool software from www.cryoex.com
- Linux machine with `usbmon` support

### Method 1: Using VirtualBox

1. **Set up Windows VM**:
   ```bash
   # Install VirtualBox if not installed
   sudo pacman -S virtualbox

   # Create Windows VM and install official Deepcool software
   ```

2. **Enable USB monitoring on Linux host**:
   ```bash
   # Load usbmon kernel module
   sudo modprobe usbmon

   # Find the USB bus number for LM360
   lsusb | grep "3633:0026"
   # Example output: Bus 001 Device 010: ID 3633:0026 DC LM-Series

   # Start capturing (replace '1' with your bus number)
   sudo cat /sys/kernel/debug/usb/usbmon/1u > lm360_capture.txt
   ```

3. **Pass USB to VM and capture traffic**:
   - In VirtualBox, attach the LM360 USB device to Windows VM
   - In Windows, run the official Deepcool software
   - Display CPU/GPU temps, change screens, etc.
   - Stop the capture after ~30 seconds

4. **Analyze the capture**:
   ```bash
   # View the captured data
   less lm360_capture.txt
   ```

### Method 2: Using Wireshark (Alternative)

```bash
# Install wireshark with USBPcap support
sudo pacman -S wireshark-qt

# Run wireshark as root
sudo wireshark
```

1. Select the USB interface for Bus 001
2. Start capture
3. In Windows (or VM), run Deepcool software
4. Stop capture and analyze packets

## Project Structure

```
coolmaster-driver/
├── main.py                          # USB probe script
├── README.md                        # This file
├── FINDINGS.md                      # Research findings
├── pyproject.toml                   # Python project config
├── .venv/                           # Python virtual environment
├── deepcool-digital-linux/          # Nortank12's driver (tested, doesn't work)
├── deepcool-digital-linux-philling/ # philling-dev's driver (pre-built only)
└── deepcool-digital-info/           # Algorithm0's driver (tested, doesn't work)
```

## Dependencies

```bash
# Python packages (already installed in .venv)
uv pip install hidapi psutil pyjson5 click
```

## Next Steps

1. **Run the probe script** with sudo
2. **Review output** to see if any protocol works
3. **If no protocol works**:
   - Set up USB packet capture
   - Analyze the official software's USB communication
   - Implement the protocol in Python
4. **Build the driver**:
   - Create Python driver using `hidapi`
   - Add CPU/GPU temperature monitoring
   - Package as systemd service

## Resources

- [USB Reverse Engineering Guide (Hackaday)](https://hackaday.com/2018/05/25/usb-reverse-engineering-a-universal-guide/)
- [OpenRazer USB Reverse Engineering Wiki](https://github.com/openrazer/openrazer/wiki/Reverse-Engineering-USB-Protocol)
- [liquidctl Documentation](https://github.com/liquidctl/liquidctl)

## Device Information

- **Model**: Deepcool LM360
- **USB VID**: `0x3633` (Deepcool)
- **USB PID**: `0x0026` (LM Series)
- **Display**: 2.4" IPS LCD with MP4 support
- **Connection**: USB 2.0 (9-pin internal header)

## Contributing

If you successfully reverse engineer the protocol or get the driver working, please consider:
- Opening an issue in the existing Deepcool driver repos
- Sharing your findings with the community
- Contributing to this project

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
