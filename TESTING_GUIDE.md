# X-Input Testing Guide for BumbleGum Guitar Controllers

## Overview
This guide provides step-by-step instructions for testing the new X-Input (Xbox controller) support in your BumbleGum guitar controller firmware.

## Testing Environment Setup

### Prerequisites
- BumbleGum guitar controller with CircuitPython
- Windows 10/11 PC
- USB cable for controller connection
- Test games (recommended below)
- Git access to the `feature/xinput-support` branch

### Test Hardware
- Physical BumbleGum guitar controller
- All fret buttons functional
- Whammy bar working
- Strum bar operational
- D-pad/joystick responsive

## Phase 1: Firmware Installation Testing

### Step 1: Deploy X-Input Firmware
```bash
# Navigate to firmware directory
cd "C:\Users\mlwat\OneDrive\Desktop\BGG-Windows-App v3.0\bgg-firmware-updates"

# Ensure you're on the X-Input branch
git branch
# Should show: * feature/xinput-support

# Copy files to guitar controller (when connected as USB drive)
# Method 1: Manual copy (hold GREEN_FRET during boot to enable USB drive)
# Method 2: Use your Windows configurator app to deploy firmware
```

### Step 2: Configure X-Input Mode
Edit `config.json` on the controller:
```json
{
    "controller_mode": "xinput",
    // ... rest of configuration
}
```

### Step 3: Verify Firmware Load
1. Connect controller to PC
2. Check Windows Device Manager
3. Should see "Xbox 360 Controller" instead of custom HID device
4. Note the device path and driver information

## Phase 2: Windows Recognition Testing

### Test 2.1: Device Manager Verification
1. **Open Device Manager** (`Win + X`, select Device Manager)
2. **Look for "Xbox 360 Controller"** under "Microsoft Xbox One Controller" or "Human Interface Devices"
3. **Verify driver:** Should show Microsoft driver, not generic HID
4. **Check Properties:** Right-click → Properties → Details → Hardware Ids
   - Should show: `USB\VID_045E&PID_028E` (Microsoft Xbox 360 Controller)

### Test 2.2: Windows Game Controller Panel
1. **Open Control Panel** → Hardware and Sound → Devices and Printers
2. **Right-click controller** → "Game controller settings"
3. **Select controller** → Properties
4. **Expected Results:**
   - Shows as "Xbox 360 Controller"
   - All buttons should respond when pressed
   - Analog sticks should move when D-pad is used
   - Triggers should respond to whammy bar

### Test 2.3: Windows Gaming Services
1. **Open Xbox App** (Windows built-in)
2. **Check controller detection:** Should automatically recognize as Xbox controller
3. **Controller test:** Use Xbox app's controller test feature

## Phase 3: Button Mapping Testing

### Test 3.1: Button Response Verification
Create this test matrix and verify each input:

| Guitar Input | Expected Xbox Button | Test Method |
|--------------|---------------------|-------------|
| GREEN_FRET | A Button | Press in Game Controller panel |
| RED_FRET | B Button | Press in Game Controller panel |
| YELLOW_FRET | Y Button | Press in Game Controller panel |
| BLUE_FRET | X Button | Press in Game Controller panel |
| ORANGE_FRET | Left Bumper (LB) | Press in Game Controller panel |
| STRUM_UP | Right Bumper (RB) | Press in Game Controller panel |
| STRUM_DOWN | Right Bumper (RB) | Press in Game Controller panel |
| SELECT | Back Button | Press in Game Controller panel |
| START | Start Button | Press in Game Controller panel |
| TILT | Left Stick Click | Press in Game Controller panel |
| D-PAD UP | Left Stick Up | Watch analog stick in panel |
| D-PAD DOWN | Left Stick Down | Watch analog stick in panel |
| D-PAD LEFT | Left Stick Left | Watch analog stick in panel |
| D-PAD RIGHT | Left Stick Right | Watch analog stick in panel |
| WHAMMY | Right Trigger | Move whammy, watch trigger bar |

### Test 3.2: Analog Input Testing
1. **Whammy Bar → Right Trigger:**
   - Move whammy from minimum to maximum
   - Right trigger bar should move from 0% to 100%
   - Movement should be smooth and proportional

2. **D-Pad → Left Analog Stick:**
   - Press each D-pad direction
   - Left stick should move to corresponding position
   - Diagonal combinations should work (e.g., UP+RIGHT)

## Phase 4: Game Compatibility Testing

### Test 4.1: Steam Games
**Recommended test games:**
- **Rocket League** (Free) - Good Xbox controller support
- **Halo: The Master Chief Collection** - Xbox-optimized
- **Forza Horizon 5** - Racing game with controller support

**Test procedure:**
1. Launch Steam
2. Steam should auto-detect as "Xbox 360 Controller"
3. Launch test game
4. Check controller settings in-game
5. Verify all buttons work as expected
6. Test analog inputs (whammy as accelerator/brake)

