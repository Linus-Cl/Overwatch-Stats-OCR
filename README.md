# Overwatch Stats OCR

Automatically track your Overwatch match stats using screenshots. This tool uses a hotkey to capture your screen, extracts player statistics using OCR, uploads the data to a private Google Sheet, and provides a web-based dashboard to visualize your performance.

![Web App Screenshot](https://i.imgur.com/example.png) <!-- Placeholder image -->

---

### Core Features

*   **Hotkey Activation:** Press a key to capture and process your latest scoreboard.
*   **Automated OCR:** Extracts map, result, game mode, and player names/heroes from the screenshot.
*   **Google Sheets Integration:** Automatically uploads structured game data to a personal Google Sheet.
*   **Web Dashboard:** A local web application to visualize your stats, hero usage, and performance over time.

### How It Works

1.  **One-Time Setup:** Run a setup script that configures your Google Account and creates the spreadsheet for you.
2.  **Run the Listener:** Start a background script that waits for your hotkey press.
3.  **View Your Stats:** Launch the web application to see your data beautifully visualized.

---

### Getting Started

*   **To install and use the application, please follow our [Setup Guide](SETUP.md).**
*   **For instructions on running the web dashboard, see the [Web App Guide](web_app/README.md).**