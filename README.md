# Overwatch Stats OCR

This project allows you to automatically track your Overwatch stats by taking a screenshot of the scoreboard at the end of a game, extracting the data using OCR, and uploading it to a Google Sheet. The data is then displayed on a web-based dashboard.

## Features

- **Automatic Data Extraction:** Uses OCR and template matching to extract game data from a screenshot of the scoreboard.
- **Google Sheets Integration:** Automatically uploads the extracted data to a Google Sheet.
- **Web Dashboard:** A fully interactive web dashboard to visualize your stats.
- **Hotkey Trigger:** Use a configurable hotkey to capture stats at any time.

## Prerequisites

1.  **Python 3:** Make sure you have Python 3 installed on your system.
2.  **Google Cloud Platform Project:** You will need a Google Cloud Platform project with the Google Sheets API enabled.
3.  **Google Service Account:** Create a service account and download the `credentials.json` file.
4.  **Share Google Sheet:** Share your Google Sheet with the service account's email address.

## Installation

1.  **Clone the repository:**

    ```
    git clone https://github.com/your-username/Overwatch-Stats-OCR.git
    cd Overwatch-Stats-OCR
    ```

2.  **Install the dependencies:**

    ```
    pip install -r requirements.txt
    ```

## Configuration

1.  **`google_sheets_integration/credentials.json`:** Place your downloaded `credentials.json` file in this directory.

2.  **`constants.py`:** Open the `constants.py` file and customize the following values:

    - `KNOWN_PLAYERS`: A list of the exact in-game names of the players you want to track.
    - `url`: The download URL of your Google Sheet.
    - `players`: The names to be displayed in the plots on the web dashboard.
    - `HOTKEY`: The key to press to trigger the screenshot and analysis. You can find key names [here](https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key).
    - `SCREENSHOT_PATH`: The path where the screenshot will be saved.

## Running the Application

There are two ways to run the application:

### 1. Running the script directly

```
python run.py
```

This will start the hotkey listener in the console.

### 2. Running the executable

You can create a standalone executable by running the `build.py` script:

```
python build.py
```

This will create an executable file in the `dist` directory. You can then run this file to start the application.

## Usage

1.  Start the application using one of the methods above.
2.  Play an Overwatch game.
3.  At the end of the game, when the scoreboard is visible, press the configured hotkey (default is `F6`).
4.  The application will take a screenshot, analyze it, and upload the data to your Google Sheet.
5.  You can then view your updated stats on the web dashboard.

## Web Dashboard

To run the web dashboard, execute the following command:

```
python web_app/app.py
```

This will start a local web server, and you can view the dashboard by opening your web browser to `http://127.0.0.1:8050`.
