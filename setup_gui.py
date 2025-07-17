import sys
import os
import json
import subprocess
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
import logging
import multiprocessing

from PyQt6.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFileDialog, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from generate_templates import run_interactive_template_generator

# --- Constants ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
CLIENT_SECRET_FILE = "google_sheets_integration/client_secret.json"
SHEET_TITLE = "Overwatch Stats OCR"

# --- Worker Threads ---

class Worker(QObject):
    """A generic worker for running tasks in a separate thread."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, task, **kwargs):
        super().__init__()
        self.task = task
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.task(**self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            logging.error(f"Error in worker thread for task '{self.task.__name__}': {e}", exc_info=True)
            self.error.emit(str(e))

# --- Task Functions (to be run in worker threads) ---

def template_generation_task(players, screenshot_path):
    """
    This function now runs the template generator in a separate process
    to avoid issues with bundled executables and GUI library conflicts.
    """
    try:
        # Using multiprocessing to run the OpenCV GUI in a completely separate process
        process = multiprocessing.Process(
            target=run_interactive_template_generator,
            args=(players, screenshot_path)
        )
        process.start()
        process.join() # Wait for the process to complete

        if process.exitcode != 0:
            raise Exception(f"Template generator process exited with code {process.exitcode}. Check logs for details.")
        
        return True
    except Exception as e:
        # Log the full exception details
        logging.error(f"Failed to run template generator: {e}", exc_info=True)
        # Raise a new exception with a user-friendly message
        raise Exception(f"Template generator failed. Details: {e}")

def google_auth_task():
    if not os.path.exists(CLIENT_SECRET_FILE):
        raise FileNotFoundError(f"'{CLIENT_SECRET_FILE}' not found. Please ensure it is in the correct directory.")
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    return creds

# --- Wizard Pages ---

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome")
        self.setSubTitle("This wizard will guide you through the one-time setup for Overwatch Stats OCR.")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Click 'Next' to begin."))
        self.setLayout(layout)

class PlayersPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Player Names")
        self.setSubTitle("Enter the player names you want to track, separated by commas.")
        layout = QVBoxLayout()
        self.players_entry = QLineEdit()
        self.players_entry.setPlaceholderText("PLAYER1,PLAYER2,PLAYER3")
        layout.addWidget(self.players_entry)
        self.setLayout(layout)

    def validatePage(self):
        players = [p.strip() for p in self.players_entry.text().split(",") if p.strip()]
        if not players:
            QMessageBox.warning(self, "Invalid Input", "Please enter at least one player name.")
            return False
        self.wizard().config_data['known_players'] = [p.upper() for p in players]
        return True

class TemplatesPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.is_complete = False
        self.setTitle("Name Templates")
        self.setSubTitle("This step is required. Select a scoreboard screenshot to generate name templates.")
        layout = QVBoxLayout()
        self.status_label = QLabel("Status: Pending")
        self.generate_button = QPushButton("Select Screenshot & Generate")
        self.generate_button.clicked.connect(self.run_generator)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def run_generator(self):
        screenshot_path, _ = QFileDialog.getOpenFileName(self, "Select Screenshot", "", "Image Files (*.png *.jpg *.jpeg)")
        if not screenshot_path:
            return

        QMessageBox.information(self, "Heads Up", "The template generator will now run in a separate window. This setup wizard will wait until it is complete.")
        self.generate_button.setEnabled(False)
        self.status_label.setText("Status: Running template generator...")

        self.thread = QThread()
        self.worker = Worker(template_generation_task, players=self.wizard().config_data['known_players'], screenshot_path=screenshot_path)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.thread.start()

    def on_finished(self, result):
        self.status_label.setText("Status: Templates generated successfully!")
        self.is_complete = True
        self.completeChanged.emit() # Notifies the wizard to update Next/Finish button state
        self.thread.quit()
        self.thread.wait()

    def on_error(self, error_msg):
        self.status_label.setText(f"Status: Error! {error_msg}")
        QMessageBox.critical(self, "Template Generation Failed", error_msg)
        self.generate_button.setEnabled(True)
        self.thread.quit()
        self.thread.wait()

    def isComplete(self):
        return self.is_complete

class GoogleSheetsPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.is_complete = False
        self.creds = None
        self.setTitle("Google Sheets Integration")
        self.setSubTitle("Authenticate with your Google account to create the spreadsheet.")
        layout = QVBoxLayout()
        self.status_label = QLabel("Status: Pending")
        self.auth_button = QPushButton("Authenticate with Google")
        self.auth_button.clicked.connect(self.run_auth)
        layout.addWidget(self.auth_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def run_auth(self):
        self.auth_button.setEnabled(False)
        self.status_label.setText("Status: Waiting for browser authentication...")
        self.thread = QThread()
        self.worker = Worker(google_auth_task)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_auth_finished)
        self.worker.error.connect(self.on_auth_error)
        self.thread.start()

    def on_auth_finished(self, creds):
        self.creds = creds
        self.thread.quit()
        self.thread.wait()
        self.status_label.setText("Authentication successful! Now creating spreadsheet...")
        self.create_sheet()

    def on_auth_error(self, error_msg):
        self.status_label.setText(f"Status: Authentication Failed! {error_msg}")
        QMessageBox.critical(self, "Authentication Failed", error_msg)
        self.auth_button.setEnabled(True)
        self.thread.quit()
        self.thread.wait()

    def create_sheet(self):
        try:
            client = gspread.authorize(self.creds)
            try:
                existing_sheet = client.open(SHEET_TITLE)
                reply = QMessageBox.question(self, "Sheet Exists", f"A sheet named '{SHEET_TITLE}' already exists. Do you want to delete it and create a new one?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    raise Exception("User aborted to prevent sheet deletion.")
                client.del_spreadsheet(existing_sheet.id)
            except gspread.exceptions.SpreadsheetNotFound:
                pass

            sheet = client.create(SHEET_TITLE)
            worksheet = sheet.get_worksheet(0)
            sheet.share(None, perm_type="anyone", role="reader")
            header = ["Match ID", "Date", "Season", "Year", "Month", "Map", "Gamemode", "Result", "Game Length", "Team 1 Score", "Team 1 Side", "Team 2 Score", "Team 2 Side"]
            for player in self.wizard().config_data['known_players']:
                header.extend([f"{player} Hero", f"{player} Role"])
            worksheet.append_row(header)

            self.wizard().config_data['sheet_id'] = sheet.id
            self.wizard().config_data['sheet_csv_url'] = f"https://docs.google.com/spreadsheets/d/{sheet.id}/export?format=csv&gid={worksheet.id}"
            
            # Save credentials
            creds_path = os.path.join(os.path.expanduser("~"), "OverwatchStatsOCR_Data", "token.json")
            os.makedirs(os.path.dirname(creds_path), exist_ok=True)
            with open(creds_path, "w") as token:
                token.write(self.creds.to_json())

            self.status_label.setText("Status: Spreadsheet created successfully!")
            self.is_complete = True
            self.completeChanged.emit()
        except Exception as e:
            QMessageBox.critical(self, "Sheet Creation Failed", str(e))
            self.status_label.setText(f"Status: Sheet creation failed! {e}")
            self.auth_button.setEnabled(True)

    def isComplete(self):
        return self.is_complete

class FinishPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Setup Complete")
        self.setSubTitle("Configuration has been saved. The application will now start.")

class SetupWizard(QWizard):
    def __init__(self, on_complete_callback):
        super().__init__()
        self.on_complete_callback = on_complete_callback
        self.config_data = {}
        self.setWindowTitle("Overwatch Stats OCR - Setup")

        self.addPage(WelcomePage())
        self.addPage(PlayersPage())
        self.addPage(TemplatesPage())
        self.addPage(GoogleSheetsPage())
        self.addPage(FinishPage())

    def accept(self):
        # This is called when the user clicks "Finish"
        config_path = os.path.join(os.path.expanduser("~"), "OverwatchStatsOCR_Data", "config.json")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(self.config_data, f, indent=4)
        
        logging.info(f"Configuration successfully saved to {config_path}")
        self.on_complete_callback(self.config_data)
        super().accept()

def run_setup_flow(on_complete_callback):
    app = QApplication.instance()  # Check if an instance already exists
    if not app:
        app = QApplication(sys.argv)
    
    wizard = SetupWizard(on_complete_callback)
    wizard.exec() # Use exec() for a modal dialog behavior

if __name__ == '__main__':
    # --- Fix for multiprocessing when bundled in an executable ---
    multiprocessing.freeze_support()
    # --- End of Fix ---

    # --- Fix for Qt Platform Plugin Error ---
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

    logging.basicConfig(level=logging.INFO)
    def on_complete(data):
        print("Setup completed with data:", data)
    run_setup_flow(on_complete)