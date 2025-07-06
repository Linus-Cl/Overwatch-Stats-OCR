from data_extraction import main_ocr
from google_sheets_integration import uploader

if __name__ == "__main__":
    # 1. Analyze the scoreboard to get the data
    game_data = main_ocr.analyze_scoreboard()

    # 2. If data was successfully extracted, upload it
    if game_data:
        uploader.upload_to_sheet(game_data)
    else:
        print("No data extracted from the scoreboard. Skipping upload.")
