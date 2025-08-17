# boot.py v4.0.0 - Smart Acknowledgment System + Enhanced Device Communication + X-Input Support
__version__ = "4.0.0"

def get_version():
    return __version__

import board
import digitalio
import storage
import supervisor
import usb_cdc
import usb_hid
import usb_midi
import microcontroller
import json
import os
import time

# Use last 2 bytes of UID for unique PID
uid_bytes = microcontroller.cpu.uid
unique_pid = int.from_bytes(uid_bytes[-2:], "big")

# Load controller mode from config.json
controller_mode = "hid"  # Default fallback
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    controller_mode = config.get('controller_mode', 'hid')
    print(f"Controller mode: {controller_mode}")
except Exception as e:
    print(f"Could not load controller mode from config, using default HID: {e}")

# Xbox 360 Controller compatible HID descriptor
XBOX_GAMEPAD_DESCRIPTOR = bytes((
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x05,        # Usage (Gamepad)
    0xA1, 0x01,        # Collection (Application)
    
    # Digital buttons (10 buttons: A, B, X, Y, LB, RB, Back, Start, LS, RS)
    0x05, 0x09,        # Usage Page (Button)
    0x19, 0x01,        # Usage Minimum (Button 1)
    0x29, 0x0A,        # Usage Maximum (Button 10)
    0x15, 0x00,        # Logical Minimum (0)
    0x25, 0x01,        # Logical Maximum (1)
    0x95, 0x0A,        # Report Count (10)
    0x75, 0x01,        # Report Size (1 bit)
    0x81, 0x02,        # Input (Data, Variable, Absolute)
    
    # Padding (6 bits)
    0x95, 0x06,        # Report Count (6)
    0x75, 0x01,        # Report Size (1 bit)
    0x81, 0x03,        # Input (Constant, Variable, Absolute)
    
    # Left and Right triggers (Z and RZ)
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x32,        # Usage (Z) - Left Trigger
    0x09, 0x35,        # Usage (RZ) - Right Trigger
    0x15, 0x00,        # Logical Minimum (0)
    0x26, 0xFF, 0x00,  # Logical Maximum (255)
    0x95, 0x02,        # Report Count (2)
    0x75, 0x08,        # Report Size (8 bits)
    0x81, 0x02,        # Input (Data, Variable, Absolute)
    
    # Left stick X and Y
    0x09, 0x30,        # Usage (X)
    0x09, 0x31,        # Usage (Y)
    0x16, 0x00, 0x80,  # Logical Minimum (-32768)
    0x26, 0xFF, 0x7F,  # Logical Maximum (32767)
    0x95, 0x02,        # Report Count (2)
    0x75, 0x10,        # Report Size (16 bits)
    0x81, 0x02,        # Input (Data, Variable, Absolute)
    
    # Right stick X and Y
    0x09, 0x33,        # Usage (RX)
    0x09, 0x34,        # Usage (RY)
    0x16, 0x00, 0x80,  # Logical Minimum (-32768)
    0x26, 0xFF, 0x7F,  # Logical Maximum (32767)
    0x95, 0x02,        # Report Count (2)
    0x75, 0x10,        # Report Size (16 bits)
    0x81, 0x02,        # Input (Data, Variable, Absolute)
    
    0xC0               # End Collection
))

# Original Custom HID Gamepad Descriptor (Report ID 5)
CUSTOM_GAMEPAD_DESCRIPTOR = bytes((
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x05,        # Usage (Gamepad)
    0xA1, 0x01,        # Collection (Application)
    0x85, 0x05,        #   Report ID (5)

    # Buttons (11)
    0x05, 0x09,        #   Usage Page (Button)
    0x19, 0x01,        #   Usage Minimum (Button 1)
    0x29, 0x0B,        #   Usage Maximum (Button 11)
    0x15, 0x00,
    0x25, 0x01,
    0x95, 0x0B,
    0x75, 0x01,
    0x81, 0x02,

    # Padding (5 bits)
    0x95, 0x05,
    0x75, 0x01,
    0x81, 0x03,

    # Hat switch (4 bits)
    0x05, 0x01,
    0x09, 0x39,
    0x15, 0x00,
    0x25, 0x07,
    0x35, 0x00,
    0x46, 0x3B, 0x01,
    0x65, 0x14,
    0x75, 0x04,
    0x95, 0x01,
    0x81, 0x42,

    # Padding (4 bits)
    0x75, 0x04,
    0x95, 0x01,
    0x81, 0x03,

    # Z axis (whammy)
    0x09, 0x32,
    0x15, 0x00,
    0x26, 0xFF, 0x00,
    0x75, 0x08,
    0x95, 0x01,
    0x81, 0x02,

    0xC0
))

