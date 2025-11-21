# USB Packet Capture Guide for LM360

## Setup Overview
We'll use your Windows 11 VM (win11) in virsh/qemu to run the official Deepcool software while capturing USB packets on the Linux host.

## Step 1: Identify USB Device Details

First, let's get the exact USB bus and device info:

```bash
lsusb | grep 3633
# Output: Bus 001 Device 010: ID 3633:0026 DC LM-Series
```

Note the bus (001) and device number (010).

Get more details:
```bash
lsusb -t | grep -A 5 LM-Series
```

## Step 2: Enable USB Monitoring on Linux Host

```bash
# Load usbmon kernel module
sudo modprobe usbmon

# Verify it's loaded
lsmod | grep usbmon

# Check available USB busses for monitoring
ls -la /sys/kernel/debug/usb/usbmon/
```

## Step 3: Attach LM360 to Windows VM

### Option A: Using virt-manager (GUI)
```bash
# Open virt-manager
virt-manager
```
1. Right-click on "win11" VM → Open
2. View → Details
3. Add Hardware → USB Host Device
4. Select: "DC LM-Series [3633:0026]"
5. Click Finish

### Option B: Using virsh (CLI)

Create a USB device XML file:
```bash
cat > /tmp/lm360-usb.xml <<EOF
<hostdev mode='subsystem' type='usb'>
  <source>
    <vendor id='0x3633'/>
    <product id='0x0026'/>
  </source>
</hostdev>
EOF

# Attach to running VM
sudo virsh attach-device win11 /tmp/lm360-usb.xml --live

# Or edit VM config permanently
sudo virsh edit win11
# Then add the <hostdev> block inside <devices>
```

## Step 4: Start USB Packet Capture

In a separate terminal on Linux host:

```bash
# Start capturing (Bus 001 = 1u)
sudo cat /sys/kernel/debug/usb/usbmon/1u > ~/lm360_capture.txt
```

**Keep this terminal running!** It will capture all USB traffic on Bus 001.

## Step 5: Use Windows Software

1. **Start Windows VM:**
   ```bash
   virsh start win11
   # Or in virt-manager, click "Play" button
   ```

2. **In Windows VM:**
   - Open Device Manager
   - Verify LM360 appears (should show as "DC LM-Series" or unknown device)
   - Download official software from: www.cryoex.com
   - Install the software
   - Open the software
   - The logo should appear on the LCD!

3. **Interact with the display:**
   - Change display modes (CPU temp, GPU temp, etc.)
   - Switch between different screens
   - Do this for 30-60 seconds

## Step 6: Stop Capture

Back on Linux host:
```bash
# Stop the capture (Ctrl+C in the terminal running cat)
# Check file size
ls -lh ~/lm360_capture.txt
```

## Step 7: Detach USB from VM

```bash
# Detach from VM
sudo virsh detach-device win11 /tmp/lm360-usb.xml --live

# Or just shut down the VM
virsh shutdown win11
```

## Step 8: Analyze the Capture

```bash
# View the captured data
less ~/lm360_capture.txt

# Or use our analysis script (we'll create this)
cd /home/end4/code/projects/coolmaster-driver
python3 analyze_capture.py ~/lm360_capture.txt
```

## Troubleshooting

### USB device not showing in Windows
- Check in Linux: `lsusb` - device should NOT appear (passed to VM)
- Try detaching and reattaching
- Restart the VM

### Capture file is empty
- Check permissions: `sudo chmod 644 ~/lm360_capture.txt`
- Make sure you're capturing the right bus (Bus 001 → 1u)
- Try capturing ALL busses: `sudo cat /sys/kernel/debug/usb/usbmon/0u > ~/lm360_capture_all.txt`

### VM can't access USB
- Check VM is running as your user or root
- Add yourself to libvirt group: `sudo usermod -a -G libvirt $USER`
- Logout and login again

## Quick Start Commands

All-in-one setup:
```bash
# Terminal 1: Start capture
sudo modprobe usbmon
sudo cat /sys/kernel/debug/usb/usbmon/1u > ~/lm360_capture.txt

# Terminal 2: Attach USB and start VM
sudo virsh attach-device win11 /tmp/lm360-usb.xml --live
# Then use Windows software for 1 minute
# Then: Ctrl+C in Terminal 1 to stop capture
sudo virsh detach-device win11 /tmp/lm360-usb.xml --live
```

## What We're Looking For

In the captured packets, we want to find:
1. **Initialization sequence** - commands sent when software starts
2. **Display mode changes** - commands when switching CPU/GPU display
3. **Temperature updates** - how temp data is formatted and sent
4. **Wake/sleep commands** - power control sequences

The capture will show:
- Direction: `o` = OUT (to device), `i` = IN (from device)
- Endpoint addresses
- Data payload in hex
- Timestamps
