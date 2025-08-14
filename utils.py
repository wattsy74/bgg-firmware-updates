# utils.py
__version__ = "4.0.0"

def get_version():
    return __version__
# Utility functions for BGG Firmware
import board

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple. Handles both #ffffff and ffffff formats."""
    if not hex_color:
        return (0, 0, 0)  # Default to black for invalid colors
    
    hex_color = hex_color.lstrip("#")
    
    # Ensure we have exactly 6 characters
    if len(hex_color) != 6:
        print(f"Warning: Invalid hex color format '{hex_color}', using black")
        return (0, 0, 0)
    
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        print(f"Warning: Could not parse hex color '{hex_color}', using black")
        return (0, 0, 0)

def load_config(raw, resolve_pin):
    conf = {}
    for key, value in raw.items():
        if isinstance(value, str) and value.startswith("GP"):
            conf[key] = resolve_pin(value)
        elif isinstance(value, list):
            # Handle color arrays - convert any HEX strings to RGB tuples
            converted_list = []
            for v in value:
                if isinstance(v, str) and (v.startswith("#") or len(v) == 6):
                    # Handle both "#ffffff" and "ffffff" formats
                    converted_list.append(hex_to_rgb(v))
                else:
                    converted_list.append(v)
            conf[key] = converted_list
        elif isinstance(value, str) and value.startswith("#"):
            conf[key] = hex_to_rgb(value)
        else:
            conf[key] = value
    return conf
