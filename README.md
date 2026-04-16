# Connect 4 Robot Project

This repository contains the Connect 4 AI, webcam-based board detection, and gantry serial control used to play on a physical board.

## What You Need

### Required Project Files

To run the webcam version from `run_connect4_windows_webcam.bat`, these local files are required:

- `run_connect4_windows_webcam.bat`
- `connect4_webcam.py`
- `main.py`
- `gantry_serial.py`
- `requirements.txt`

### Python Packages

Install the packages listed in `requirements.txt`:

- `numpy`
- `opencv-python`
- `pyserial`

### Optional Files

These files are useful for testing or other modes, but they are not required for the webcam launcher:

- `connect4_ai_test.py`
- `connect4_serial_test.py`
- `vex_column_test.py`
- `run_connect4_windows.bat`
- `run_connect4.sh`
- `aits.md`
- `Assessment 2.docx`
- `.3mf` files
- `STL FILES/`

### Hardware and Runtime Requirements

- A working webcam
- A graphical desktop session
- If you want serial output to the robot/brain: a connected serial device and the correct COM port

## How To Run

### Windows Webcam Mode

Run:

```bat
run_connect4_windows_webcam.bat
```

You can also pass a COM port and baud rate:

```bat
run_connect4_windows_webcam.bat COM4 115200
```

If no arguments are provided, the script defaults to:

- COM port: `COM4`
- Baud rate: `115200`

### What the Batch File Does

The batch file:

- finds the Python interpreter
- enables serial output through environment variables
- starts `connect4_webcam.py`

## Setup

### Physical Setup

- Board location: Place the board on a flat, stable surface with a plain background behind it.
- Webcam position: Position the webcam so it faces the board directly and captures the full play area.
- Lighting setup: Use bright, even lighting to reduce colour detection errors and shadows.
- Gantry placement: Keep the dropper chute just above and parallel to the board so pieces can be placed cleanly.
- Serial connection port: Use the correct COM port for your setup. `COM4` is the default, but you can change it as explained in the [How To Run](#how-to-run) section.

### Calibration Steps

1. Open the webcam mode.
2. Click on the four corner holes of the board to calibrate the warped camera view.
3. Sample the human counter colour by clicking on a human counter in the Board View and pressing `H`.
4. To sample the program counter colour, repeat the same step but press `A` instead.
5. Check that the detected board matches the real board.
6. Adjust the calibration if needed.

### Game Start Procedure

- Who moves first: Human
- How a human move is entered: Physically place the counter into the desired column on the board.
- How the AI move is displayed or sent to the gantry: The program displays the suggested column and sends the column number through serial connection.
- What to do if the board state becomes inconsistent: Press `R` on your keyboard to reset the calibration and game state.

### Notes for Demonstration
- Best lighting conditions: Bright and even

## Notes

- `connect4_webcam.py` imports `main.py` for the Connect 4 game logic.
- `connect4_webcam.py` imports `gantry_serial.py` for optional serial communication.
- The webcam mode calibrates the board from the four corner holes, warps the camera into a top-down view, and then tracks moves using colour calibration and board-state validation.
- If the board detection becomes inconsistent, the program shows debug overlays and lets you recalibrate the board or reset the full session with `r`.
- The gantry side uses serial column commands and includes a calibration workflow so the column positions can be tuned for the physical build.
- If `pyserial` is missing, the webcam mode can still run, but serial commands to the robot will be disabled.
- If OpenCV or NumPy is missing, webcam mode will not start.

## Other Run Modes

If you only want to test the AI without the webcam, use:

```bat
python connect4_ai_test.py
```

## Repository Contents

- `main.py`: Connect 4 rules, board handling, and AI search
- `connect4_webcam.py`: webcam detection and physical board gameplay
- `gantry_serial.py`: serial link to the robot/brain
- `connect4_ai_test.py`: terminal-based AI test mode
- `connect4_serial_test.py`: serial communication test
- `vex_column_test.py`: gantry calibration/testing utility

## References

- OpenCV documentation: https://docs.opencv.org/
- NumPy documentation: https://numpy.org/doc/
- pyserial documentation: https://pyserial.readthedocs.io/
- VEX EXP documentation and support resources used during development
- AI transparency statement and usage summary: `AITS.md`
