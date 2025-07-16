import cv2
import numpy as np
import os
import pytesseract
import json
import re
import logging
from thefuzz import fuzz
from constants import resource_path, TESSERACT_CMD_PATH, CONFIG_FILE

# If a Tesseract path is specified in constants, set it
if TESSERACT_CMD_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD_PATH

# --- CONFIGURATION ---
HERO_TEMPLATES_PATH = resource_path("data_extraction/templates/hero_templates/")
MAP_TEMPLATES_PATH = resource_path("data_extraction/templates/map_templates/")
NAME_TEMPLATES_PATH = resource_path("data_extraction/templates/name_templates/")

# --- GAMEMODE CONFIG ---
KNOWN_GAMEMODES = ["PUSH", "CONTROL", "HYBRID", "ESCORT", "FLASHPOINT", "CLASH"]
SYMMETRIC_MODES = {"PUSH", "CONTROL", "FLASHPOINT", "CLASH"}
ASYMMETRIC_MODES = {"HYBRID", "ESCORT"}

# --- PARAMETERS ---
MAP_CONFIDENCE_THRESHOLD = 0.80
HERO_DETECTION_THRESHOLD = 0.70
NAME_DETECTION_THRESHOLD = 0.85
RESULT_SIMILARITY_THRESHOLD = 75


def load_known_players():
    """Loads known player names from config.json."""
    if not os.path.exists(CONFIG_FILE):
        logging.error(f"'{CONFIG_FILE}' not found. Please run setup.py first.")
        return []
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        return config.get("known_players", [])


def find_heroes_in_roi(roi, hero_templates, threshold):
    found_heroes = []
    roi_h, roi_w = roi.shape[:2]
    for name, template in hero_templates.items():
        if template is None:
            continue
        templ_h, templ_w = template.shape[:2]
        if templ_h > roi_h or templ_w > roi_w:
            continue
        res = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(res)
        logging.debug(f"  - Checking for {name:<12} | Best match score: {max_val:.2f}")
        if max_val >= threshold:
            if all(
                abs(max_loc[0] - ex) > 20 or abs(max_loc[1] - ey) > 20
                for _, ex, ey, _ in found_heroes
            ):
                found_heroes.append((name, max_loc[0], max_loc[1], max_val))
                logging.info(
                    f"    └──> DETECTED {name} at ({max_loc[0]}, {max_loc[1]}) with score {max_val:.2f}"
                )
    return found_heroes


