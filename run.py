import time
import shutil
import os
from data_extraction.main_ocr import analyze_scoreboard
from google_sheets_integration.uploader import upload_to_sheet
from pynput import keyboard
import pyautogui
import constants


def on_activate():
    """The function called when the hotkey is pressed."""
    print(f"--- Hotkey {constants.HOTKEY} activated! ---")
    print("--- Starting main process ---")

    print(f"Current working directory: {os.getcwd()}")

    # --- Take Screenshot ---
    try:
        # Ensure the directory exists
        screenshot_dir = os.path.dirname(constants.SCREENSHOT_PATH)
        print(f"Ensuring directory '{screenshot_dir}' exists...")
        os.makedirs(screenshot_dir, exist_ok=True)

        print(f"Attempting to save screenshot to: {constants.SCREENSHOT_PATH}")
        screenshot = pyautogui.screenshot()
        screenshot.save(constants.SCREENSHOT_PATH)

        print(f"Screenshot saved to {constants.SCREENSHOT_PATH}")
        # Add a small delay to ensure the file is written
        time.sleep(1)
    except Exception as e:
        print(f"--- AN ERROR OCCURRED WHILE TAKING SCREENSHOT ---")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        print("-------------------------------------------------")
        print(
            "This might be a permissions issue. On macOS, you may need to grant your terminal or IDE screen recording and file access permissions in System Settings > Privacy & Security."
        )
        print("--- Analysis aborted ---")
        return
    # --- END Screenshot ---

    # Verify that the screenshot was saved before proceeding
    if not os.path.exists(constants.SCREENSHOT_PATH):
        print(f"Error: Screenshot not found at {constants.SCREENSHOT_PATH}")
        print("--- Analysis aborted ---")
        return

    print("--- Analyzing scoreboard ---")
    game_data = analyze_scoreboard(scoreboard_img_path=constants.SCREENSHOT_PATH)
    if game_data:
        print("--- Uploading to Google Sheets ---")
        upload_to_sheet(game_data)
        print("--- Process complete ---")
    else:
        print("--- Analysis failed, stopping process ---")
    print(f"--- Waiting for next hotkey press ({constants.HOTKEY}) ---")


def on_press(key):
    if key == keyboard.Key.f6:
        on_activate()


if __name__ == "__main__":
    print(f"--- Overwatch Stats OCR (DEBUG MODE) ---")
    print(f"Press the hotkey ({constants.HOTKEY}) to start the process.")
    print("The script is now running in the background.")
    print("Press Ctrl+C in the console to exit.")

    with keyboard.Listener(on_press=on_press) as l:
        l.join()
    # print(analyze_scoreboard("data_extraction/scoreboard.png"))
