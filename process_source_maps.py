
import os
import cv2
import logging

import numpy as np

# --- CONFIGURATION ---
SOURCE_DIR = "pics"
DEST_DIR = "data_extraction/templates/map_templates"
LOG_LEVEL = logging.INFO

# --- SCRIPT ---

def setup_logging():
    """Sets up basic logging."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def process_maps():
    """
    Converts all .tif map images from the source directory to .png format
    in the destination directory, ready for feature matching.
    """
    setup_logging()
    logging.info("--- Starting Map Template Processing ---")

    if not os.path.exists(SOURCE_DIR):
        logging.error(f"Source directory '{SOURCE_DIR}' not found. Please ensure it exists in the project root.")
        return

    # Ensure the destination directory exists
    os.makedirs(DEST_DIR, exist_ok=True)

    # --- Clean up old templates ---
    logging.info(f"Cleaning old templates from '{DEST_DIR}'...")
    for file in os.listdir(DEST_DIR):
        if file.endswith(".png"):
            os.remove(os.path.join(DEST_DIR, file))
    logging.info("Cleanup complete.")

    # --- Process new templates ---
    map_folders = [d for d in os.listdir(SOURCE_DIR) if os.path.isdir(os.path.join(SOURCE_DIR, d))]
    
    total_processed = 0
    for map_name in map_folders:
        map_folder_path = os.path.join(SOURCE_DIR, map_name)
        image_files = [f for f in os.listdir(map_folder_path) if f.lower().endswith(".tif")]
        
        if not image_files:
            logging.warning(f"No .tif images found in '{map_folder_path}'. Skipping.")
            continue

        logging.info(f"Processing map: {map_name} ({len(image_files)} images)")
        
        image_counter = 1
        for tif_file in image_files:
            try:
                source_path = os.path.join(map_folder_path, tif_file)
                
                # Robustly read the image file to handle special characters
                with open(source_path, 'rb') as f:
                    chunk = f.read()
                img_array = np.frombuffer(chunk, dtype=np.uint8)
                image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                if image is None:
                    logging.warning(f"  - Could not read image: {source_path}. Skipping.")
                    continue
                
                # Construct the new filename
                new_filename = f"{map_name.lower()}_{image_counter}.png"
                dest_path = os.path.join(DEST_DIR, new_filename)
                
                # Save as .png
                cv2.imwrite(dest_path, image)
                logging.info(f"  - Converted and saved to '{dest_path}'")
                
                image_counter += 1
                total_processed += 1

            except Exception as e:
                logging.error(f"  - Failed to process file {tif_file}: {e}", exc_info=True)

    logging.info(f"--- Processing Complete. Total images converted: {total_processed} ---")

if __name__ == "__main__":
    process_maps()
