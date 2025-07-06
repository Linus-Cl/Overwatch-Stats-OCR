import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- CONFIGURATION ---
# This scope allows the app to read and write to Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
# Path to your client secret file (downloaded from Google Cloud Console)
CLIENT_SECRET_FILE = "google_sheets_integration/client_secret.json"
# The name of the Google Sheet to upload to
SHEET_ID = "1GA_Y0fQ9MqqTfyr9CngHvSyqOKDlq-7TpXVVyb7r3A0"  # <--- REPLACE THIS WITH YOUR ACTUAL SHEET ID


def get_sheet(sheet_id):
    """
    Authenticates with the Google Sheets API and returns a worksheet object.
    """
    try:
        # Authenticate using OAuth 2.0 for desktop applications
        # This will open a browser window for you to authorize the first time
        client = gspread.oauth(credentials_filename=CLIENT_SECRET_FILE, scopes=SCOPES)
        sheet = client.open_by_key(sheet_id).sheet1  # Get the first worksheet
        return sheet
    except FileNotFoundError:
        print(f"ERROR: Client secret file not found at '{CLIENT_SECRET_FILE}'.")
        print(
            "Please ensure you have downloaded 'client_secret.json' from Google Cloud Console and placed it in the 'google_sheets_integration/' directory."
        )
        return None
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"ERROR: Google Sheet with ID '{sheet_id}' not found.")
        print(
            "Please ensure the Google Sheet exists and you have shared it with the email address that authorized this application."
        )
        return None
    except Exception as e:
        print(f"An unexpected error occurred during Google Sheets authentication: {e}")
        return None


def flatten_json_for_sheet(data):
    """
    Flattens the complex JSON structure into a single list (row)
    that can be easily appended to a Google Sheet.
    """
    # --- Basic Info ---
    row = [
        data.get("date", ""),
        data.get("map", ""),
        data.get("gamemode", ""),
        data.get("result", ""),
        data.get("length", ""),
    ]

    # --- Team Info ---
    team1 = data.get("team1", {})
    team2 = data.get("team2", {})
    row.extend([team1.get("score", ""), team1.get("side", "")])
    row.extend([team2.get("score", ""), team2.get("side", "")])

    # --- Player Info (assuming a fixed order based on KNOWN_PLAYERS) ---
    # This part is crucial and needs to be robust. We create a dictionary
    # to hold player data for easy lookup.
    player_map = {}
    for p_data in team1.get("players", []):
        player_map[p_data["player_name"]] = p_data
    for p_data in team2.get("players", []):
        player_map[p_data["player_name"]] = p_data

    # Now, we iterate through the *known* players from your constants to ensure
    # the order is always the same in the spreadsheet.
    from constants import KNOWN_PLAYERS

    for player_name in KNOWN_PLAYERS:
        player_info = player_map.get(player_name)
        if player_info:
            row.append(player_info.get("hero", "N/A"))
        else:
            # This player wasn't in the match
            row.append("nicht dabei")

    return row


def get_header_row():
    """
    Generates the header row for the Google Sheet based on the data structure.
    This ensures consistency between the data and the column titles.
    """
    header = [
        "Datum",
        "Map",
        "Gamemode",
        "Win Lose",
        "Game Length",
        "Team 1 Score",
        "Team 1 Side",
        "Team 2 Score",
        "Team 2 Side",
    ]
    # Add player hero columns dynamically from constants
    from constants import KNOWN_PLAYERS

    for player in KNOWN_PLAYERS:
        header.append(f"{player} Hero")

    return header


def upload_to_sheet(data):
    """
    Main function to upload a single game's data to the Google Sheet.
    It flattens the data, gets the sheet, and appends the new row.
    It also checks if the header exists and adds it if needed.
    """
    print("--- GOOGLE SHEETS UPLOAD ---")
    sheet = get_sheet(SHEET_ID)
    if not sheet:
        print("└──> Upload failed: Could not access the worksheet.")
        return

    # Check if the sheet is empty to add a header row
    if not sheet.get_all_values():
        print("  - Sheet is empty. Adding header row...")
        header = get_header_row()
        sheet.append_row(header)
        print("    └──> Header row added successfully.")

    # Prepare and append the data row
    new_row = flatten_json_for_sheet(data)
    print(f"  - Appending new game data: {new_row}")
    try:
        sheet.append_row(new_row)
        print("└──> Successfully uploaded data to Google Sheets.")
    except Exception as e:
        print(f"└──> Upload failed: An error occurred while appending the row: {e}")
