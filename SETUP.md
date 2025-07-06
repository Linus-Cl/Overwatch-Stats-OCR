# Complete Installation and Setup Guide

Welcome! This guide will walk you through every step needed to get the Overwatch Stats OCR tool running on your machine.

---

### **Part 1: Google Cloud Prerequisites (Manual Setup)**

This part is done once in your web browser. It's necessary to give the application permission to create and write to a Google Sheet on your behalf.

1.  **Create a Google Cloud Project:**
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   If you don't have a project, create a new one. You can name it whatever you like (e.g., "Overwatch OCR Stats").

2.  **Enable the Required APIs:**
    *   In your project's dashboard, navigate to the **"APIs & Services"** > **"Library"**.
    *   Search for and **enable** the **Google Sheets API**.
    *   Search for and **enable** the **Google Drive API**.

3.  **Configure the OAuth Consent Screen:**
    *   In "APIs & Services", go to the **"OAuth consent screen"**.
    *   Select **"External"** for the User Type and click **"Create"**.
    *   On the next page:
        *   **App name:** Give your app a name (e.g., "Overwatch Stats OCR").
        *   **User support email:** Select your email address.
        *   **Developer contact information:** Enter your email address again.
    *   Click **"Save and Continue"** through the "Scopes" and "Optional Info" pages.
    *   On the "Test users" page, click **"+ Add Users"** and add the Google email address you will be using. This is a critical step.

4.  **Create Your Credentials:**
    *   Navigate to **"APIs & Services"** > **"Credentials"**.
    *   Click **"+ Create Credentials"** at the top and select **"OAuth client ID"**.
    *   For the **"Application type"**, choose **"Desktop app"**.
    *   Give it a name (e.g., "Overwatch OCR Client").
    *   Click **"Create"**.

5.  **Download Your Client Secret File:**
    *   A confirmation popup will appear. Click the **"DOWNLOAD JSON"** button.
    *   This will download a file with a name like `client_secret_[...].json`.
    *   **Rename this file to `client_secret.json`**.

---

### **Part 2: Local Project Setup**

Now that you have your credentials, you can set up the project on your computer.

1.  **Clone the Repository:**
    *   If you have git, run: `git clone https://github.com/your-username/Overwatch-Stats-OCR.git`
    *   Alternatively, download the project as a ZIP file and extract it.

2.  **Place Your Credentials File:**
    *   Take the `client_secret.json` file you downloaded and renamed.
    *   Place it inside the `google_sheets_integration/` directory. The final path should be `google_sheets_integration/client_secret.json`.

3.  **Install Dependencies:**
    *   Open your terminal or command prompt in the project's root directory.
    *   Run the following command to install all the necessary Python libraries:
        ```
        pip install -r requirements.txt
        ```

---

### **Part 3: Automated Configuration**

This is the final setup step. This script will connect to your Google Account, create the spreadsheet, and save your configuration.

1.  **Run the Setup Script:**
    *   In your terminal, run:
        ```
        python setup.py
        ```
2.  **Follow the Prompts:**
    *   The script will first ask you to enter the player names you want to track.
    *   Next, it will automatically open a new tab in your web browser, asking you to sign in to your Google Account and grant permission. **Please approve these permissions.**
    *   Once you grant permission, the script will create the Google Sheet and a local `config.json` file.

---

### **Part 4: Running the OCR Tool**

You're all set! Now you can run the main application.

1.  **Start the Hotkey Listener:**
    *   In your terminal, run:
        ```
        python run.py
        ```
2.  **Confirmation:**
    *   You will see a message confirming that the script is running and waiting for the hotkey press (F6 by default).
    *   You can now press the hotkey in-game when the scoreboard is visible to capture and upload your stats.
    *   To stop the listener, press `Ctrl+C` in the terminal.