# Set USB identification based on controller mode
if controller_mode == "xinput":
    print("Configuring as Xbox 360 Controller (X-Input)")
    supervisor.set_usb_identification(
        manufacturer="Microsoft",
        product="Controller",
        vid=0x045E,              # Microsoft Vendor ID
        pid=0x028E               # Xbox 360 Controller PID
    )
    gamepad_descriptor = XBOX_GAMEPAD_DESCRIPTOR
    report_id = None  # Xbox controllers don't use report IDs
    report_length = 12  # Xbox format: 2 bytes buttons + 2 bytes triggers + 8 bytes analog sticks
else:
    print("Configuring as Custom HID Gamepad")
    supervisor.set_usb_identification(
        manufacturer="BumbleGum",
        product="CH-Guitar",
        vid=0x6997,
        pid=unique_pid
    )
    gamepad_descriptor = CUSTOM_GAMEPAD_DESCRIPTOR
    report_id = (5,)
    report_length = (4,)  # Original format: 4 bytes total

# Load device name from config.json
device_name = "Guitar Controller"  # Default fallback
try:
    device_name = config.get('device_name', 'Guitar Controller')
    print(f"Loaded device name from config: '{device_name}'")
except Exception as e:
    print(f"Could not load device name from config, using default: {e}")

if controller_mode == "xinput":
    usb_hid.set_interface_name("Xbox 360 Controller")
else:
    usb_hid.set_interface_name(f"BumbleGum Guitars - {device_name}")

# Enable custom HID gamepad
if controller_mode == "xinput":
    gamepad = usb_hid.Device(
        report_descriptor=gamepad_descriptor,
        usage_page=0x01,
        usage=0x05,
        report_ids=(),  # No report IDs for Xbox
        in_report_lengths=(12,),  # Xbox format
        out_report_lengths=(0,)
    )
else:
    gamepad = usb_hid.Device(
        report_descriptor=gamepad_descriptor,
        usage_page=0x01,
        usage=0x05,
        report_ids=report_id,
        in_report_lengths=report_length,
        out_report_lengths=(0,)
    )

usb_hid.enable((gamepad,))

# Disable MIDI
usb_midi.disable()

# Enable USB CDC (console + data)
usb_cdc.enable(console=True, data=True)

# Rest of the boot.py code remains the same...
# [Include all the firmware update system code from the original boot.py]

# Disable auto-reload to prevent interruptions during file operations
try:
    supervisor.runtime.autoreload = False
    print("Auto-reload disabled via supervisor.runtime.autoreload")
except (AttributeError, NameError):
    try:
        supervisor.disable_autoreload()
        print("Auto-reload disabled via supervisor.disable_autoreload()")
    except (AttributeError, NameError):
        print("Auto-reload disable not available - manual reboot control only")

# Hold GREEN_FRET (GP10) to enable USB drive (for manual debugging only)
button = digitalio.DigitalInOut(board.GP10)
button.switch_to_input(pull=digitalio.Pull.UP)

if not button.value:  # GREEN_FRET pressed - manual debugging mode
    print("GREEN_FRET pressed - USB drive enabled for manual debugging")
else:
    print("USB drive disabled for normal operation")
    storage.disable_usb_drive()

print(f"BGG Guitar Controller v{__version__} boot complete! (Mode: {controller_mode})")
