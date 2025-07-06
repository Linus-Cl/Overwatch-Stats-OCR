import PyInstaller.__main__
import os

# -----------------------------------------------------------------------------
# --- CONFIGURATION ---
# -----------------------------------------------------------------------------

# The name for the final executable
EXE_NAME = "OverwatchStatsOCR"

# The main script that is the entry point of your application
MAIN_SCRIPT = "run.py"

# List of data files and directories to include.
# Format: "path/on/disk:path/in/executable"
# Use os.pathsep to separate multiple entries on the same line.
DATA_TO_INCLUDE = [
    # All hero, map, and name templates
    f"data_extraction/templates{os.pathsep}data_extraction/templates",
    # The client secret for Google Sheets
    f"google_sheets_integration/client_secret.json{os.pathsep}google_sheets_integration",
]

# PyInstaller options
# For a full list of options, see the PyInstaller documentation
PYINSTALLER_OPTIONS = [
    "--noconfirm",  # Don't ask for confirmation before overwriting
    "--onefile",  # Create a single file executable
    "--windowed",  # No console window when the app runs
    # Add any other required hidden imports if PyInstaller fails to find them
    # '--hidden-import=your_hidden_module',
]

# -----------------------------------------------------------------------------
# --- BUILD SCRIPT ---
# -----------------------------------------------------------------------------


def build():
    """
    Runs the PyInstaller build process.
    """
    command = [
        MAIN_SCRIPT,
        f"--name={EXE_NAME}",
    ]
    command.extend(PYINSTALLER_OPTIONS)

    # Add data files
    for item in DATA_TO_INCLUDE:
        command.append(f"--add-data={item}")

    print("--- Running PyInstaller with the following command ---")
    # Print the command in a readable format
    print("pyinstaller " + " ".join(f'"{c}"' if " " in c else c for c in command))
    print("----------------------------------------------------")

    try:
        PyInstaller.__main__.run(command)
        print("\n--- Build successful! ---")
        print(f"Executable created at: {os.path.join('dist', EXE_NAME + '.exe')}")
        print("-------------------------")
    except Exception as e:
        print("\n--- BUILD FAILED ---")
        print(f"An error occurred during the build process: {e}")
        print("--------------------")


if __name__ == "__main__":
    build()