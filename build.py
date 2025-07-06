
import PyInstaller.__main__
import os

# The name of the main script
main_script = "run.py"

# The name of the executable to be created
exe_name = "OverwatchStatsOCR"

# The PyInstaller command
pyinstaller_command = [
    main_script,
    f"--name={exe_name}",
    "--onefile",
    # Using --console for now to make debugging easier
    "--console",
    # Add data files
    f"--add-data=data_extraction/templates{os.pathsep}data_extraction/templates",
    f"--add-data=google_sheets_integration/credentials.json{os.pathsep}google_sheets_integration",
    f"--add-data=constants.py{os.pathsep}.",
]

if __name__ == "__main__":
    print("--- Building executable ---")
    PyInstaller.__main__.run(pyinstaller_command)
    print("--- Build complete ---")
