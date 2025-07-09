import PyInstaller.__main__
import os
import sys

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
# IMPORTANT: This build script assumes that you have already run `setup.py`
# at least once to generate `config.json` and `token.json`.
DATA_TO_INCLUDE = [
    # All hero, map, and name templates
    f"data_extraction/templates{os.pathsep}data_extraction/templates",
    # The client secret for Google Sheets (if it exists)
    f"google_sheets_integration/client_secret.json{os.pathsep}google_sheets_integration",
    # The entire web app directory
    f"web_app{os.pathsep}web_app",
    # The generated config and token files
    f"{os.path.abspath('config.json')}{os.pathsep}.",
    f"{os.path.abspath('token.json')}{os.pathsep}.",
]

# PyInstaller options
# For a full list of options, see the PyInstaller documentation
PYINSTALLER_OPTIONS = [
    "--noconfirm",  # Don't ask for confirmation before overwriting
    "--onedir",     # Create a directory bundle (best for debugging)
    "--windowed",   # Use a windowed app bundle for macOS (no console)
    # Add any other required hidden imports if PyInstaller fails to find them
    '--hidden-import=pynput.keyboard._darwin',
    '--hidden-import=pynput.mouse._darwin',
    '--hidden-import=pystray._dummy',
]

# -----------------------------------------------------------------------------
# --- BUILD SCRIPT ---
# -----------------------------------------------------------------------------


def build():
    """
    Runs the PyInstaller build process.
    
    This script should be run AFTER `setup.py` has been completed,
    as it requires `config.json` and `token.json` to be present.
    """
    # Pre-build checks
    if not os.path.exists('config.json') or not os.path.exists('token.json'):
        print("--- BUILD PRE-CHECK FAILED ---")
        print("Error: 'config.json' or 'token.json' not found.")
        print("Please run 'python setup.py' to generate these files before building.")
        print("------------------------------")
        sys.exit(1)

    command = [
        MAIN_SCRIPT,
        f"--name={EXE_NAME}",
    ]
    command.extend(PYINSTALLER_OPTIONS)

    # Add data files
    for item in DATA_TO_INCLUDE:
        # Ensure the source file/dir exists before adding it
        source_path = item.split(os.pathsep)[0]
        if os.path.exists(source_path):
            command.append(f"--add-data={item}")
        else:
            print(f"Warning: Data file/directory not found, skipping: {source_path}")

    print("--- Running PyInstaller with the following command ---")
    # Print the command in a readable format
    print("pyinstaller " + " ".join(f'"{c}"' if " " in c else c for c in command))
    print("----------------------------------------------------")

    try:
        PyInstaller.__main__.run(command)
        print("\n--- Build successful! ---")
        # The output path depends on the OS
        exe_path = os.path.join('dist', EXE_NAME)
        if sys.platform == 'win32':
            exe_path += '.exe'
        print(f"Executable created at: {exe_path}")
        print("-------------------------")
    except Exception as e:
        print("\n--- BUILD FAILED ---")
        print(f"An error occurred during the build process: {e}")
        print("--------------------")


if __name__ == "__main__":
    build()
