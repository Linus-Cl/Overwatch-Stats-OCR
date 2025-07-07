import cv2
import os
import numpy as np

# --- CONFIGURATION ---
NAME_TEMPLATES_PATH = "data_extraction/templates/name_templates/"
WINDOW_NAME = "Template Generator"

# --- STATE VARIABLES ---
# These are managed by the main function to avoid complex global state
class GeneratorState:
    def __init__(self, image):
        self.base_image = image
        self.display_image = image.copy()
        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.selected_roi = None

def draw_text(img, text, pos, font_scale=1.2, color=(255, 255, 255), thickness=2):
    """Helper to draw large, visible text with a black background for readability."""
    (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    pad = 10
    cv2.rectangle(img, (pos[0] - pad, pos[1] + pad), (pos[0] + text_w + pad, pos[1] - text_h - (pad * 2)), (0, 0, 0), -1)
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

def update_display(state, player_name):
    """Redraws the entire display based on the current state. Call only when state changes."""
    state.display_image = state.base_image.copy()
    
    if state.selected_roi:
        x, y, w, h = state.selected_roi
        cv2.rectangle(state.display_image, (x, y), (x + w, y + h), (0, 0, 255), 3) # Thick Red
        draw_text(state.display_image, f"Confirm for {player_name.upper()}?", (50, 70))
        draw_text(state.display_image, "'y': Yes | 'n': No, re-draw | 's': Skip", (50, 130), font_scale=0.8)
    else:
        draw_text(state.display_image, f"Draw rectangle around: {player_name.upper()}", (50, 70))
        draw_text(state.display_image, "'s': Skip Player | 'q': Quit", (50, 130), font_scale=0.8)
    
    cv2.imshow(WINDOW_NAME, state.display_image)

def mouse_callback(event, x, y, flags, param):
    """Handles mouse events. More efficient drawing during mouse drag."""
    state, player_name = param  # Unpack state and current player name

    if event == cv2.EVENT_LBUTTONDOWN:
        state.drawing = True
        state.start_point = (x, y)
        state.selected_roi = None
        update_display(state, player_name) # Redraw to clear old confirmation box

    elif event == cv2.EVENT_MOUSEMOVE:
        if state.drawing:
            # For smooth drawing, only update the display with a temporary rectangle
            temp_img = state.display_image.copy()
            cv2.rectangle(temp_img, state.start_point, (x, y), (0, 255, 0), 2)
            cv2.imshow(WINDOW_NAME, temp_img)

    elif event == cv2.EVENT_LBUTTONUP:
        state.drawing = False
        state.end_point = (x, y)
        x1, y1 = min(state.start_point[0], state.end_point[0]), min(state.start_point[1], state.end_point[1])
        x2, y2 = max(state.start_point[0], state.end_point[0]), max(state.start_point[1], state.end_point[1])
        
        if x2 - x1 > 5 and y2 - y1 > 5:
            state.selected_roi = (x1, y1, x2 - x1, y2 - y1)
        else:
            state.selected_roi = None
        
        update_display(state, player_name) # Update with the final red box for confirmation

def refine_and_save_template(img_base, rough_box, player_name):
    """Crops the template by finding the tightest bounding box around white text."""
    x, y, w, h = rough_box
    initial_crop = img_base[y:y+h, x:x+w]

    if initial_crop.size == 0:
        print(f"   ! Failed to crop for '{player_name}'. Skipping.")
        return

    gray = cv2.cvtColor(initial_crop, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print(f"   ! No text contours found for '{player_name}'. Saving the rough selection.")
        final_crop = initial_crop
    else:
        all_points = np.concatenate(contours, axis=0)
        cx, cy, cw, ch = cv2.boundingRect(all_points)
        pad = 1
        final_crop = initial_crop[max(0, cy-pad):cy+ch+pad, max(0, cx-pad):cx+cw+pad]

    save_path = os.path.join(NAME_TEMPLATES_PATH, f"{player_name.lower()}.png")
    cv2.imwrite(save_path, final_crop)
    print(f"   + Template for '{player_name.upper()}' saved successfully.")

def run_interactive_template_generator(player_names, screenshot_path):
    """An interactive tool that lets the user generate templates one by one with improved performance."""
    if not os.path.exists(screenshot_path):
        print(f"Error: Screenshot not found at '{screenshot_path}'. Aborting.")
        return

    try:
        img_base = cv2.imread(screenshot_path)
        if img_base is None: raise ValueError("Image could not be loaded.")
    except Exception as e:
        print(f"Error loading screenshot: {e}")
        return

    os.makedirs(NAME_TEMPLATES_PATH, exist_ok=True)
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    
    state = GeneratorState(img_base)

    print("\n--- Interactive Name Template Generator ---")
    print("Instructions are in the image window. Press 'q' to quit at any time.")

    for i, player in enumerate(player_names):
        state.selected_roi = None # Reset selection for each new player
        
        # Pass state and player name to the callback
        cv2.setMouseCallback(WINDOW_NAME, mouse_callback, (state, player))
        update_display(state, player)

        while True:
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print("\n-> Quitting template generator.")
                cv2.destroyAllWindows()
                return
            
            if key == ord('s'):
                print(f"\n-> Skipped {player.upper()}.")
                break # Move to the next player in the outer loop

            if state.selected_roi:
                if key == ord('y'):
                    print(f"\n-> Creating template for: {player.upper()}")
                    refine_and_save_template(state.base_image, state.selected_roi, player)
                    break # Move to the next player
                
                elif key == ord('n'):
                    print("   - Selection rejected. Please re-draw.")
                    state.selected_roi = None
                    update_display(state, player)

    # --- Final Confirmation Screen ---
    final_img = state.base_image.copy()
    # Apply a dark overlay
    overlay = np.zeros_like(final_img)
    cv2.addWeighted(final_img, 0.5, overlay, 0.5, 0, final_img)
    
    # Display the final message
    text = "ALL DONE! PROCEED IN TERMINAL"
    font_scale = 1.5
    thickness = 2
    (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    center_x, center_y = final_img.shape[1] // 2, final_img.shape[0] // 2
    cv2.putText(final_img, text, (center_x - text_w // 2, center_y + text_h // 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
    
    cv2.imshow(WINDOW_NAME, final_img)
    cv2.waitKey(2000) # Display for 2 seconds

    print("\n--- Template generation complete. ---")
    cv2.destroyAllWindows()
