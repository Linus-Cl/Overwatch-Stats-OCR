from generate_templates import run_interactive_template_generator
import os
import json
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow

# --- CONFIGURATION ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
CLIENT_SECRET_FILE = "google_sheets_integration/client_secret.json"
CONFIG_FILE = "config.json"
SHEET_TITLE = "Overwatch Stats OCR"


def get_user_players():
    """Prompts the user to enter the player names they want to track."""
    while True:
        players_input = input(
            "Enter the player names you want to track, separated by commas (e.g., Player1,Player2,Player3): "
        )
        if not players_input:
            print("Please enter at least one player name.")
            continue

        players = [p.strip().upper() for p in players_input.split(",")]

        if players:
            print(f"Tracking the following players: {', '.join(players)}")
            return players
        else:
            print("Invalid input. Please try again.")


def get_current_season():
    """Prompts the user to enter the current season number."""
    while True:
        season_input = input("Enter the current Overwatch season number (e.g., 11): ")
        if season_input.isdigit():
            return int(season_input)
        else:
            print("Invalid input. Please enter a number.")


def authenticate_and_create_sheet(players):
    """
    Guides the user through authentication, creates a new Google Sheet,
    and returns the sheet ID and CSV download URL.
    """
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
    except FileNotFoundError:
        print(f"ERROR: '{CLIENT_SECRET_FILE}' not found.")
        print(
            "Please ensure you have completed Part 1 of the SETUP.md guide and placed the file in the correct directory."
        )
        return None, None
    except Exception as e:
        print(f"An error occurred during authentication: {e}")
        return None, None

    print("\nAuthentication successful!")

    try:
        client = gspread.authorize(creds)

        # --- Check for existing sheet before creating a new one ---
        try:
            existing_sheet = client.open(SHEET_TITLE)
            print("\n--- WARNING ---")
            print(f"A Google Sheet named '{SHEET_TITLE}' already exists in your Google Drive.")
            print("Proceeding will DELETE the existing sheet and replace it with a new one.")
            proceed = input("Are you sure you want to continue? (y/n): ").lower()
            if proceed != 'y':
                print("Setup aborted by user.")
                return None, None
            
            print(f"Deleting existing sheet '{SHEET_TITLE}'...")
            client.del_spreadsheet(existing_sheet.id)
            print("Existing sheet deleted.")

        except gspread.exceptions.SpreadsheetNotFound:
            # This is the expected path if the sheet doesn't exist.
            pass

        print(f"Creating a new Google Sheet named '{SHEET_TITLE}'...")
        sheet = client.create(SHEET_TITLE)
        worksheet = sheet.get_worksheet(0)

        sheet.share(None, perm_type="anyone", role="reader")

        # Create the header row in English
        header = [
            "Match ID",
            "Date",
            "Season",
            "Year",
            "Month",
            "Map",
            "Gamemode",
            "Result",
            "Game Length",
            "Team 1 Score",
            "Team 1 Side",
            "Team 2 Score",
            "Team 2 Side",
        ]
        for player in players:
            header.append(f"{player} Hero")
            header.append(f"{player} Role")

        worksheet.append_row(header)
        print("Google Sheet created and header row added successfully.")

        sheet_id = sheet.id
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={worksheet.id}"

        return sheet_id, csv_url

    except Exception as e:
        print(f"An error occurred while creating the Google Sheet: {e}")
        return None, None



def save_config(players, season, sheet_id, csv_url):
    """Saves the user's configuration to config.json."""
    config_data = {
        "known_players": players,
        "current_season": season,
        "sheet_id": sheet_id,
        "sheet_csv_url": csv_url,
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)

    print(f"\nConfiguration saved to '{CONFIG_FILE}'.")


if __name__ == "__main__":
    print("--- Overwatch Stats OCR Setup ---")

    if os.path.exists(CONFIG_FILE):
        overwrite = input(
            f"A '{CONFIG_FILE}' already exists. Do you want to overwrite it? (y/n): "
        ).lower()
        if overwrite != "y":
            print("Setup aborted.")
            exit()

    players = get_user_players()

    # --- New Template Generation Step ---
    run_template_gen = input(
        "\nDo you want to automatically generate name templates from a screenshot now? (y/n): "
    ).lower()
    if run_template_gen == "y":
        screenshot_path = input(
            "Please enter the full path to your scoreboard screenshot: "
        )
        run_interactive_template_generator(players, screenshot_path)
    else:
        print(
            "\nSkipping template generation. Ensure you have manually created templates for all players."
        )

    season = get_current_season()
    sheet_id, csv_url = authenticate_and_create_sheet(players)

    if sheet_id and csv_url:
        save_config(players, season, sheet_id, csv_url)
        print("\n--- Setup Complete! ---")
        print("You can now run the main application using 'python run.py'.")
        print(
            "To change the season later, simply edit the 'current_season' value in config.json."
        )
    else:
        print("\n--- Setup Failed ---")
        print("Please check the error messages above and try again.")