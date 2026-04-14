from collections import Counter, deque
import os
import sys

# OpenCV is required for webcam capture and display.
try:
    import cv2
except ModuleNotFoundError as error:
    if error.name == "cv2":
        print(
            "OpenCV is not installed, so webcam mode cannot start.\n"
            "On a Raspberry Pi, the most reliable fix is:\n"
            "  sudo apt update\n"
            "  sudo apt install python3-opencv python3-numpy\n\n"
            "If you only want to test the game logic, run:\n"
            "  python3 connect4_ai_test.py"
        )
        raise SystemExit(1)
    raise

# NumPy handles the perspective warp and pixel scoring.
try:
    import numpy as np
except ModuleNotFoundError as error:
    if error.name == "numpy":
        print(
            "NumPy is not installed, so webcam mode cannot start.\n"
            "On a Raspberry Pi, install it with:\n"
            "  sudo apt update\n"
            "  sudo apt install python3-numpy\n\n"
            "If you only want to test the game logic, run:\n"
            "  python3 connect4_ai_test.py"
        )
        raise SystemExit(1)
    raise

import main
from gantry_serial import build_gantry_link_from_env


# Board geometry and colour thresholds.
ROWS = main.rows
COLS = main.cols
HUMAN_SYMBOL = main.symbol1
AI_SYMBOL = main.symbol2
CAMERA_INDEX = 1
CAMERA_CANDIDATES = [0, 1, 2, 3]
WINDOW_NAME = "Connect 4 Webcam"
STABLE_DETECTIONS = 8
BOARD_WIDTH = 700
BOARD_HEIGHT = 600
CALIBRATION_PATCH = 28
CALIBRATION_HUE_WIDTH = 18
DETECTION_MIN_AREA_RATIO = 0.12
DEFAULT_HUMAN_MODEL = {"hue": 0, "sat_low": 80, "val_low": 50, "hue_width": CALIBRATION_HUE_WIDTH}
DEFAULT_AI_MODEL = {"hue": 28, "sat_low": 80, "val_low": 50, "hue_width": CALIBRATION_HUE_WIDTH}


# Webcam mode needs a desktop session, not a headless terminal.
def ensure_gui_available():
    if sys.platform.startswith("linux"):
        has_x11 = bool(os.environ.get("DISPLAY"))
        has_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
        if not (has_x11 or has_wayland):
            raise RuntimeError(
                "No graphical desktop session was detected. Webcam mode uses OpenCV windows, "
                "so on a Raspberry Pi it must be run from the desktop, VNC, or an SSH session "
                "with X forwarding enabled. For terminal-only play, run `python3 connect4_ai_test.py`."
            )


def empty_board():
    return [[" "] * COLS for _ in range(ROWS)]


def clone_board(board):
    return [row[:] for row in board]


def board_to_key(board):
    return tuple(tuple(row) for row in board)


def key_to_board(key):
    return [list(row) for row in key]


def board_to_text(board):
    return "\n".join(" ".join(cell if cell != " " else "." for cell in row) for row in board)


def order_points(points):
    pts = np.array(points, dtype=np.float32)
    ordered = np.zeros((4, 2), dtype=np.float32)
    sums = pts.sum(axis=1)
    diffs = np.diff(pts, axis=1)
    ordered[0] = pts[np.argmin(sums)]
    ordered[2] = pts[np.argmax(sums)]
    ordered[1] = pts[np.argmin(diffs)]
    ordered[3] = pts[np.argmax(diffs)]
    return ordered


def board_outline_from_hole_centers(points):
    # Convert corner hole clicks into the board outline.
    tl, tr, br, bl = order_points(points)
    top_step = (tr - tl) / max(COLS - 1, 1)
    bottom_step = (br - bl) / max(COLS - 1, 1)
    left_step = (bl - tl) / max(ROWS - 1, 1)
    right_step = (br - tr) / max(ROWS - 1, 1)

    outline = np.array(
        [
            tl - 0.5 * top_step - 0.5 * left_step,
            tr + 0.5 * top_step - 0.5 * right_step,
            br + 0.5 * bottom_step + 0.5 * right_step,
            bl - 0.5 * bottom_step + 0.5 * left_step,
        ],
        dtype=np.float32,
    )
    return outline


