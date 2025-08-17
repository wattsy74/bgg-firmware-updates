# gamepad.py v4.0.0 - Enhanced with X-Input Support
__version__ = "4.0.0"

def get_version():
    return __version__

import usb_hid
import json

class CustomGamepad:
    def __init__(self):
        # Load controller mode from config
        self.controller_mode = "hid"  # Default
        try:
            with open("/config.json", "r") as f:
                config = json.load(f)
            self.controller_mode = config.get("controller_mode", "hid")
            print(f"Gamepad initialized in {self.controller_mode} mode")
        except Exception as e:
            print(f"Could not load controller mode, using HID: {e}")
        
        # Find the HID device
        for dev in usb_hid.devices:
            if dev.usage_page == 0x01 and dev.usage == 0x05:
                self.device = dev
                break
        else:
            raise RuntimeError("Custom HID gamepad not found")
        
        # Initialize state variables
        if self.controller_mode == "xinput":
            self._init_xinput()
        else:
            self._init_hid()
    
    def _init_hid(self):
        """Initialize for original HID mode"""
        self.buttons = 0
        self.hat = 0x0F
        self.z_axis = 0
        
        # Button mapping for guitar controller
        self.BUTTON_MAP = {
            1: "GREEN_FRET",    # Button 1
            2: "RED_FRET",      # Button 2
            3: "YELLOW_FRET",   # Button 3
            4: "BLUE_FRET",     # Button 4
            5: "ORANGE_FRET",   # Button 5
            6: "STRUM_UP",      # Button 6
            7: "STRUM_DOWN",    # Button 7
            8: "SELECT",        # Button 8
            9: "START",         # Button 9
            10: "TILT",         # Button 10
            11: "GUIDE"         # Button 11
        }
    
    def _init_xinput(self):
        """Initialize for Xbox controller mode"""
        self.buttons = 0
        self.left_trigger = 0
        self.right_trigger = 0
        self.left_stick_x = 0
        self.left_stick_y = 0
        self.right_stick_x = 0
        self.right_stick_y = 0
        
        # Xbox button mapping for guitar controller
        # Map guitar buttons to Xbox controller equivalents
        self.XBOX_BUTTON_MAP = {
            1: 0,   # GREEN_FRET -> A button (bit 0)
            2: 1,   # RED_FRET -> B button (bit 1)
            3: 3,   # YELLOW_FRET -> Y button (bit 3)
            4: 2,   # BLUE_FRET -> X button (bit 2)
            5: 4,   # ORANGE_FRET -> Left Bumper (bit 4)
            6: 5,   # STRUM_UP -> Right Bumper (bit 5)
            7: 5,   # STRUM_DOWN -> Right Bumper (bit 5) - same as strum up
            8: 6,   # SELECT -> Back button (bit 6)
            9: 7,   # START -> Start button (bit 7)
            10: 8,  # TILT -> Left Stick (bit 8)
            11: 9   # GUIDE -> Right Stick (bit 9) - Note: Xbox Guide is not in standard HID
        }

    def press(self, n):
        """Press a button (n = 1-11)"""
        if self.controller_mode == "xinput":
            if n in self.XBOX_BUTTON_MAP:
                xbox_button = self.XBOX_BUTTON_MAP[n]
                self.buttons |= (1 << xbox_button)
        else:
            self.buttons |= (1 << (n - 1))
        self.send()

    def release(self, n):
        """Release a button (n = 1-11)"""
        if self.controller_mode == "xinput":
            if n in self.XBOX_BUTTON_MAP:
                xbox_button = self.XBOX_BUTTON_MAP[n]
                self.buttons &= ~(1 << xbox_button)
        else:
            self.buttons &= ~(1 << (n - 1))
        self.send()

    def set_hat(self, d):
        """Set hat switch direction (HID mode) or convert to left stick (Xbox mode)"""
        if self.controller_mode == "xinput":
            # Convert hat directions to analog stick values
            # Xbox uses -32768 to 32767 range
            if d == 0:      # Up
                self.left_stick_x = 0
                self.left_stick_y = 32767
            elif d == 1:    # Up-Right
                self.left_stick_x = 23170
                self.left_stick_y = 23170
            elif d == 2:    # Right
                self.left_stick_x = 32767
                self.left_stick_y = 0
            elif d == 3:    # Down-Right
                self.left_stick_x = 23170
                self.left_stick_y = -23170
            elif d == 4:    # Down
                self.left_stick_x = 0
                self.left_stick_y = -32767
            elif d == 5:    # Down-Left
                self.left_stick_x = -23170
                self.left_stick_y = -23170
            elif d == 6:    # Left
                self.left_stick_x = -32767
                self.left_stick_y = 0
            elif d == 7:    # Up-Left
                self.left_stick_x = -23170
                self.left_stick_y = 23170
            else:           # Center/None
                self.left_stick_x = 0
                self.left_stick_y = 0
        else:
            self.hat = d & 0x0F
        self.send()

    def set_whammy(self, v):
        """Set whammy bar value (0-255)"""
        if self.controller_mode == "xinput":
            # Map whammy to right trigger (0-255)
            self.right_trigger = max(0, min(255, v))
        else:
            self.z_axis = max(0, min(255, v))
        self.send()
    
    def set_analog_stick(self, stick, x, y):
        """Set analog stick values for Xbox mode (stick = 'left' or 'right', x/y = -32768 to 32767)"""
        if self.controller_mode == "xinput":
            if stick == 'left':
                self.left_stick_x = max(-32768, min(32767, x))
                self.left_stick_y = max(-32768, min(32767, y))
            elif stick == 'right':
                self.right_stick_x = max(-32768, min(32767, x))
                self.right_stick_y = max(-32768, min(32767, y))
            self.send()

    def send(self):
        """Send the current gamepad state"""
        try:
            if self.controller_mode == "xinput":
                self._send_xinput()
            else:
                self._send_hid()
        except OSError:
            pass  # Ignore send errors (device may not be ready)

    def _send_hid(self):
        """Send HID gamepad report (original format)"""
        report = bytearray([
            self.buttons & 0xFF,                    # Low byte of buttons
            (self.buttons >> 8) & 0x07,            # High 3 bits of buttons
            (self.hat & 0x0F) | 0xF0,              # Hat switch + padding
            self.z_axis                             # Whammy/Z-axis
        ])
        self.device.send_report(report)

    def _send_xinput(self):
        """Send Xbox controller report (X-Input format)"""
        # Xbox 360 controller report format:
        # Bytes 0-1: Buttons (16 bits)
        # Byte 2: Left trigger (0-255)
        # Byte 3: Right trigger (0-255)
        # Bytes 4-5: Left stick X (-32768 to 32767, little endian)
        # Bytes 6-7: Left stick Y (-32768 to 32767, little endian)
        # Bytes 8-9: Right stick X (-32768 to 32767, little endian)
        # Bytes 10-11: Right stick Y (-32768 to 32767, little endian)
        
        report = bytearray(12)
        
        # Buttons (16 bits, little endian)
        report[0] = self.buttons & 0xFF
        report[1] = (self.buttons >> 8) & 0xFF
        
        # Triggers
        report[2] = self.left_trigger
        report[3] = self.right_trigger
        
        # Left stick (little endian 16-bit signed)
        report[4] = self.left_stick_x & 0xFF
        report[5] = (self.left_stick_x >> 8) & 0xFF
        report[6] = self.left_stick_y & 0xFF
        report[7] = (self.left_stick_y >> 8) & 0xFF
        
        # Right stick (little endian 16-bit signed)
        report[8] = self.right_stick_x & 0xFF
        report[9] = (self.right_stick_x >> 8) & 0xFF
        report[10] = self.right_stick_y & 0xFF
        report[11] = (self.right_stick_y >> 8) & 0xFF
        
        self.device.send_report(report)

    def get_mode(self):
        """Return the current controller mode"""
        return self.controller_mode
    
    def print_status(self):
        """Print current gamepad status for debugging"""
        if self.controller_mode == "xinput":
            print(f"Xbox Mode - Buttons: {self.buttons:016b}, LT: {self.left_trigger}, RT: {self.right_trigger}")
            print(f"Left Stick: ({self.left_stick_x}, {self.left_stick_y}), Right Stick: ({self.right_stick_x}, {self.right_stick_y})")
        else:
            print(f"HID Mode - Buttons: {self.buttons:011b}, Hat: {self.hat}, Z: {self.z_axis}")
