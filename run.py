import time
import os
import logging
import threading
import subprocess
import sys
import webbrowser
from web_app.app import app as web_app
from PIL import Image, ImageDraw
from pystray import MenuItem as item, Icon as icon
from pynput import keyboard
import pyautogui
import constants
from data_extraction.main_ocr import analyze_scoreboard
from google_sheets_integration.uploader import upload_to_sheet

import json


# --- Setup Logging ---
# Create a logs directory in the user's home folder
log_dir = os.path.join(os.path.expanduser("~"), "OverwatchStatsOCR_Logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app.log")

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(log_file, mode='a')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)
root_logger = logging.getLogger()
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)
root_logger.setLevel(logging.INFO)

# --- Global State ---
keyboard_listener = None
is_listener_running = False
web_app_process = None

def on_setup_complete(config_data):
    """Callback function to save config and then relaunch the application."""
    # The config is saved by the setup GUI now, so this function just needs to relaunch.
    logging.info("Setup complete. Relaunching application...")
    
    # Relaunch the application in a new, clean process
    # This completely separates the setup environment from the main app environment.
    subprocess.Popen([sys.executable, __file__])
    
    # Exit the current (setup) process
    sys.exit(0)


def create_default_icon():
    """Creates a simple 64x64px icon for the system tray."""
    width, height = 64, 64
    # Simple blue circle on a transparent background
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, width - 4, height - 4), fill="royalblue")
    return image


def on_activate():
    """The function called when the hotkey is pressed."""
    logging.info(f"--- Hotkey {constants.HOTKEY} activated! Starting main process ---")
    try:
        screenshot_dir = os.path.dirname(constants.SCREENSHOT_PATH)
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot = pyautogui.screenshot()
        screenshot.save(constants.SCREENSHOT_PATH)
        logging.info(f"Screenshot saved to {constants.SCREENSHOT_PATH}")
        time.sleep(1)
    except Exception:
        logging.error(
            "--- AN ERROR OCCURRED WHILE TAKING SCREENSHOT ---", exc_info=True
        )
        return

    if not os.path.exists(constants.SCREENSHOT_PATH):
        logging.error(f"Screenshot not found at {constants.SCREENSHOT_PATH}. Aborting.")
        return

    logging.info("--- Analyzing scoreboard ---")
    game_data = analyze_scoreboard(scoreboard_img_path=constants.SCREENSHOT_PATH)

    if game_data:
        logging.info("--- Uploading to Google Sheets ---")
        upload_to_sheet(game_data)
        logging.info("--- Process complete ---")
    else:
        logging.warning("--- Analysis failed or was aborted, stopping process ---")
    logging.info(f"--- Waiting for next hotkey press ({constants.HOTKEY}) ---")


def on_press(key):
    hotkey_char = None
    try:
        hotkey_char = key.char
    except AttributeError:
        pass  # Special key

    if hotkey_char == constants.HOTKEY or key == getattr(keyboard.Key, constants.HOTKEY, None):
        on_activate()


def start_listener():
    global keyboard_listener, is_listener_running
    if not is_listener_running:
        logging.info("Starting keyboard listener.")
        keyboard_listener = keyboard.Listener(on_press=on_press)
        keyboard_listener.start()
        is_listener_running = True


def stop_listener():
    global keyboard_listener, is_listener_running
    if is_listener_running and keyboard_listener:
        logging.info("Stopping keyboard listener.")
        keyboard_listener.stop()
        is_listener_running = False


web_app_thread = None


def launch_web_dashboard():
    global web_app_thread
    if web_app_thread and web_app_thread.is_alive():
        logging.warning("Web dashboard is already running.")
        webbrowser.open("http://127.0.0.1:8050/")
        return

    def run_app():
        try:
            web_app.run(host="127.0.0.1", port=8050)
        except Exception as e:
            logging.error(f"Failed to start web app: {e}", exc_info=True)

    web_app_thread = threading.Thread(target=run_app)
    web_app_thread.daemon = True
    web_app_thread.start()
    logging.info("Web dashboard started.")
    # Give the server a moment to start before opening the browser
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8050/")


def on_exit(icon, item):
    logging.info("Exit selected. Shutting down.")
    stop_listener()
    if web_app_thread:
        # It's a daemon thread, so it should exit with the main program.
        # No explicit stop needed unless it's not a daemon.
        pass
    icon.stop()


def main():
    logging.info("--- Overwatch Stats OCR ---")

    # The pystray documentation recommends starting listeners
    # in a setup function passed to run(). This avoids race conditions on macOS.
    def post_setup(icon):
        icon.visible = True
        start_listener()

    # Setup the system tray icon
    tray_icon = icon(
        'OverwatchStatsOCR',
        create_default_icon(),
        'Overwatch Stats OCR',
        menu=(
            item('Status: Listening', None, enabled=False),
            item('Launch Web Dashboard', launch_web_dashboard),
            item('Exit', on_exit)
        )
    )
    logging.info("Application started. System tray icon is now active.")
    tray_icon.run(setup=post_setup)


if __name__ == "__main__":
    # --- Fix for Qt Platform Plugin Error ---
    # In complex environments like Anaconda, we must explicitly tell Qt where its
    # plugins are. We do this by finding the PyQt6 package path directly.
    try:
        import PyQt6
        import os
        
        # Get the path to the PyQt6 package
        pyqt_path = os.path.dirname(PyQt6.__file__)
        # Construct the full path to the Qt plugins directory
        plugins_path = os.path.join(pyqt_path, "Qt6", "plugins")
        
        # Set the environment variable. This is the most reliable method for development.
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugins_path
        
        logging.info(f"Forcing Qt plugin path to: {plugins_path}")

    except Exception as e:
        logging.warning(f"Could not set Qt plugin path: {e}")
    # --- End of Fix ---

    try:
        # Check if config exists before starting
        if not os.path.exists(constants.CONFIG_FILE):
            logging.info("Configuration not found. Launching first-time setup GUI.")
            # We import here, after the path has been set.
            from setup_gui import run_setup_flow
            run_setup_flow(on_setup_complete)
        else:
            main()
    except Exception as e:
        logging.critical(
            "--- A CRITICAL UNHANDLED EXCEPTION OCCURRED ---", exc_info=True
        )
        # In a real GUI app, you would show a message box to the user here.
        # For now, the log file is our only record.
        sys.exit(1)
