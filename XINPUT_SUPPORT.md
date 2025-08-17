# X-Input Support for BumbleGum Guitar Controllers

## Overview
This document explains how to add X-Input (Xbox controller) support to your BumbleGum guitar controllers. X-Input provides better game compatibility and automatic driver support on Windows.

## What is X-Input?
- X-Input is Microsoft's input API used by Xbox controllers
- Provides automatic driver installation on Windows
- Better compatibility with modern games (especially those optimized for Xbox controllers)
- Recognized as "Xbox 360 Controller" by games and Windows

## Implementation Options

### Option 1: Configuration-Based Mode Switching (Recommended)

**Benefits:**
- Users can choose between HID and X-Input modes
- Maintains backward compatibility
- Can be changed via your Windows configurator app

**Implementation:**

1. **Add controller mode to config.json:**
```json
{
    "controller_mode": "xinput",  // or "hid"
    // ... rest of config
}
```

2. **Modified boot.py:**
   - Check `controller_mode` setting
   - Use Xbox USB IDs for X-Input mode (VID: 0x045E, PID: 0x028E)
   - Use Xbox-compatible HID descriptor
   - Keep original HID descriptor for HID mode

3. **Enhanced gamepad.py:**
   - Support both report formats
   - Map guitar buttons to Xbox button equivalents
   - Convert hat switch to analog stick for Xbox mode
   - Map whammy bar to trigger input

### Option 2: Dual-Mode Device (Advanced)

**Benefits:**
- Appears as both HID gamepad and Xbox controller
- Games can choose which interface to use

**Drawbacks:**
- More complex implementation
- Potential driver conflicts
- Higher resource usage

### Option 3: Pure X-Input Mode

**Benefits:**
- Simplest implementation
- Best game compatibility
- Automatic Windows driver support

**Drawbacks:**
- Loses custom HID functionality
- May break compatibility with some rhythm game software

## X-Input Button Mapping for Guitar Controllers

```
Guitar Button     -> Xbox Button
GREEN_FRET       -> A (Face button down)
RED_FRET         -> B (Face button right)  
YELLOW_FRET      -> Y (Face button up)
BLUE_FRET        -> X (Face button left)
ORANGE_FRET      -> Left Bumper
STRUM_UP/DOWN    -> Right Bumper
SELECT           -> Back
START            -> Start
TILT             -> Left Stick Click
D-PAD            -> Left Analog Stick
WHAMMY           -> Right Trigger
```

## Technical Details

### Xbox Controller USB IDs
- **Vendor ID:** 0x045E (Microsoft)
- **Product ID:** 0x028E (Xbox 360 Controller)
- **Product Name:** "Controller"
- **Manufacturer:** "Microsoft"

### Report Format
Xbox controllers use a 12-byte report:
- Bytes 0-1: Button states (16 bits)
- Byte 2: Left trigger (0-255)
- Byte 3: Right trigger (0-255)  
- Bytes 4-5: Left stick X (-32768 to 32767)
- Bytes 6-7: Left stick Y (-32768 to 32767)
- Bytes 8-9: Right stick X (-32768 to 32767)
- Bytes 10-11: Right stick Y (-32768 to 32767)

## Windows Configurator Integration

Your Windows app should:

1. **Detect controller mode:**
```python
controller_mode = device_config.get('controller_mode', 'hid')
if controller_mode == 'xinput':
    # Show Xbox controller layout in UI
    # Use Xbox button names
else:
    # Show custom gamepad layout
```

2. **Provide mode switching:**
```python
def set_controller_mode(mode):
    config['controller_mode'] = mode
    save_config(config)
    # Prompt user to reconnect device
```

3. **Update UI labels:**
   - X-Input mode: Use Xbox button names (A, B, X, Y, LB, RB, etc.)
   - HID mode: Use custom names (Green Fret, Red Fret, etc.)

## Testing X-Input Implementation

1. **Windows Game Controller Panel:**
   - Should show as "Xbox 360 Controller"
   - All buttons and analog inputs should work

2. **Steam Controller Test:**
   - Steam should automatically recognize as Xbox controller
   - No additional configuration needed

3. **Game Compatibility:**
   - Test with games that prefer Xbox controllers
   - Verify automatic button mapping works

## Migration Path

1. **Phase 1:** Add configuration option (default to HID for compatibility)
2. **Phase 2:** Update Windows app to support mode switching
3. **Phase 3:** Test with community feedback
4. **Phase 4:** Consider making X-Input default for new devices

## Potential Issues and Solutions

### Issue: Driver Conflicts
**Solution:** Use unique USB IDs or provide clear mode switching

### Issue: Game Detection
**Solution:** Ensure exact Xbox controller descriptor compliance

### Issue: Rhythm Game Compatibility  
**Solution:** Keep HID mode available as fallback

### Issue: Multiple Controller Support
**Solution:** Implement per-device mode settings

## Files to Modify

1. **config.json** - Add `controller_mode` setting
2. **boot.py** - Add X-Input USB IDs and descriptors  
3. **gamepad.py** - Add Xbox report format support
4. **Windows App** - Add mode selection UI

## Recommended Implementation

Start with **Option 1** (Configuration-Based Mode Switching) as it provides the best balance of:
- User choice and flexibility
- Backward compatibility  
- Game compatibility improvements
- Easy implementation and testing

This allows users to choose the best mode for their specific games and use cases while maintaining all existing functionality.
