# Overwatch Stats OCR

Automatically track your Overwatch match stats using screenshots. This tool uses a hotkey to capture your screen, extracts player statistics using OCR, uploads the data to a private Google Sheet, and provides a web-based dashboard to visualize your performance.

![Web App Screenshot](https://i.imgur.com/example.png) <!-- Placeholder image -->

---

## Installation & Usage

1.  **Download the Application:**
    -   Go to the [**GitHub Releases Page**](https://github.com/your-username/your-repo/releases) and download the latest `.zip` file for your operating system (macOS or Windows).
    -   *(Please replace the link above with your actual releases page URL after you create it!)*

2.  **Unzip and Run:**
    -   Extract the contents of the `.zip` file.
    -   Run the application:
        -   **On Windows:** Double-click `OverwatchStatsOCR.exe`.
        -   **On macOS:** Double-click `OverwatchStatsOCR.app`.

3.  **First-Time Setup:**
    -   The first time you launch, a setup window will appear. It will guide you through entering your player names and authenticating with Google to create your private spreadsheet.

4.  **Permissions (macOS Only):**
    -   On macOS, you **must** grant **Accessibility** and **Screen Recording** permissions when prompted. You can manage these in `System Settings > Privacy & Security`.

5.  **How to Use:**
    -   With the app running (look for the icon in your system tray), simply press the **F6** key when your Overwatch scoreboard is visible.
    -   The app will automatically capture, analyze, and upload the stats.
    -   Right-click the tray icon to open your local Web Dashboard and view your stats.

---

### For Developers

If you wish to contribute or run the project from source, please see the original [Setup Guide](SETUP.md).