def warp_board(frame, hole_centers):
    # Warp the camera view into a top-down board view.
    src = board_outline_from_hole_centers(hole_centers)
    dst = np.array(
        [
            [0, 0],
            [BOARD_WIDTH - 1, 0],
            [BOARD_WIDTH - 1, BOARD_HEIGHT - 1],
            [0, BOARD_HEIGHT - 1],
        ],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(frame, matrix, (BOARD_WIDTH, BOARD_HEIGHT))


def circular_hue_distance(hue_values, target_hue):
    diff = np.abs(hue_values.astype(np.int16) - int(target_hue))
    return np.minimum(diff, 180 - diff)


def sample_colour_model(frame, sample_point, label):
    # Learn a colour model from a clicked counter.
    sample = extract_sample_patch(frame, sample_point)
    hsv = cv2.cvtColor(sample, cv2.COLOR_BGR2HSV)
    pixels = hsv.reshape(-1, 3)
    strong_pixels = pixels[(pixels[:, 1] > 80) & (pixels[:, 2] > 60)]
    if len(strong_pixels) == 0:
        raise ValueError(f"Could not detect a strong {label} colour in the sample area.")

    dominant_hue = int(np.median(strong_pixels[:, 0]))
    sat_low = int(max(50, np.percentile(strong_pixels[:, 1], 15) - 15))
    val_low = int(max(40, np.percentile(strong_pixels[:, 2], 10) - 20))
    hue_width = int(min(28, max(CALIBRATION_HUE_WIDTH, np.percentile(circular_hue_distance(strong_pixels[:, 0], dominant_hue), 90) + 4)))
    return {
        "hue": dominant_hue,
        "sat_low": sat_low,
        "val_low": val_low,
        "hue_width": hue_width,
    }


def model_score(hsv, circle_mask, colour_model):
    masked_pixels = hsv[circle_mask > 0]
    if len(masked_pixels) == 0:
        return 0

    hue_distance = circular_hue_distance(masked_pixels[:, 0], colour_model["hue"])
    sat_threshold = max(40, colour_model["sat_low"] - 35)
    val_threshold = max(25, colour_model["val_low"] - 35)
    valid_mask = (masked_pixels[:, 1] >= sat_threshold) & (masked_pixels[:, 2] >= val_threshold)
    if not np.any(valid_mask):
        return 0

    close_hue = hue_distance <= colour_model["hue_width"]
    strong_match = valid_mask & close_hue
    return int(np.count_nonzero(strong_match))


def classify_cell(cell_bgr, human_model, ai_model):
    # Compare the detected pixels against both colour models.
    hsv = cv2.cvtColor(cell_bgr, cv2.COLOR_BGR2HSV)
    h, w = hsv.shape[:2]
    radius = int(min(h, w) * 0.22)
    center = (w // 2, h // 2)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, center, radius, 255, -1)

    human_score = model_score(hsv, mask, human_model)
    ai_score = model_score(hsv, mask, ai_model)
    area = np.pi * radius * radius

    if human_score > area * DETECTION_MIN_AREA_RATIO and human_score > ai_score * 1.2:
        symbol = HUMAN_SYMBOL
    elif ai_score > area * DETECTION_MIN_AREA_RATIO and ai_score > human_score * 1.2:
        symbol = AI_SYMBOL
    else:
        symbol = " "

    return symbol, int(human_score), int(ai_score)

def detect_board_state_with_debug(warped_frame, human_model, ai_model):
    # Classify each cell and keep per-cell debug scores.
    board = empty_board()
    debug = [[None] * COLS for _ in range(ROWS)]
    cell_w = BOARD_WIDTH / COLS
    cell_h = BOARD_HEIGHT / ROWS

    for row in range(ROWS):
        for col in range(COLS):
            x0 = int(col * cell_w)
            x1 = int((col + 1) * cell_w)
            y0 = int(row * cell_h)
            y1 = int((row + 1) * cell_h)
            cell = warped_frame[y0:y1, x0:x1]
            symbol, human_score, ai_score = classify_cell(cell, human_model, ai_model)
            board[row][col] = symbol
            debug[row][col] = {
                "symbol": symbol,
                "human_score": human_score,
                "ai_score": ai_score,
            }

    return board, debug


def draw_grid_overlay(frame):
    # Draw the logical 7x6 grid over the warped board image.
    overlay = frame.copy()
    cell_w = BOARD_WIDTH / COLS
    cell_h = BOARD_HEIGHT / ROWS

    for col in range(1, COLS):
        x = int(col * cell_w)
        cv2.line(overlay, (x, 0), (x, BOARD_HEIGHT), (255, 255, 255), 1)
    for row in range(1, ROWS):
        y = int(row * cell_h)
        cv2.line(overlay, (0, y), (BOARD_WIDTH, y), (255, 255, 255), 1)

    return overlay


def has_gravity(board):
    # Valid boards cannot have floating pieces.
    for col in range(COLS):
        seen_empty = False
        for row in range(ROWS - 1, -1, -1):
            if board[row][col] == " ":
                seen_empty = True
            elif seen_empty:
                return False
    return True


def gravity_failure(board):
    # Return the first column that violates gravity.
    for col in range(COLS):
        seen_empty = False
        for row in range(ROWS - 1, -1, -1):
            if board[row][col] == " ":
                seen_empty = True
            elif seen_empty:
                return f"gap in column {col + 1}"
    return None


def count_symbol(board, symbol):
    return sum(cell == symbol for row in board for cell in row)


def is_valid_detected_board(board):
    human_count = count_symbol(board, HUMAN_SYMBOL)
    ai_count = count_symbol(board, AI_SYMBOL)
    return has_gravity(board) and human_count >= ai_count and human_count - ai_count <= 1


def board_validation_message(board):
    gravity_issue = gravity_failure(board)
    if gravity_issue is not None:
        return f"Inconsistent: {gravity_issue}"

    human_count = count_symbol(board, HUMAN_SYMBOL)
    ai_count = count_symbol(board, AI_SYMBOL)
    if human_count < ai_count:
        return f"Inconsistent: human={human_count}, program={ai_count}"
    if human_count - ai_count > 1:
        return f"Inconsistent: too many human moves ({human_count}-{ai_count})"
    return f"Counts OK: human={human_count}, program={ai_count}"


def apply_move(board, col, symbol):
    # Simulate a move on a copy of the current board.
    updated = clone_board(board)
    row = main.GetAvailableRow(updated, col)
    if row is None:
        return None
    updated[row][col] = symbol
    return updated


def diff_cells(before, after):
    # Find the cells that changed between two board states.
    diffs = []
    for row in range(ROWS):
        for col in range(COLS):
            if before[row][col] != after[row][col]:
                diffs.append((row, col, before[row][col], after[row][col]))
    return diffs


def is_single_human_move(previous_board, detected_board):
    # Accept only one legal human placement at a time.
    diffs = diff_cells(previous_board, detected_board)
    if len(diffs) != 1:
        return False
    row, col, before, after = diffs[0]
    if before != " " or after != HUMAN_SYMBOL:
        return False
    expected_row = main.GetAvailableRow(previous_board, col)
    return expected_row == row


def select_stable_board(history):
    # Require the same detected board several times in a row.
    if len(history) < STABLE_DETECTIONS:
        return None
    counts = Counter(history)
    board_key, board_count = counts.most_common(1)[0]
    if board_count >= STABLE_DETECTIONS:
        return key_to_board(board_key)
    return None


def draw_status_text(frame, lines, origin=(10, 25), color=(0, 255, 0)):
    # Render status lines on the video frame.
    x, y = origin
    for index, line in enumerate(lines):
        cv2.putText(
            frame,
            line,
            (x, y + index * 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
            cv2.LINE_AA,
        )


def sample_patch_bounds(frame, sample_point):
    # Clamp the sample area so it stays inside the image.
    h, w = frame.shape[:2]
    patch = min(CALIBRATION_PATCH, h - 2, w - 2)
    half = patch // 2
    cx = int(np.clip(sample_point[0], half, w - half))
    cy = int(np.clip(sample_point[1], half, h - half))
    return cx - half, cy - half, cx + half, cy + half


def extract_sample_patch(frame, sample_point):
    x0, y0, x1, y1 = sample_patch_bounds(frame, sample_point)
    return frame[y0:y1, x0:x1]


def draw_sample_marker(frame, sample_point):
    # Show the sampled patch on the warped board view.
    x0, y0, x1, y1 = sample_patch_bounds(frame, sample_point)
    cx, cy = sample_point
    cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 255, 255), 2)
    cv2.drawMarker(frame, (cx, cy), (0, 255, 255), cv2.MARKER_CROSS, 18, 2)


def parse_camera_candidates():
    # Allow optional camera index overrides from the command line.
    if len(sys.argv) <= 1:
        return CAMERA_CANDIDATES

    candidates = []
    for arg in sys.argv[1:]:
        try:
            candidates.append(int(arg))
        except ValueError:
            pass
    return candidates or CAMERA_CANDIDATES


def open_webcam():
    # Try a small set of camera indices until one opens cleanly.
    attempted = []
    for camera_index in parse_camera_candidates():
        capture = cv2.VideoCapture(camera_index)
        if capture.isOpened():
            ok, _frame = capture.read()
            if ok:
                return capture, camera_index
        capture.release()
        attempted.append(str(camera_index))

    attempted_text = ", ".join(attempted) if attempted else "none"
    raise RuntimeError(
        f"Could not open webcam. Tried camera indices: {attempted_text}. "
        "Close other apps using the camera, or run `python3 connect4_webcam.py 1` with a different index."
    )


def draw_detection_debug(frame, debug_cells):
    # Overlay the per-cell classification scores for troubleshooting.
    cell_w = BOARD_WIDTH / COLS
    cell_h = BOARD_HEIGHT / ROWS

    for row in range(ROWS):
        for col in range(COLS):
            info = debug_cells[row][col]
            if info is None:
                continue

            x = int(col * cell_w)
            y = int(row * cell_h)
            symbol = info["symbol"] if info["symbol"] != " " else "."

            cv2.putText(
                frame,
                symbol,
                (x + 8, y + 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"H{info['human_score']}",
                (x + 8, y + int(cell_h) - 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (80, 255, 80),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"A{info['ai_score']}",
                (x + 8, y + int(cell_h) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (80, 160, 255),
                1,
                cv2.LINE_AA,
            )


def main_loop():
    ensure_gui_available()
    capture, active_camera_index = open_webcam()
    gantry_link = build_gantry_link_from_env()

    # Track calibration, detection stability, and whose turn it is.
    clicked_corners = []
    detection_history = deque(maxlen=STABLE_DETECTIONS)
    logical_board = empty_board()
    expected_ai_board = None
    ai_choice = None
    turn = "human"
    message = "Click the centers of the 4 corner holes: top-left, top-right, bottom-right, bottom-left."
    if gantry_link is not None:
        connected, serial_status = gantry_link.connect()
        if connected:
            message = f"{message} Serial ready on {gantry_link.port}."
        else:
            message = f"{message} Serial disabled: {serial_status}"
    winner = None
    human_model = DEFAULT_HUMAN_MODEL.copy()
    ai_model = DEFAULT_AI_MODEL.copy()
    human_colour_ready = False
    ai_colour_ready = False
    pending_sample = None
    latest_detected_board = empty_board()
    latest_debug_cells = [[None] * COLS for _ in range(ROWS)]

    def on_mouse(_event, x, y, _flags, _param):
        nonlocal clicked_corners, message
        if _event == cv2.EVENT_LBUTTONDOWN and len(clicked_corners) < 4:
            clicked_corners.append((x, y))
            if len(clicked_corners) == 4:
                message = "Calibration complete. Click a counter in Board View, then press H or A."

    def on_board_mouse(_event, x, y, _flags, _param):
        nonlocal pending_sample, message
        if _event == cv2.EVENT_LBUTTONDOWN:
            pending_sample = (x, y)
            message = f"Sample selected at ({x}, {y}). Press H for human or A for program."

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse)
    cv2.namedWindow("Board View")
    cv2.setMouseCallback("Board View", on_board_mouse)

    while True:
        ok, frame = capture.read()
        if not ok:
            break

        display = frame.copy()
        for index, point in enumerate(clicked_corners, start=1):
            cv2.circle(display, point, 6, (255, 0, 0), -1)
            cv2.putText(display, str(index), (point[0] + 8, point[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        warped = None
        stable_board = None

        if len(clicked_corners) == 4:
            warped = warp_board(frame, clicked_corners)
            if human_colour_ready and ai_colour_ready:
                # Only trust the board after both colours are calibrated.
                detected_board, latest_debug_cells = detect_board_state_with_debug(warped, human_model, ai_model)
                latest_detected_board = clone_board(detected_board)
                detection_history.append(board_to_key(detected_board))
                stable_board = select_stable_board(detection_history)
            else:
                detection_history.clear()
                latest_detected_board = empty_board()
                latest_debug_cells = [[None] * COLS for _ in range(ROWS)]

            warped_display = draw_grid_overlay(warped)
            if pending_sample is not None:
                draw_sample_marker(warped_display, pending_sample)
            draw_detection_debug(warped_display, latest_debug_cells)
            draw_status_text(
                warped_display,
                [
                    "Top view",
                    f"Human colour: {'set' if human_colour_ready else 'not set'}",
                    f"Program colour: {'set' if ai_colour_ready else 'not set'}",
                    "Click a counter to sample its colour",
                ],
                origin=(10, 25),
                color=(255, 255, 255),
            )
            cv2.imshow("Board View", warped_display)

        if stable_board is not None and winner is None:
            if not is_valid_detected_board(stable_board):
                message = board_validation_message(stable_board)
            elif turn == "human":
                if board_to_key(stable_board) == board_to_key(logical_board):
                    message = "Waiting for the human move."
                elif is_single_human_move(logical_board, stable_board):
                    logical_board = clone_board(stable_board)
                    if main.IsWinningBoard(HUMAN_SYMBOL, logical_board):
                        winner = "Human wins."
                        message = winner
                    elif main.IsFull(logical_board):
                        winner = "Draw."
                        message = winner
                    else:
                        # Ask the AI for the next move and mirror it on the board.
                        ai_choice = main.BestMove(clone_board(logical_board), AI_SYMBOL, HUMAN_SYMBOL, maxDepth=5)
                        expected_ai_board = apply_move(logical_board, ai_choice, AI_SYMBOL)
                        if expected_ai_board is None:
                            winner = "Draw."
                            message = winner
                        else:
                            turn = "await_ai_confirmation"
                            if gantry_link is None:
                                message = f"Program plays column {ai_choice + 1}. Place the program counter there."
                            else:
                                sent, serial_status = gantry_link.send_column(ai_choice)
                                if sent:
                                    message = f"Program plays column {ai_choice + 1}. Gantry command sent."
                                else:
                                    message = (
                                        f"Program chose column {ai_choice + 1}, but serial send failed. "
                                        f"{serial_status}"
                                    )
                else:
                    message = "Move seen but rejected. Check the Detected board view and recalibrate if needed."
            elif turn == "await_ai_confirmation" and expected_ai_board is not None:
                if board_to_key(stable_board) == board_to_key(expected_ai_board):
                    logical_board = clone_board(expected_ai_board)
                    expected_ai_board = None
                    if main.IsWinningBoard(AI_SYMBOL, logical_board):
                        winner = "Program wins."
                        message = winner
                    elif main.IsFull(logical_board):
                        winner = "Draw."
                        message = winner
                    else:
                        turn = "human"
                        message = "Waiting for the human move."
                else:
                    message = f"Program move is column {ai_choice + 1}. Waiting for the board to match."

        if len(clicked_corners) == 4 and not (human_colour_ready and ai_colour_ready):
            if pending_sample is None:
                if not human_colour_ready:
                    message = "Click the human counter in Board View, then press H."
                elif not ai_colour_ready:
                    message = "Click the program counter in Board View, then press A."

        info_lines = [
            message,
            f"Camera index: {active_camera_index}",
            "Keys: click in Board View to sample, h human colour, a program colour, q quit, r reset",
        ]
        if ai_choice is not None and turn == "await_ai_confirmation":
            info_lines.append(f"Suggested column: {ai_choice + 1}")
        draw_status_text(display, info_lines)

        board_lines = board_to_text(logical_board).splitlines()
        draw_status_text(display, ["Logical board:"] + board_lines, origin=(10, 110), color=(0, 255, 255))
        detected_lines = board_to_text(latest_detected_board).splitlines()
        draw_status_text(display, ["Detected board:"] + detected_lines, origin=(10, 320), color=(255, 255, 255))

        cv2.imshow(WINDOW_NAME, display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break
        if key == ord("h") and len(clicked_corners) == 4:
            try:
                if pending_sample is None:
                    raise ValueError("Click the human counter in Board View before pressing H.")
                human_model = sample_colour_model(warp_board(frame, clicked_corners), pending_sample, "human counter")
                human_colour_ready = True
                detection_history.clear()
                message = "Human counter colour calibrated."
            except ValueError as error:
                message = str(error)
        if key == ord("a") and len(clicked_corners) == 4:
            try:
                if pending_sample is None:
                    raise ValueError("Click the program counter in Board View before pressing A.")
                ai_model = sample_colour_model(warp_board(frame, clicked_corners), pending_sample, "program counter")
                ai_colour_ready = True
                detection_history.clear()
                message = "Program counter colour calibrated."
            except ValueError as error:
                message = str(error)
        if key == ord("r"):
            # Reset the full calibration and game state.
            clicked_corners = []
            detection_history.clear()
            logical_board = empty_board()
            expected_ai_board = None
            ai_choice = None
            turn = "human"
            winner = None
            human_model = DEFAULT_HUMAN_MODEL.copy()
            ai_model = DEFAULT_AI_MODEL.copy()
            human_colour_ready = False
            ai_colour_ready = False
            pending_sample = None
            latest_detected_board = empty_board()
            latest_debug_cells = [[None] * COLS for _ in range(ROWS)]
            message = "Click the centers of the 4 corner holes: top-left, top-right, bottom-right, bottom-left."

    capture.release()
    if gantry_link is not None:
        gantry_link.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main_loop()
    except RuntimeError as error:
        print(error)
        raise SystemExit(1)