def find_known_players_in_roi(roi, name_templates, threshold):
    found_players = []
    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    for name, template in name_templates.items():
        if template is None:
            logging.warning(f"  - Skipping template for '{name}' as it could not be loaded.")
            continue
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        w, h = template_gray.shape[::-1]
        res = cv2.matchTemplate(roi_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, _max_loc = cv2.minMaxLoc(res)
        logging.debug(f"  - Checking for '{name:<12}' | Best match score: {max_val:.2f}")
        locs = np.where(res >= threshold)
        detections = [(pt[0], pt[1], res[pt[1], pt[0]]) for pt in zip(*locs[::-1])]
        suppressed_detections = []
        detections.sort(key=lambda x: x[2], reverse=True)
        for x, y, score in detections:
            if not any(
                abs(x - sx) < w * 0.5 and abs(y - sy) < h * 0.5
                for sx, sy, _ in suppressed_detections
            ):
                suppressed_detections.append((x, y, score))
        for x, y, score in suppressed_detections:
            found_players.append({"name": name, "y": y, "x": x, "score": score})
            logging.info(
                f"    └──> DETECTED {name} at ({x}, {y}) with score {score:.2f} (Threshold: {threshold})"
            )
    return found_players


def find_best_map_match(map_roi, map_templates, threshold):
    best_match_score, best_match_name = -1, "Unknown"
    logging.info("--- MAP DETECTION ---")
    for name, template in map_templates.items():
        if template is None:
            continue
        res = cv2.matchTemplate(map_roi, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        logging.debug(f"  - Checking for {name:<20} | Confidence: {max_val:.2f}")
        if max_val > best_match_score:
            best_match_score, best_match_name = max_val, name
    if best_match_score >= threshold:
        logging.info(
            f"└──> Best Match Found: {best_match_name} (Score: {best_match_score:.2f})"
        )
        return best_match_name
    else:
        logging.warning(
            f"└──> No map found above threshold {threshold}. Best attempt was {best_match_name} (Score: {best_match_score:.2f})"
        )
        return "Unknown"


def is_scoreboard_image(image):
    """
    A quick check to see if the image is likely a scoreboard by looking for
    the 'FINAL SCORE' text in a specific region.
    """
    try:
        # A tight ROI around where 'FINAL SCORE' is expected
        # Adjusted Y-coordinates by -50px based on user feedback.
        validator_roi_coords = (1550, 850, 1800, 890)
        roi = image[
            validator_roi_coords[1] : validator_roi_coords[3],
            validator_roi_coords[0] : validator_roi_coords[2],
        ]
        # --- DEBUG: Save the ROI to a file ---
        cv2.imwrite("debug_validator_roi.png", roi)
        logging.info("Saved validation ROI to debug_validator_roi.png")
        # --- END DEBUG ---
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray_roi, config="--psm 7").strip().upper()
        confidence = fuzz.partial_ratio("FINAL SCORE", text)

        logging.info("--- SCOREBOARD VALIDATION ---")
        logging.info(f"  - Validator text found: '{text}'")
        logging.info(f"  - 'FINAL SCORE' confidence: {confidence}%")

        return confidence > 80
    except Exception as e:
        logging.error("Scoreboard validation check failed.", exc_info=True)
        return False


def analyze_scoreboard(scoreboard_img_path):
    """
    Analyzes an Overwatch scoreboard screenshot to extract game data.
    """
    if not os.path.exists(scoreboard_img_path):
        logging.error(f"Scoreboard image not found at {scoreboard_img_path}")
        return None
    scoreboard_img = cv2.imread(scoreboard_img_path)
    if scoreboard_img is None:
        logging.error(f"Could not read image file {scoreboard_img_path}")
        return None

    if not is_scoreboard_image(scoreboard_img):
        logging.warning("Validation failed. Image is not a valid scoreboard. Aborting analysis.")
        return None
    logging.info("Validation successful. Proceeding with full analysis.")

    KNOWN_PLAYERS = load_known_players()
    if not KNOWN_PLAYERS:
        return None

    map_templates = {
        os.path.basename(p).split(".")[0]: cv2.imread(os.path.join(MAP_TEMPLATES_PATH, p))
        for p in os.listdir(MAP_TEMPLATES_PATH) if p.endswith(".png")
    }
    hero_templates = {
        os.path.basename(p).split(".")[0]: cv2.imread(os.path.join(HERO_TEMPLATES_PATH, p))
        for p in os.listdir(HERO_TEMPLATES_PATH) if p.endswith(".png")
    }
    name_templates = {
        name: cv2.imread(os.path.join(NAME_TEMPLATES_PATH, f"{name.lower()}.png"))
        for name in KNOWN_PLAYERS
    }

    roi_coords = {
        "map": (1515, 291, 2205, 738), "result": (1556, 773, 1770, 847),
        "game_details": (1550, 845, 1950, 1050), "team1_names": (479, 336, 713, 743),
        "team1_heroes": (390, 328, 477, 744), "team2_names": (477, 868, 778, 1279),
        "team2_heroes": (385, 849, 483, 1288),
    }

    ROI_MAP = scoreboard_img[roi_coords["map"][1]:roi_coords["map"][3], roi_coords["map"][0]:roi_coords["map"][2]]
    ROI_HEROES_1 = scoreboard_img[roi_coords["team1_heroes"][1]:roi_coords["team1_heroes"][3], roi_coords["team1_heroes"][0]:roi_coords["team1_heroes"][2]]
    ROI_HEROES_2 = scoreboard_img[roi_coords["team2_heroes"][1]:roi_coords["team2_heroes"][3], roi_coords["team2_heroes"][0]:roi_coords["team2_heroes"][2]]
    ROI_RESULT = scoreboard_img[roi_coords["result"][1]:roi_coords["result"][3], roi_coords["result"][0]:roi_coords["result"][2]]
    ROI_GAME_DETAILS = scoreboard_img[roi_coords["game_details"][1]:roi_coords["game_details"][3], roi_coords["game_details"][0]:roi_coords["game_details"][2]]
    ROI_TEAM1_NAMES = scoreboard_img[roi_coords["team1_names"][1]:roi_coords["team1_names"][3], roi_coords["team1_names"][0]:roi_coords["team1_names"][2]]
    ROI_TEAM2_NAMES = scoreboard_img[roi_coords["team2_names"][1]:roi_coords["team2_names"][3], roi_coords["team2_names"][0]:roi_coords["team2_names"][2]]

    detected_map = find_best_map_match(ROI_MAP, map_templates, MAP_CONFIDENCE_THRESHOLD)

    logging.info("--- TEAM 1 HERO DETECTION ---")
    team1_heroes_found = find_heroes_in_roi(ROI_HEROES_1, hero_templates, HERO_DETECTION_THRESHOLD)
    logging.info("--- TEAM 2 HERO DETECTION ---")
    team2_heroes_found = find_heroes_in_roi(ROI_HEROES_2, hero_templates, HERO_DETECTION_THRESHOLD)
    team1_heroes_sorted = sorted(team1_heroes_found, key=lambda item: item[2])
    team2_heroes_sorted = sorted(team2_heroes_found, key=lambda item: item[2])

    logging.info("--- TEXT RECOGNITION (OCR for Game Result) ---")
    match_result = "UNKNOWN"
    try:
        result_text = pytesseract.image_to_string(ROI_RESULT, config="--psm 7").strip().upper()
        scores = {
            "VICTORY": fuzz.ratio(result_text, "VICTORY"), "DEFEAT": fuzz.ratio(result_text, "DEFEAT"),
            "DRAW": fuzz.ratio(result_text, "DRAW"),
        }
        logging.info(f"  - Raw OCR: '{result_text}' | Scores: {scores}")
        if scores:
            best_match = max(scores, key=scores.get)
            if scores[best_match] >= RESULT_SIMILARITY_THRESHOLD:
                match_result = best_match
        logging.info(f"  - Game Result Detected: {match_result}")
    except Exception:
        logging.error("OCR FAILED for result.", exc_info=True)
        match_result = "OCR_FAILED"

    logging.info("--- TEXT RECOGNITION (OCR for Game Details) ---")
    detected_gamemode, game_length, game_date = "Unknown", "Unknown", "Unknown"
    team1_score, team2_score = -1, -1
    try:
        gray_details = cv2.cvtColor(ROI_GAME_DETAILS, cv2.COLOR_BGR2GRAY)
        details_text = pytesseract.image_to_string(gray_details, config="--psm 6").strip().upper()
        logging.debug(f"  - Raw OCR for Details:\n---\n{details_text}\n---")
        lines = [line.strip() for line in details_text.split("\n") if line.strip()]
        for line in lines:
            if "FINAL SCORE" in line:
                score_match = re.search(r"(\d+)\s*VS\s*(\d+)", line)
                if score_match:
                    team1_score, team2_score = int(score_match.group(1)), int(score_match.group(2))
            elif "GAME MODE" in line:
                value = line.split(":", 1)[-1]
                for mode in KNOWN_GAMEMODES:
                    if mode in value:
                        detected_gamemode = mode
                        break
            elif "GAME LENGTH" in line:
                game_length = line.split(":", 1)[-1].strip()
            elif "DATE" in line:
                game_date = line.split(":", 1)[-1].strip()
        logging.info(f"  - Gamemode: {detected_gamemode}, Score: {team1_score}-{team2_score}, Length: {game_length}, Date: {game_date}")
    except Exception:
        logging.error("OCR FAILED for game details.", exc_info=True)

    team1_side, team2_side = "unknown", "unknown"
    if detected_gamemode in SYMMETRIC_MODES:
        team1_side, team2_side = "attack", "attack"
    elif detected_gamemode in ASYMMETRIC_MODES and team1_score != -1:
        if team1_score > team2_score: team1_side, team2_side = "attack", "defense"
        elif team2_score > team1_score: team1_side, team2_side = "defense", "attack"
        elif team1_score == team2_score:
            if match_result == "VICTORY": team1_side, team2_side = "defense", "attack"
            elif match_result == "DEFEAT": team1_side, team2_side = "attack", "defense"

    logging.info("--- PLAYER NAME DETECTION (Template Matching) ---")
    logging.info("--- Detecting in Team 1 ---")
    team1_players_found = find_known_players_in_roi(ROI_TEAM1_NAMES, name_templates, NAME_DETECTION_THRESHOLD)
    logging.info("--- Detecting in Team 2 ---")
    team2_players_found = find_known_players_in_roi(ROI_TEAM2_NAMES, name_templates, NAME_DETECTION_THRESHOLD)
    team1_players_sorted = sorted(team1_players_found, key=lambda p: p["y"])
    team2_players_sorted = sorted(team2_players_found, key=lambda p: p["y"])

    logging.info("--- VALIDATING DATA ---")
    known_players_found = any(p["name"] in KNOWN_PLAYERS for p in team1_players_sorted) or any(p["name"] in KNOWN_PLAYERS for p in team2_players_sorted)
    if detected_map == "Unknown" or match_result == "UNKNOWN" or not known_players_found:
        logging.warning("--- VALIDATION FAILED ---")
        if detected_map == "Unknown": logging.warning("Reason: Map could not be determined.")
        if match_result == "UNKNOWN": logging.warning("Reason: Match result could not be determined.")
        if not known_players_found: logging.warning("Reason: No known players were found.")
        logging.warning("--- Analysis aborted, no data will be returned. ---")
        return None
    logging.info("--- Validation successful, proceeding with data assembly. ---")

    final_data = {
        "map": detected_map, "gamemode": detected_gamemode, "result": match_result,
        "date": game_date, "length": game_length,
        "team1": {"score": team1_score, "side": team1_side, "players": []},
        "team2": {"score": team2_score, "side": team2_side, "players": []},
    }

    logging.info("--- Pairing Players with Heroes ---")
    available_heroes_1 = list(team1_heroes_sorted)
    for player in team1_players_sorted:
        if not available_heroes_1: break
        closest_hero = min(available_heroes_1, key=lambda h: abs(h[2] - player["y"]))
        final_data["team1"]["players"].append({"player_name": player["name"], "hero": closest_hero[0].title()})
        available_heroes_1.remove(closest_hero)
        logging.debug(f"  - Team 1: Paired {player['name']} (y={player['y']}) with {closest_hero[0]} (y={closest_hero[2]}) ")

    available_heroes_2 = list(team2_heroes_sorted)
    for player in team2_players_sorted:
        if not available_heroes_2: break
        closest_hero = min(available_heroes_2, key=lambda h: abs(h[2] - player["y"]))
        final_data["team2"]["players"].append({"player_name": player["name"], "hero": closest_hero[0].title()})
        available_heroes_2.remove(closest_hero)
        logging.debug(f"  - Team 2: Paired {player['name']} (y={player['y']}) with {closest_hero[0]} (y={closest_hero[2]}) ")

    logging.info("--- EXTRACTION COMPLETE ---")
    logging.debug(f"Final structured data: {json.dumps(final_data, indent=2)}")
    return final_data
