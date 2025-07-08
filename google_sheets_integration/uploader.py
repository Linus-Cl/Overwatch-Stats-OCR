import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os
import pandas as pd
from datetime import datetime

from constants import resource_path

# --- CONFIGURATION ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CLIENT_SECRET_FILE = resource_path("google_sheets_integration/client_secret.json")
TOKEN_FILE = "token.json"
CONFIG_FILE = "config.json"

# --- HERO TO ROLE MAPPING ---
HERO_ROLES = {
    # Damage
    "Ashe": "Damage",
    "Bastion": "Damage",
    "Cassidy": "Damage",
    "Echo": "Damage",
    "Freja": "Damage",
    "Genji": "Damage",
    "Hanzo": "Damage",
    "Junkrat": "Damage",
    "Mei": "Damage",
    "Pharah": "Damage",
    "Reaper": "Damage",
    "Sojourn": "Damage",
    "Soldier": "Damage",
    "Sombra": "Damage",
    "Symmetra": "Damage",
    "Torbjoern": "Damage",
    "Tracer": "Damage",
    "Widowmaker": "Damage",
    "Venture": "Damage",
    # Tank
    "D.Va": "Tank",
    "Doomfist": "Tank",
    "Hazard": "Tank",
    "Junkerqueen": "Tank",
    "Orisa": "Tank",
    "Ramattra": "Tank",
    "Reinhardt": "Tank",
    "Roadhog": "Tank",
    "Sigma": "Tank",
    "Winston": "Tank",
    "Wrecking Ball": "Tank",
    "Zarya": "Tank",
    "Mauga": "Tank",
    # Support
    "Ana": "Support",
    "Baptiste": "Support",
    "Brigitte": "Support",
    "Illari": "Support",
    "Juno": "Support",
    "Kiriko": "Support",
    "Lifeweaver": "Support",
    "Lucio": "Support",
    "Mercy": "Support",
    "Moira": "Support",
    "Zenyatta": "Support",
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request

            creds.refresh(Request())
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRET_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
            except FileNotFoundError:
                print(
                    f"ERROR: '{CLIENT_SECRET_FILE}' not found. Please run setup.py first."
                )
                return None
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


def get_sheet(sheet_id, creds):
    try:
        client = gspread.authorize(creds)
        return client.open_by_key(sheet_id).sheet1
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"ERROR: Google Sheet with ID '{sheet_id}' not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def get_next_match_id(sheet):
    """Gets the last Match ID from the sheet and increments it."""
    try:
        last_id = sheet.col_values(1)[-1]
        return int(last_id) + 1 if last_id.isdigit() else 1
    except (IndexError, ValueError):
        return 1


def flatten_json_for_sheet(data, config, match_id):
    """
    Flattens the JSON, generates derived data, and prepares the row for upload.
    """
    date_str = data.get("date", "")
    try:
        date_obj = datetime.strptime(date_str, "%m/%d/%Y")
        year = date_obj.year
        month = date_obj.strftime("%B")
    except (ValueError, TypeError):
        date_obj, year, month = None, "", ""

    row = [
        match_id,
        date_obj.strftime("%Y-%m-%d") if date_obj else "",
        config.get("current_season", ""),
        year,
        month,
        data.get("map", ""),
        data.get("gamemode", ""),
        data.get("result", ""),
        data.get("length", ""),
        data.get("team1", {}).get("score", ""),
        data.get("team1", {}).get("side", ""),
        data.get("team2", {}).get("score", ""),
        data.get("team2", {}).get("side", ""),
    ]

    player_map = {p["player_name"]: p for p in data.get("team1", {}).get("players", [])}
    player_map.update(
        {p["player_name"]: p for p in data.get("team2", {}).get("players", [])}
    )

    for player_name in config["known_players"]:
        player_info = player_map.get(player_name)
        if player_info:
            hero = player_info.get("hero", "N/A")
            role = HERO_ROLES.get(hero, "Unknown")
            row.extend([hero, role])
        else:
            row.extend(["Not in game", "Not in game"])

    return row


def upload_to_sheet(data):
    """Main function to upload a single game's data to the Google Sheet."""
    print("--- GOOGLE SHEETS UPLOAD ---")
    config = load_config()
    if not config:
        print("└──> Upload failed: config.json not found. Please run setup.py first.")
        return

    creds = get_credentials()
    if not creds:
        print("└──> Upload failed: Could not get Google credentials.")
        return

    sheet = get_sheet(config["sheet_id"], creds)
    if not sheet:
        print("└──> Upload failed: Could not access the worksheet.")
        return

    next_id = get_next_match_id(sheet)
    new_row = flatten_json_for_sheet(data, config, next_id)

    print(f"  - Appending new game data (Match ID: {next_id}): {new_row}")
    try:
        sheet.append_row(new_row)
        print("└──> Successfully uploaded data to Google Sheets.")
    except Exception as e:
        print(f"└──> Upload failed: An error occurred while appending the row: {e}")
