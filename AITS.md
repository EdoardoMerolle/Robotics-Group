# Group 9 AITS Statement

- Model used: ChatGPT 5 Codex
- AITS level: 5

I used AI throughout this project to refine the Connect 4 robot system, including the game logic, webcam-based board detection, and gantry control. The Connect 4 logic in `main.py` was my own Level 5 work, and Codex helped extend it by improving the minimax-based decision-making, move ordering, threat detection, and physical-game integration. For the rest of the system, I directed the AI to generate code, reviewed the results, tested them on the physical setup, and asked for changes whenever the behaviour was not correct or not reliable enough for the real board.

Codex then helped refine the Connect 4 behaviour, including the minimax-based decision-making, move ordering, threat detection, and win/block logic. I tested those outputs and requested adjustments to make the AI play more sensibly and to improve how it handled edge cases during actual gameplay.

Codex was also used to build the webcam pipeline for detecting the physical board. This included perspective correction, colour calibration, board-state reconstruction, detection stability checks, and validation of legal board positions. I checked the webcam output against the physical board, identified problems such as unreliable move detection, incorrect board cropping, camera-index failures, and gravity-check errors, and then asked for revisions until the system behaved properly.

For the hardware side, Codex generated the VEX EXP gantry control and serial communication code. I tested how the brain responded to column commands, checked that the gantry moved to the correct positions, and requested changes such as slower motion, a pause at the selected column, and a column position calibration mode. I also verified that the system could recover from serial and controller issues during testing.

My role was to direct ChatGPT Codex, judge whether the results were acceptable, and keep iterating until the final system worked as a complete physical computing project. The final submission is therefore based on my own Connect 4 logic, with AI-assisted webcam-controlled functionality and serial connection, human testing, and iterative correction throughout, which is why I consider it to fit AITS level 5.
