import sys
import os


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# --- AUTOMATION CONFIG ---
# The key to press to trigger the screenshot and analysis
# You can find key names here: https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key
HOTKEY = "f6"

# The path where the screenshot will be saved
SCREENSHOT_PATH = "screenshots/screenshot.png"
