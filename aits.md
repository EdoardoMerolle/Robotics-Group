# Group 9: Edoardo Merolle & Jack Abson AITS
Model Used: ChatGPT 5 Codex

## Connect 4 Logic

The project builds on Edoardo’s previous Artificial Intelligence & Machine Learning Connect 4 work from Level 2, which was used as the foundation for the robot’s decision-making system. Codex extended this by improving the AI’s move selection and overall strategy.

The Connect 4 algorithm was enhanced through better move simulation and smarter column ordering, prioritising central columns before moving outward. The BestMove function was also refined to prioritise winning moves, block immediate losses, and avoid moves that would allow obvious counterplays.

In addition, the minimax evaluation was strengthened to better value centre control and recognise potential threats. The search depth used in both the testing environment and the webcam-based gameplay was increased, resulting in more consistent and competitive AI behaviour.

## Camera Control

To allow the robot to interact with a physical board, Codex developed a webcam-based detection system. This system uses a separate Python script to identify the four corner holes of the board, apply a perspective transformation, and convert the camera feed into a top-down grid representation.

From this transformed view, the program reconstructs the game state in real time. It also includes colour calibration, debug overlays, validation checks, and move tracking, enabling a human player to compete against the AI using a physical board.

This system was refined through iterative testing and feedback from Edoardo. Several usability improvements were introduced, including colour customisation, a virtual environment with a run script, improved calibration controls, and replacing the original calibration box with a more precise eyedropper tool. Additional work was done to improve robustness under varying lighting conditions, along with the creation of a separate non-webcam test harness for AI development.

During testing, a number of issues were identified. These included unreliable move detection, incorrect board cropping (sometimes including the tray instead of just the grid), failures when accessing the default camera index, and errors in the consistency checker that incorrectly flagged valid board states. Codex addressed these problems by introducing camera index fallback, improving debug visualisation, switching to hole-centre based calibration, refining colour detection, and correcting the gravity-check logic.

## Gantry Control

To physically execute the AI’s chosen move, Codex generated a VEX EXP brain-side program to control the gantry mechanism. This program receives a column number (1–7) via serial communication, interprets it as the target column, and moves the gantry motor to the corresponding position using predefined motor values.

This component was shaped significantly by Edoardo’s feedback. He requested that the gantry pause at the selected column before returning, use “column 0” as an off-board resting position, and operate at a slower speed so that movement could be clearly observed.

To support easier setup and adjustment, a controller-based calibration mode was introduced. This allows the gantry positions for each column to be configured interactively:

- B enters calibration mode
- A saves the current motor position for the selected column
- R1 exits calibration mode

While in calibration mode, the gantry can be manually adjusted (jogged), and positions can be stored for each column. Once calibration is complete, the system returns to normal operation using serial input. For convenience, the saved calibration values are also printed to the console, making them easier to review than on the brain display.

Further testing revealed several issues, including the controller becoming unresponsive due to blocking serial input, calibration text being difficult to read, and unintuitive button mapping. These were resolved by moving serial communication to a background task, simplifying the on-screen interface, and updating the control scheme.

Finally, the gantry behaviour was refined so that it pauses at the selected column for five seconds before returning to the home position. This home position is treated as column 0, ensuring the gantry remains clear of the board between moves.