### Test 4.2: Non-Steam Games
**Test with:**
- **Clone Hero** - Primary target for guitar controllers
- **YARG** - Open-source rhythm game
- **Fortnite Festival** - Epic Games rhythm mode

**Expected behavior:**
- Should work without additional configuration
- Button mapping should be automatic
- May need to set up as "Xbox controller" in game settings

### Test 4.3: Emulators
**Test with:**
- **Dolphin** (GameCube/Wii emulator)
- **PCSX2** (PS2 emulator)
- **RetroArch** (Multi-system emulator)

**Test procedure:**
1. Configure controller in emulator
2. Should appear as Xbox 360 controller option
3. Map guitar buttons to game functions
4. Test in-game functionality

## Phase 5: Mode Switching Testing

### Test 5.1: HID Mode Fallback
1. **Change config.json:**
   ```json
   "controller_mode": "hid"
   ```
2. **Reconnect controller**
3. **Verify:** Should appear as custom HID gamepad again
4. **Test original functionality:** All original features should work

### Test 5.2: Mode Switching via Configurator App
1. **Use your Windows app** to change controller mode
2. **Test seamless switching** between modes
3. **Verify settings persistence** after reconnection

## Phase 6: Performance and Stability Testing

### Test 6.1: Input Latency
1. **Use input lag testing software** (like InputLagTimer)
2. **Compare latency** between HID and X-Input modes
3. **Verify acceptable performance** (should be <10ms)

### Test 6.2: Extended Use Testing
1. **Connect controller for extended period** (2+ hours)
2. **Test continuous input** (button mashing, whammy movement)
3. **Monitor for disconnections** or driver issues
4. **Check Windows Event Viewer** for USB errors

### Test 6.3: Multiple Controller Testing
1. **Connect multiple controllers** in X-Input mode
2. **Verify each gets unique identity** in Windows
3. **Test simultaneous use** in games that support multiple controllers

## Phase 7: Edge Case Testing

### Test 7.1: Rapid Button Presses
1. **Rapid fire button testing** (strum bar especially)
2. **Verify no input drops** or stuck buttons
3. **Test button combinations** (multiple frets pressed)

### Test 7.2: Analog Edge Cases
1. **Whammy bar extremes** (fully up, fully down)
2. **D-pad combinations** (diagonal directions)
3. **Rapid analog changes** (quick whammy movements)

### Test 7.3: Connection Scenarios
1. **Hot-plug testing** (connect/disconnect while Windows running)
2. **Sleep/wake testing** (Windows sleep with controller connected)
3. **USB port switching** (different USB ports)

## Debugging and Troubleshooting

### Common Issues and Solutions

**Issue: Controller not detected as Xbox controller**
- Solution: Check USB VID/PID in Device Manager
- Should be: VID_045E&PID_028E

**Issue: Buttons not mapping correctly**
- Solution: Verify button mapping in gamepad_xinput.py
- Test with Windows Game Controller panel

**Issue: Analog inputs not working**
- Solution: Check whammy calibration values
- Verify D-pad to analog stick conversion

**Issue: Driver conflicts**
- Solution: Uninstall device, switch to HID mode, then back to X-Input

### Debug Tools
1. **Windows Device Manager** - Hardware detection
2. **Game Controller Panel** - Input testing
3. **USB Device Tree Viewer** - Low-level USB analysis
4. **Process Monitor** - Driver/file access monitoring

## Testing Checklist

### Pre-Testing
- [ ] Firmware branch deployed
- [ ] Controller configured for X-Input mode
- [ ] Windows recognizes as Xbox 360 Controller
- [ ] All hardware components functional

### Basic Functionality
- [ ] All fret buttons map to correct Xbox buttons
- [ ] Strum bar works as Right Bumper
- [ ] SELECT/START work as Back/Start
- [ ] D-pad converts to left analog stick
- [ ] Whammy bar works as right trigger

### Game Testing
- [ ] Steam recognizes controller automatically
- [ ] Test game (Rocket League) works correctly
- [ ] Clone Hero/rhythm games still functional
- [ ] No additional driver installation required

### Advanced Testing
- [ ] Mode switching works (HID ↔ X-Input)
- [ ] Multiple controllers supported
- [ ] Extended use stability verified
- [ ] Input latency acceptable

### Regression Testing
- [ ] Original HID mode still works
- [ ] All existing features preserved
- [ ] Configuration app compatibility maintained

## Success Criteria

The X-Input implementation is successful if:
1. ✅ Windows automatically recognizes as Xbox 360 Controller
2. ✅ All guitar inputs map correctly to Xbox equivalents
3. ✅ Games work without additional configuration
4. ✅ Performance matches or exceeds HID mode
5. ✅ Mode switching works reliably
6. ✅ No regression in existing functionality

## Reporting Issues

When reporting issues, include:
- Windows version
- Controller hardware version
- Firmware version and mode
- Specific game/application
- Steps to reproduce
- Expected vs actual behavior
- Screenshots of Device Manager/Game Controller panel
