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


# --- TESSERACT CONFIG ---
# If tesseract is not in your PATH, include the full path to the Tesseract executable.
# Example for Windows: r'C:/Program Files/Tesseract-OCR/tesseract.exe'
# Example for macOS (if installed with Homebrew): '/opt/homebrew/bin/tesseract'
TESSERACT_CMD_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# --- AUTOMATION CONFIG ---
# The key to press to trigger the screenshot and analysis
# You can find key names here: https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key
HOTKEY = "f6"

# The path where the screenshot will be saved
# We save it in the user's home directory to avoid permission issues.
SCREENSHOT_DIR = os.path.join(os.path.expanduser("~"), "OverwatchStatsOCR_Screenshots")
SCREENSHOT_PATH = os.path.join(SCREENSHOT_DIR, "screenshot.png")

# --- APPLICATION CONFIG FILES ---
# We store user-generated config in the user's home directory.
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "OverwatchStatsOCR_Data")
CONFIG_FILE = os.path.join(USER_DATA_DIR, "config.json")
TOKEN_FILE = os.path.join(USER_DATA_DIR, "token.json")
