# boot.py v3.5 - Complete with Update Processor and 12-File Log Rotation
__version__ = "3.5"

def get_version():
    return __version__

import microcontroller
import board
import digitalio
import storage
import usb_cdc
import usb_hid
import usb_midi
import supervisor

# Use last 2 bytes of UID for unique PID
uid_bytes = microcontroller.cpu.uid
unique_pid = int.from_bytes(uid_bytes[-2:], "big")

# Custom HID Gamepad Descriptor (Report ID 5)
GAMEPAD_REPORT_DESCRIPTOR = bytes((
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

supervisor.set_usb_identification(
    manufacturer="BumbleGum",
    product="CH-Guitar",
    vid=0x6997,
    pid=unique_pid
)

usb_hid.set_interface_name("BumbleGum Guitars - Guitar Controller")

# Enable custom HID gamepad
gamepad = usb_hid.Device(
    report_descriptor=GAMEPAD_REPORT_DESCRIPTOR,
    usage_page=0x01,
    usage=0x05,
    report_ids=(5,),
    in_report_lengths=(4,),  # 4 bytes: 2 for buttons, 1 for hat, 1 for Z
    out_report_lengths=(0,)
)
usb_hid.enable((gamepad,))

# Disable MIDI
usb_midi.disable()

# Enable USB CDC (console + data)
usb_cdc.enable(console=True, data=True)

# Disable auto-reload to prevent interruptions during file operations
# Try multiple methods for compatibility across CircuitPython versions
try:
    # CircuitPython 8.x and newer method
    supervisor.runtime.autoreload = False
    print("✅ Auto-reload disabled via supervisor.runtime.autoreload")
except (AttributeError, NameError):
    try:
        # Alternative method for some versions
        supervisor.disable_autoreload()
        print("✅ Auto-reload disabled via supervisor.disable_autoreload()")
    except (AttributeError, NameError):
        print("⚠️ Auto-reload disable not available - manual reboot control only")

# ===== FIRMWARE UPDATE SYSTEM =====
# Logging system for tracking update attempts
def write_log(message, log_file_path):
    try:
        with open(log_file_path, 'a') as log_file:
            import time
            # Simple timestamp (CircuitPython doesn't have full datetime)
            log_file.write(f"[{time.monotonic():.3f}s] {message}\n")
        print(message)  # Also print to console
    except Exception as e:
        print(f"{message} (LOG ERROR: {e})")

# Smart config merge function to preserve user settings while adding new options
def merge_config_file(update_path, target_path, log_file_path):
    """
    Merge config.json files intelligently:
    - Preserve all existing user settings
    - Add new settings from update
    - Update version/metadata if present
    - Create backup of original
    """
    try:
        import json
        
        write_log(f"🔀 Smart merging config file: {update_path} -> {target_path}", log_file_path)
        
        # Load existing config (if it exists)
        existing_config = {}
        try:
            with open(target_path, 'r') as f:
                existing_config = json.load(f)
            write_log(f"📖 Loaded existing config with {len(existing_config)} settings", log_file_path)
        except (OSError, ValueError) as e:
            write_log(f"⚠️ No existing config or invalid JSON, creating new: {e}", log_file_path)
        
        # Load update config
        with open(update_path, 'r') as f:
            update_config = json.load(f)
        write_log(f"📥 Loaded update config with {len(update_config)} settings", log_file_path)
        
        # Create backup of existing config
        if existing_config:
            try:
                backup_path = f'{target_path}.backup'
                with open(backup_path, 'w') as f:
                    json.dump(existing_config, f)
                write_log(f"💾 Created config backup: {backup_path}", log_file_path)
            except Exception as e:
                write_log(f"⚠️ Could not create backup: {e}", log_file_path)
        
        # Smart merge logic
        merged_config = existing_config.copy()  # Start with existing settings
        new_settings = []
        updated_settings = []
        
        # Special handling for preset files
        is_preset_file = 'preset' in target_path.lower()
        
        for key, value in update_config.items():
            if key not in existing_config:
                # New setting - add it
                merged_config[key] = value
                new_settings.append(key)
            elif key in ['version', 'firmware_version', 'config_version', 'last_updated']:
                # Version/metadata fields - update from new config
                merged_config[key] = value
                updated_settings.append(key)
            elif is_preset_file and key == 'presets' and isinstance(value, dict) and isinstance(existing_config.get(key), dict):
                # Special preset merging: merge preset dictionaries by adding new presets while preserving existing ones
                existing_presets = existing_config[key]
                update_presets = value
                merged_presets = existing_presets.copy()
                
                new_presets = []
                for preset_name, preset_data in update_presets.items():
                    if preset_name not in existing_presets:
                        merged_presets[preset_name] = preset_data
                        new_presets.append(preset_name)
                    else:
                        write_log(f"🔒 Preserving user preset: {preset_name}", log_file_path)
                
                merged_config[key] = merged_presets
                if new_presets:
                    write_log(f"🎮 Added new presets: {new_presets}", log_file_path)
            else:
                # Existing setting - keep user's value
                write_log(f"🔒 Preserving user setting: {key}", log_file_path)
        
        # Write merged config
        with open(target_path, 'w') as f:
            json.dump(merged_config, f)
        
        # Log merge results
        if new_settings:
            write_log(f"➕ Added new settings: {new_settings}", log_file_path)
        if updated_settings:
            write_log(f"🔄 Updated metadata: {updated_settings}", log_file_path)
        
        write_log(f"✅ Config merge complete: {len(merged_config)} total settings", log_file_path)
        return True
        
    except Exception as e:
        write_log(f"❌ Config merge failed: {e}", log_file_path)
        write_log(f"🔍 Error details: {type(e).__name__}: {str(e)}", log_file_path)
        return False

# Check for pending firmware updates in /updates/ folder at boot
def process_firmware_updates():
    import os
    
    # Create incremental log file with rollover (keep only last 12 logs)
    log_number = 1
    existing_logs = []
    
    # Find all existing log files
    try:
        root_files = os.listdir('/')
        for filename in root_files:
            if filename.startswith('update_log_') and filename.endswith('.txt'):
                try:
                    # Extract log number from filename
                    log_num = int(filename[11:14])  # update_log_XXX.txt
                    existing_logs.append(log_num)
                except ValueError:
                    pass  # Skip malformed log filenames
    except Exception as e:
        pass  # Continue if directory listing fails
    
    # Sort existing logs and find next number
    existing_logs.sort()
    if existing_logs:
        log_number = existing_logs[-1] + 1
    
    # If we have 12 or more logs, remove the oldest one
    if len(existing_logs) >= 12:
        oldest_log_num = existing_logs[0]
        try:
            os.remove(f'/update_log_{oldest_log_num:03d}.txt')
            print(f"🗑️ Removed old log file: update_log_{oldest_log_num:03d}.txt")
        except Exception as e:
            print(f"⚠️ Could not remove old log: {e}")
    
    log_file_path = f'/update_log_{log_number:03d}.txt'
    
    write_log("🔍 DEBUG: Starting process_firmware_updates()", log_file_path)
    write_log(f"📝 Using log file: {log_file_path}", log_file_path)
    if existing_logs:
        write_log(f"📊 Log management: {len(existing_logs)} existing logs, keeping last 12", log_file_path)
    try:
        # Check if updates folder exists
        root_files = os.listdir('/')
        write_log(f"🔍 DEBUG: Root file count: {len(root_files)}", log_file_path)
        has_updates = 'updates' in root_files
        write_log(f"🔍 DEBUG: Has updates folder: {has_updates}", log_file_path)
        
        if has_updates:
            write_log("🔄 Firmware updates found, processing...", log_file_path)
            update_files = os.listdir('/updates')
            write_log(f"🔍 DEBUG: Found {len(update_files)} update files", log_file_path)
            
            if update_files:
                write_log(f"📦 Found {len(update_files)} update files", log_file_path)
                
                # Ensure filesystem is writable for updates
                try:
                    storage.remount("/", readonly=False)
                    write_log("📝 Filesystem remounted as writable", log_file_path)
                except Exception as e:
                    write_log(f"⚠️ Could not remount filesystem: {e}", log_file_path)
                    write_log("🔄 Attempting updates anyway...", log_file_path)
                
                # Create update flag with retry counter to prevent infinite loops
                retry_count = 0
                try:
                    # Check if there's an existing retry count file
                    try:
                        with open('/update_retry_count.txt', 'r') as f:
                            retry_count = int(f.read().strip())
                    except:
                        retry_count = 0
                    
                    retry_count += 1
                    write_log(f"🔍 DEBUG: Update attempt #{retry_count}", log_file_path)
                    
                    # Maximum 3 retry attempts to prevent infinite loops
                    if retry_count > 3:
                        write_log("❌ Maximum retry attempts exceeded, aborting updates", log_file_path)
                        # Clean up everything to prevent further attempts
                        try:
                            for filename in update_files:
                                os.remove(f'/updates/{filename}')
                            os.rmdir('/updates')
                            os.remove('/update_retry_count.txt')
                            write_log("🗑️ Cleaned up failed update files", log_file_path)
                        except Exception as cleanup_e:
                            write_log(f"⚠️ Cleanup failed: {cleanup_e}", log_file_path)
                        return
                    
                    # Save retry count
                    with open('/update_retry_count.txt', 'w') as f:
                        f.write(str(retry_count))
                    
                    with open('/updating.flag', 'w') as flag_file:
                        flag_file.write(f'firmware_update_in_progress_attempt_{retry_count}\n')
                    write_log(f"🏁 Update flag created (attempt {retry_count})", log_file_path)
                except Exception as e:
                    write_log(f"⚠️ Could not create update flag: {e}", log_file_path)
                
                # Move each file from /updates/ to root, with special handling for config files
                success_count = 0
                failed_files = []
                for filename in update_files:
                    write_log(f"🔍 DEBUG: Processing file: {filename}", log_file_path)
                    try:
                        update_path = f'/updates/{filename}'
                        target_path = f'/{filename}'
                        
                        # Special handling for config files
                        if filename.lower().endswith('.json') and ('config' in filename.lower() or 'preset' in filename.lower()):
                            write_log(f"⚙️ Detected config file, using smart merge", log_file_path)
                            
                            if merge_config_file(update_path, target_path, log_file_path):
                                write_log(f"✅ Config merged: {filename}", log_file_path)
                                success_count += 1
                                
                                # Remove the update file after successful merge
                                write_log(f"🔍 DEBUG: Removing update file: {update_path}", log_file_path)
                                os.remove(update_path)
                                write_log(f"🔍 DEBUG: Update file removed", log_file_path)
                            else:
                                write_log(f"❌ Config merge failed: {filename}", log_file_path)
                                failed_files.append(filename)
                        else:
                            # Standard file replacement for non-config files
                            write_log(f"🔍 DEBUG: Standard file replacement", log_file_path)
                            write_log(f"🔍 DEBUG: Reading from: {update_path}", log_file_path)
                            
                            # Check file size to determine reading strategy
                            try:
                                import os
                                file_size = os.stat(update_path)[6]  # File size in bytes
                                write_log(f"🔍 DEBUG: File size: {file_size} bytes", log_file_path)
                                
                                if file_size > 30000:  # Files larger than 30KB use chunked reading
                                    write_log(f"🧠 DEBUG: Using chunked reading for large file ({file_size} bytes)", log_file_path)
                                    
                                    # Memory-efficient chunked file copy
                                    write_log(f"🔍 DEBUG: Writing to: {target_path}", log_file_path)
                                    chunk_size = 1024  # 1KB chunks
                                    bytes_copied = 0
                                    
                                    with open(update_path, 'rb') as update_file:
                                        with open(target_path, 'wb') as target_file:
                                            while True:
                                                chunk = update_file.read(chunk_size)
                                                if not chunk:
                                                    break
                                                target_file.write(chunk)
                                                bytes_copied += len(chunk)
                                                
                                                # Progress logging every 10KB
                                                if bytes_copied % 10240 == 0:
                                                    write_log(f"🔍 DEBUG: Copied {bytes_copied}/{file_size} bytes", log_file_path)
                                                
                                                # Yield control and cleanup every 5KB to prevent memory buildup
                                                if bytes_copied % 5120 == 0:
                                                    import gc
                                                    gc.collect()
                                    
                                    write_log(f"🔍 DEBUG: Chunked write completed ({bytes_copied} bytes)", log_file_path)
                                else:
                                    # Small files - use original method
                                    write_log(f"🔍 DEBUG: Using standard reading for small file ({file_size} bytes)", log_file_path)
                                    
                                    # Read update file
                                    with open(update_path, 'rb') as update_file:
                                        content = update_file.read()
                                    write_log(f"🔍 DEBUG: Read {len(content)} bytes", log_file_path)
                                    
                                    write_log(f"🔍 DEBUG: Writing to: {target_path}", log_file_path)
                                    # Write to target location (overwrite)
                                    with open(target_path, 'wb') as target_file:
                                        target_file.write(content)
                                    write_log(f"🔍 DEBUG: Write completed", log_file_path)
                                
                            except Exception as file_error:
                                # Fallback to original method if size check fails
                                write_log(f"🔍 DEBUG: Size check failed, using fallback: {file_error}", log_file_path)
                                
                                # Read update file
                                with open(update_path, 'rb') as update_file:
                                    content = update_file.read()
                                write_log(f"🔍 DEBUG: Read {len(content)} bytes", log_file_path)
                                
                                write_log(f"🔍 DEBUG: Writing to: {target_path}", log_file_path)
                                # Write to target location (overwrite)
                                with open(target_path, 'wb') as target_file:
                                    target_file.write(content)
                                write_log(f"🔍 DEBUG: Write completed", log_file_path)
                            
                            write_log(f"✅ Updated: {filename}", log_file_path)
                            success_count += 1
                            
                            # Remove the update file only after successful write
                            write_log(f"🔍 DEBUG: Removing update file: {update_path}", log_file_path)
                            os.remove(update_path)
                            write_log(f"🔍 DEBUG: Update file removed", log_file_path)
                        
                    except Exception as e:
                        write_log(f"❌ Failed to update {filename}: {e}", log_file_path)
                        write_log(f"🔍 DEBUG: Error details: {type(e).__name__}: {str(e)}", log_file_path)
                        failed_files.append(filename)
                        # Continue with other files, don't abort entire update
                
                # Clean up only if ALL files were successfully updated
                if success_count == len(update_files):
                    try:
                        write_log("🔍 DEBUG: All files successful, removing /updates directory", log_file_path)
                        os.rmdir('/updates')
                        write_log("🗑️ Cleaned up /updates/ folder", log_file_path)
                        # Remove retry counter on complete success
                        try:
                            os.remove('/update_retry_count.txt')
                            write_log("🔍 DEBUG: Retry counter reset", log_file_path)
                        except:
                            pass
                    except Exception as e:
                        write_log(f"🔍 DEBUG: Could not remove /updates: {e}", log_file_path)
                else:
                    write_log(f"🔍 DEBUG: Only {success_count}/{len(update_files)} files updated, keeping /updates folder", log_file_path)
                
                # Remove update flag only if at least some files succeeded
                if success_count > 0:
                    try:
                        write_log("🔍 DEBUG: Removing update flag", log_file_path)
                        os.remove('/updating.flag')
                        write_log("🏁 Update flag removed", log_file_path)
                    except Exception as e:
                        write_log(f"🔍 DEBUG: Could not remove flag: {e}", log_file_path)
                else:
                    write_log("🔍 DEBUG: No files updated, keeping update flag for retry", log_file_path)
                
                write_log(f"🔍 DEBUG: Update summary - {success_count} files updated out of {len(update_files)}", log_file_path)
                if failed_files:
                    write_log(f"🔍 DEBUG: Failed files: {failed_files}", log_file_path)
                
                if success_count > 0:
                    write_log(f"🔄 Firmware update complete ({success_count} files), restarting...", log_file_path)
                    import microcontroller
                    microcontroller.reset()
                else:
                    write_log("❌ No files were successfully updated", log_file_path)
                    write_log("🔍 DEBUG: Update failed completely, will retry on next boot", log_file_path)
                
            else:
                write_log("🔍 DEBUG: Updates folder is empty", log_file_path)
                # Empty updates folder, just remove it
                try:
                    os.rmdir('/updates')
                    write_log("🗑️ Removed empty updates folder", log_file_path)
                except Exception as e:
                    write_log(f"🔍 DEBUG: Could not remove empty updates folder: {e}", log_file_path)
        else:
            write_log("🔍 DEBUG: No updates folder found", log_file_path)
                    
    except Exception as e:
        write_log(f"⚠️ Update check failed: {e}", log_file_path)
        write_log(f"🔍 DEBUG: Update check error details: {type(e).__name__}: {str(e)}", log_file_path)
        # Clean up flag if it exists
        try:
            os.remove('/updating.flag')
        except:
            pass

# Check if we're in a boot loop (updating.flag exists from previous failed boot)
def check_boot_loop():
    import os
    print("🔍 DEBUG: Starting check_boot_loop()")
    try:
        root_files = os.listdir('/')
        print(f"🔍 DEBUG: Root file count: {len(root_files)}")
        has_flag = 'updating.flag' in root_files
        has_updates = 'updates' in root_files
        print(f"🔍 DEBUG: updating.flag={has_flag}, updates={has_updates}")
        
        if has_flag:
            print("⚠️ Update flag detected from previous boot - possible boot loop")
            print("🔄 Attempting recovery...")
            
            # Ensure filesystem is writable for recovery
            try:
                storage.remount("/", readonly=False)
                print("📝 Filesystem remounted for recovery")
            except Exception as e:
                print(f"⚠️ Could not remount for recovery: {e}")
            
            # Remove update flag to prevent infinite loop
            try:
                os.remove('/updating.flag')
                print("🏁 Update flag removed for recovery")
            except Exception as e:
                print(f"🔍 DEBUG: Could not remove update flag: {e}")
            
            # Also clean up retry counter to prevent excessive retries
            try:
                os.remove('/update_retry_count.txt')
                print("🔍 DEBUG: Retry counter cleared for recovery")
            except:
                pass
            
            # If updates folder still exists, remove it to prevent re-triggering
            try:
                if has_updates:
                    print("🔍 DEBUG: Found updates folder during recovery, clearing it")
                    update_files = os.listdir('/updates')
                    print(f"🔍 DEBUG: {len(update_files)} files to remove")
                    for filename in update_files:
                        try:
                            os.remove(f'/updates/{filename}')
                            print(f"🔍 DEBUG: Removed {filename}")
                        except Exception as e:
                            print(f"🔍 DEBUG: Could not remove {filename}: {e}")
                    os.rmdir('/updates')
                    print("🗑️ Cleared updates folder for recovery")
                else:
                    print("🔍 DEBUG: No updates folder found during recovery")
            except Exception as e:
                print(f"🔍 DEBUG: Error during updates folder cleanup: {e}")
            
            print("🔍 DEBUG: Boot loop recovery completed")
            return True  # Indicates we recovered from a potential boot loop
    except Exception as e:
        print(f"🔍 DEBUG: Boot loop check failed: {e}")
    
    print("🔍 DEBUG: No boot loop detected")
    return False

# Recovery check first (this may enable filesystem writes)
recovered_from_boot_loop = check_boot_loop()

# Only process updates if we didn't just recover from a boot loop
if not recovered_from_boot_loop:
    process_firmware_updates()

# Hold GREEN_FRET (GP10) to enable USB drive (for manual debugging only)
# This happens AFTER firmware updates so filesystem is writable during updates
button = digitalio.DigitalInOut(board.GP10)
button.switch_to_input(pull=digitalio.Pull.UP)

if not button.value:  # GREEN_FRET pressed - manual debugging mode
    print("🔓 GREEN_FRET pressed - USB drive enabled for manual debugging")
    # USB drive remains enabled (writable filesystem)
else:
    print("🔒 USB drive disabled for normal operation")
    storage.disable_usb_drive()
    # Firmware updates work via serial protocol with automatic processing at boot

print(f"BGG Guitar Controller v{__version__} boot complete!")
