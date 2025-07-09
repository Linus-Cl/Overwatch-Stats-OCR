from generate_templates import run_interactive_template_generator
import os
import json
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
import logging
import sys
from constants import CONFIG_FILE

# --- CONFIGURATION ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
CLIENT_SECRET_FILE = "google_sheets_integration/client_secret.json"
SHEET_TITLE = "Overwatch Stats OCR"


def get_user_players():
    """Prompts the user to enter the player names they want to track."""
    while True:
        logging.info("Prompting for player names.")
        players_input = input(
            "Enter the player names you want to track, separated by commas (e.g., Player1,Player2,Player3): "
        )
        if not players_input:
            logging.warning("No player names entered.")
            print("Please enter at least one player name.")
            continue

        players = [p.strip().upper() for p in players_input.split(",")]

        if players:
            logging.info(f"Tracking the following players: {', '.join(players)}")
            print(f"Tracking the following players: {', '.join(players)}")
            return players
        else:
            logging.warning("Invalid player name input.")
            print("Invalid input. Please try again.")


def get_current_season():
    """Prompts the user to enter the current season number."""
    while True:
        logging.info("Prompting for current season.")
        season_input = input("Enter the current Overwatch season number (e.g., 11): ")
        if season_input.isdigit():
            logging.info(f"Season set to {season_input}.")
            return int(season_input)
        else:
            logging.warning(f"Invalid season input: '{season_input}'.")
            print("Invalid input. Please enter a number.")


def authenticate_and_create_sheet(players):
    """
    Guides the user through authentication, creates a new Google Sheet,
    and returns the sheet ID and CSV download URL.
    """
    try:
        logging.info("Starting Google authentication flow.")
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            logging.info("Successfully saved authentication token to token.json.")
    except FileNotFoundError:
        logging.error(f"'{CLIENT_SECRET_FILE}' not found.")
        print(f"ERROR: '{CLIENT_SECRET_FILE}' not found.")
        print("Please ensure you have completed Part 1 of the SETUP.md guide and placed the file in the correct directory.")
        return None, None
    except Exception as e:
        logging.error("An error occurred during authentication.", exc_info=True)
        print(f"An error occurred during authentication: {e}")
        return None, None

    logging.info("Authentication successful!")
    print("\nAuthentication successful!")

    try:
        client = gspread.authorize(creds)

        try:
            logging.info(f"Checking for existing sheet named '{SHEET_TITLE}'.")
            existing_sheet = client.open(SHEET_TITLE)
            
            print("\n--- WARNING ---")
            print(f"A Google Sheet named '{SHEET_TITLE}' already exists in your Google Drive.")
            print("Proceeding will DELETE the existing sheet and replace it with a new one.")
            
            logging.info("Prompting user to confirm deletion of existing sheet.")
            proceed = input("Are you sure you want to continue? (y/n): ").lower()

            if proceed != 'y':
                logging.info("User aborted setup to prevent sheet deletion.")
                print("Setup aborted by user.")
                return None, None
            
            logging.warning(f"User confirmed deletion. Deleting existing sheet '{SHEET_TITLE}' (ID: {existing_sheet.id}).")
            client.del_spreadsheet(existing_sheet.id)
            print("Existing sheet deleted.")

        except gspread.exceptions.SpreadsheetNotFound:
            logging.info("No existing sheet found. Proceeding to create a new one.")
            pass

        logging.info(f"Creating a new Google Sheet named '{SHEET_TITLE}'.")
        print(f"Creating a new Google Sheet named '{SHEET_TITLE}'...")
        sheet = client.create(SHEET_TITLE)
        worksheet = sheet.get_worksheet(0)

        logging.info("Sharing sheet as 'anyone with link can read'.")
        sheet.share(None, perm_type="anyone", role="reader")

        header = [
            "Match ID", "Date", "Season", "Year", "Month", "Map", "Gamemode",
            "Result", "Game Length", "Team 1 Score", "Team 1 Side",
            "Team 2 Score", "Team 2 Side",
        ]
        for player in players:
            header.append(f"{player} Hero")
            header.append(f"{player} Role")

        logging.info("Appending header row to the new sheet.")
        worksheet.append_row(header)
        print("Google Sheet created and header row added successfully.")

        sheet_id = sheet.id
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={worksheet.id}"
        logging.info(f"Sheet created with ID: {sheet_id}")

        return sheet_id, csv_url

    except Exception as e:
        logging.error("An error occurred while creating the Google Sheet.", exc_info=True)
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
    
    logging.info(f"Configuration saved to '{CONFIG_FILE}'.")
    print(f"\nConfiguration saved to '{CONFIG_FILE}'.")


if __name__ == "__main__":
    # --- Setup Logging for Setup Script ---
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_file = "app.log"
    
    # Setup handler to append to the log file
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(log_formatter)
    
    # Setup handler to print to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    # We don't add the console handler to the root logger to avoid double printing
    # with the standard print() calls for user interaction.
    root_logger.setLevel(logging.INFO)

    logging.info("--- Overwatch Stats OCR Setup Script Started ---")
    print("--- Overwatch Stats OCR Setup ---")

    if os.path.exists(CONFIG_FILE):
        logging.info(f"'{CONFIG_FILE}' already exists.")
        overwrite = input(f"A '{CONFIG_FILE}' already exists. Do you want to overwrite it? (y/n): ").lower()
        if overwrite != "y":
            logging.info("User aborted setup to prevent overwriting config.json.")
            print("Setup aborted.")
            exit()
        logging.warning("User chose to overwrite existing config.json.")

    players = get_user_players()

    logging.info("Prompting user to generate name templates.")
    run_template_gen = input("\nDo you want to automatically generate name templates from a screenshot now? (y/n): ").lower()
    if run_template_gen == "y":
        logging.info("User chose to generate templates.")
        screenshot_path = input("Please enter the full path to your scoreboard screenshot: ")
        logging.info(f"Screenshot path provided: {screenshot_path}")
        run_interactive_template_generator(players, screenshot_path)
    else:
        logging.info("User skipped template generation.")
        print("\nSkipping template generation. Ensure you have manually created templates for all players.")

    season = get_current_season()
    sheet_id, csv_url = authenticate_and_create_sheet(players)

    if sheet_id and csv_url:
        save_config(players, season, sheet_id, csv_url)
        logging.info("--- Setup Complete! ---")
        print("\n--- Setup Complete! ---")
        print("You can now run the main application using 'python run.py'.")
        print("To change the season later, simply edit the 'current_season' value in config.json.")
    else:
        logging.error("--- Setup Failed ---")
        print("\n--- Setup Failed ---")
        print("Please check the error messages above and try again.")
