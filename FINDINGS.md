# Deepcool LM360 Linux Driver Investigation

## Device Information
- **Model**: Deepcool LM360
- **USB Vendor ID**: `0x3633` (13875 decimal)
- **USB Product ID**: `0x0026` (38 decimal)
- **Display**: 2.4" IPS LCD screen with MP4 support
- **Detection**: Visible in `lsusb` as "DC LM-Series"

## Existing Driver Analysis

### Tested Drivers
1. **Nortank12/deepcool-digital-linux** (Rust) ❌
   - Status: Does NOT detect LM360
   - Reason: Product ID 0x0026 not in supported device list
   - Supported PIDs: 1-4 (AK), 5 (CH560), 6 (LS), 7 (MORPHEUS), 8 (AG), 9 (MYSTIQUE), 10 (LD), etc.
   - LM360 (PID 38) falls outside all defined ranges

2. **philling-dev/deepcool-digital-linux** ⏭️
   - Status: Pre-built .deb only, no source code
   - Based on same architecture as Nortank12's driver
   - Skipped testing

3. **Algorithm0/deepcool-digital-info** (Python) ❌
   - Status: Does NOT support LM360
   - Supported PIDs: 0x0001-0x0008 only
   - LM360's 0x0026 not recognized

### Why Existing Drivers Don't Work

All existing drivers were designed for **7-segment numerical displays**, not LCD screens:

#### Protocol Used by Existing Drivers

**Simple Mode** (CH510, etc.):
```python
# ASCII string format
data = "_HLXDATA(usage,temp,0,0,C)"
```

**Complex Mode** (AK/AG series):
```python
# 64-byte binary array
[16, mode, bar, digit1, digit2, digit3, ...]
```
Where:
- Byte 0: Always `16`
- Byte 1: Mode (`76`=CPU usage, `19`=temp, `170`=init)
- Byte 2: Bar graph value
- Bytes 3-6: Individual digits (0-9)

This protocol only works for displaying numbers, not images or complex graphics.

#### LM360's LCD Display Requirements

The LM360 has a **2.4" IPS LCD screen** that:
- Displays full color images
- Supports MP4 video playback (per specs)
- Needs framebuffer/image data protocol
- Requires completely different USB communication

**Conclusion**: The LM360 uses a fundamentally different protocol than the simple 7-segment displays.

## Reverse Engineering Plan

Since no existing driver works, we need to reverse engineer the USB protocol:

### Method 1: USB Packet Capture (Recommended)

#### Requirements
- Windows PC or Windows VM
- Official Deepcool software from www.cryoex.com
- USB packet capture tools

#### Tools Needed
- **usbmon** (Linux kernel USB monitoring)
- **Wireshark** with USBPcap
- **VirtualBox** (if using Windows in VM)

#### Process
1. Set up VirtualBox with Windows
2. Pass LM360 USB device to Windows VM
3. Run `usbmon` on Linux host to capture traffic:
   ```bash
   sudo modprobe usbmon
   sudo cat /sys/kernel/debug/usb/usbmon/1u > lm360_capture.txt
   ```
4. In Windows VM:
   - Install official Deepcool software
   - Display CPU/GPU temps on LCD
   - Perform various actions (change display, etc.)
5. Analyze captured packets to understand:
   - Initialization sequence
   - Image/text rendering commands
   - Temperature data format
   - Display update protocol

### Method 2: Direct USB Analysis

If Windows is unavailable, we can probe the device directly:

```python
import hid

# List all HID devices
for device in hid.enumerate():
    if device['vendor_id'] == 0x3633:
        print(f"Product ID: 0x{device['product_id']:04x}")
        print(f"Product String: {device['product_string']}")
        print(f"Manufacturer: {device['manufacturer_string']}")

# Try opening LM360
h = hid.device()
h.open(0x3633, 0x0026)
h.set_nonblocking(1)

# Experiment with different packet formats
# Start with patterns similar to existing drivers
# Document what works and what doesn't
```

## Next Actions

### Immediate
- [ ] Decide on reverse engineering approach
- [ ] Set up packet capture environment
- [ ] Analyze USB protocol

### After Protocol Analysis
- [ ] Build Python driver using `hidapi`
- [ ] Implement temperature display
- [ ] Add GPU temperature support
- [ ] Package as systemd service
- [ ] Consider contributing back to community

## References
- [USB Reverse Engineering Guide (Hackaday)](https://hackaday.com/2018/05/25/usb-reverse-engineering-a-universal-guide/)
- [OpenRazer USB Reverse Engineering Wiki](https://github.com/openrazer/openrazer/wiki/Reverse-Engineering-USB-Protocol)
- Existing driver repos:
  - https://github.com/Nortank12/deepcool-digital-linux
  - https://github.com/Algorithm0/deepcool-digital-info
