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

## Notes

- `connect4_webcam.py` imports `main.py` for the Connect 4 game logic.
- `connect4_webcam.py` imports `gantry_serial.py` for optional serial communication.
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

