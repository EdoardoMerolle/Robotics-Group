/*----------------------------------------------------------------------------*/
/*                                                                            */
/*    File: vex_exp_gantry_serial_main.cpp                                    */
/*    Target: VEX EXP Brain                                                   */
/*                                                                            */
/*    Paste this into a new VEXcode C++ project and download it to the brain. */
/*                                                                            */
/*    Serial protocol: send one line containing a column number 1-7.          */
/*    Example messages from the AI computer:                                  */
/*      1                                                                      */
/*      4                                                                      */
/*      7                                                                      */
/*                                                                            */
/*    The brain reads that number, then moves the gantry motor to the preset  */
/*    position for that column. Adjust COLUMN_POSITIONS_DEG to match your      */
/*    real gantry spacing.                                                     */
/*                                                                            */
/*----------------------------------------------------------------------------*/

#include "vex.h"
#include <cstdio>
#include <cstdlib>
#include <cmath>

using namespace vex;

brain Brain;
motor GantryMotor = motor(PORT1, ratio18_1, false);
controller Controller1 = controller(primary);

const int COLUMN_COUNT = 7;
const int HOME_COLUMN = 0;
const int MOTOR_SPEED_PCT = 10;
const int CALIBRATION_JOG_SPEED_PCT = 5;
const int COLUMN_DWELL_MS = 5000;
const double JOG_DEADBAND_PCT = 5.0;
double homePositionDeg = -90.0;
double columnPositionsDeg[COLUMN_COUNT] = {
  0.0,   // Column 1
  90.0,  // Column 2
  180.0, // Column 3
  270.0, // Column 4
  360.0, // Column 5
  450.0, // Column 6
  540.0  // Column 7
};

volatile int pendingSerialColumn = 0;
volatile bool serialCommandPending = false;

void drawStatus(const char *line1, const char *line2 = "") {
  Brain.Screen.clearScreen();
  Brain.Screen.setCursor(2, 1);
  Brain.Screen.print("Gantry");
  Brain.Screen.setCursor(4, 1);
  Brain.Screen.print(line1);
  Brain.Screen.setCursor(6, 1);
  Brain.Screen.print(line2);
}

void drawCalibrationScreen(int selectedColumn) {
  Brain.Screen.clearScreen();
  Brain.Screen.setCursor(1, 1);
  Brain.Screen.print("Cal");
  Brain.Screen.setCursor(3, 1);
  Brain.Screen.print("Col: %d", selectedColumn);
  Brain.Screen.setCursor(4, 1);
  Brain.Screen.print("Deg: %.1f", GantryMotor.position(degrees));
  Brain.Screen.setCursor(6, 1);
  Brain.Screen.print("Stick: jog");
  Brain.Screen.setCursor(7, 1);
  Brain.Screen.print("A save U/D sel");
  Brain.Screen.setCursor(8, 1);
  Brain.Screen.print("R1 done B cal");
}

void printCalibrationTable() {
  printf("CAL ");
  printf("%d=%.1f ", HOME_COLUMN, homePositionDeg);
  for (int index = 0; index < COLUMN_COUNT; ++index) {
    printf("%d=%.1f ", index + 1, columnPositionsDeg[index]);
  }
  printf("\n");
}

void printCalibrationStatus(int selectedColumn) {
  printf(
    "CAL_STATUS selected=%d motor_deg=%.1f save=A select=UpDown finish=R1 enter=B\n",
    selectedColumn,
    GantryMotor.position(degrees)
  );
}

void moveToStoredHome() {
  GantryMotor.spinToPosition(homePositionDeg, degrees, MOTOR_SPEED_PCT, velocityUnits::pct, true);
}

void runCalibrationMode() {
  // Manual calibration mode lets you jog the gantry and save positions.
  int selectedColumn = HOME_COLUMN;
  bool wasUpPressed = false;
  bool wasDownPressed = false;
  bool wasAPressed = false;
  bool wasR1Pressed = false;
  int lastPrintedColumn = -1;
  double lastPrintedPosition = 1000000.0;

  GantryMotor.stop(hold);
  printf("CAL_MODE entered\n");
  printCalibrationStatus(selectedColumn);

  while (true) {
    double axisPercent = Controller1.Axis3.position(percentUnits::pct);
    if (std::fabs(axisPercent) <= JOG_DEADBAND_PCT) {
      axisPercent = 0.0;
    }

    if (axisPercent == 0.0) {
      GantryMotor.stop(hold);
    } else {
      double commandPercent = axisPercent > 0 ? CALIBRATION_JOG_SPEED_PCT : -CALIBRATION_JOG_SPEED_PCT;
      GantryMotor.spin(directionType::fwd, commandPercent, velocityUnits::pct);
    }

    bool upPressed = Controller1.ButtonUp.pressing();
    bool downPressed = Controller1.ButtonDown.pressing();
    bool aPressed = Controller1.ButtonA.pressing();
    bool r1Pressed = Controller1.ButtonR1.pressing();

    if (upPressed && !wasUpPressed && selectedColumn < COLUMN_COUNT) {
      selectedColumn += 1;
      printCalibrationStatus(selectedColumn);
    }

    if (downPressed && !wasDownPressed && selectedColumn > HOME_COLUMN) {
      selectedColumn -= 1;
      printCalibrationStatus(selectedColumn);
    }

    if (aPressed && !wasAPressed) {
      double currentPosition = GantryMotor.position(degrees);
      if (selectedColumn == HOME_COLUMN) {
        homePositionDeg = currentPosition;
      } else {
        columnPositionsDeg[selectedColumn - 1] = currentPosition;
      }
      printf("CAL_SAVED column=%d position=%.1f\n", selectedColumn, currentPosition);
      printCalibrationTable();
    }

    if (r1Pressed && !wasR1Pressed) {
      GantryMotor.stop(hold);
      moveToStoredHome();
      drawStatus("Cal saved", "Serial on");
      printf("CAL_MODE finished\n");
      printCalibrationTable();
      wait(600, msec);
      return;
    }

    wasUpPressed = upPressed;
    wasDownPressed = downPressed;
    wasAPressed = aPressed;
    wasR1Pressed = r1Pressed;

    double currentPosition = GantryMotor.position(degrees);
    if (selectedColumn != lastPrintedColumn || std::fabs(currentPosition - lastPrintedPosition) >= 5.0) {
      printCalibrationStatus(selectedColumn);
      lastPrintedColumn = selectedColumn;
      lastPrintedPosition = currentPosition;
    }

    drawCalibrationScreen(selectedColumn);
    wait(20, msec);
  }
}

void moveToColumn(int columnNumber) {
  // Move to the requested column, pause, then return home.
  if (columnNumber < 1 || columnNumber > COLUMN_COUNT) {
    drawStatus("Invalid column", "Expected 1 to 7");
    printf("ERR Invalid column %d\n", columnNumber);
    return;
  }

  double targetDegrees = columnPositionsDeg[columnNumber - 1];
  char statusLine[32];
  snprintf(statusLine, sizeof(statusLine), "Moving to column %d", columnNumber);
  drawStatus(statusLine, "Motor running...");

  GantryMotor.spinToPosition(targetDegrees, degrees, MOTOR_SPEED_PCT, velocityUnits::pct, true);

  char completeLine[32];
  snprintf(completeLine, sizeof(completeLine), "At column %d", columnNumber);
  drawStatus(completeLine, "Wait 5 sec");
  printf("OK %d\n", columnNumber);
  wait(COLUMN_DWELL_MS, msec);

  drawStatus("Return home", "Motor running");
  moveToStoredHome();

  drawStatus("Home: col 0", "Serial wait");
}

int serialReaderTask() {
  // Read newline-terminated column commands from stdin.
  while (true) {
    char inputBuffer[16];
    if (fgets(inputBuffer, sizeof(inputBuffer), stdin) != NULL) {
      int requestedColumn = atoi(inputBuffer);
      if (requestedColumn >= 1 && requestedColumn <= COLUMN_COUNT) {
        pendingSerialColumn = requestedColumn;
        serialCommandPending = true;
      } else {
        printf("ERR Invalid column %d\n", requestedColumn);
      }
    }
    wait(20, msec);
  }
  return 0;
}

int main() {
  // Home the gantry, start the reader thread, then wait for commands.
  GantryMotor.setStopping(hold);
  GantryMotor.setVelocity(MOTOR_SPEED_PCT, percent);
  GantryMotor.resetPosition();

  moveToStoredHome();
  drawStatus("Home: col 0", "Send 1-7");
  printf("READY\n");
  printCalibrationTable();
  thread serialThread = thread(serialReaderTask);

  while (true) {
    if (Controller1.ButtonB.pressing()) {
      while (Controller1.ButtonB.pressing()) {
        wait(20, msec);
      }
      runCalibrationMode();
      drawStatus("Home: col 0", "Send 1-7");
    }

    if (serialCommandPending) {
      int requestedColumn = pendingSerialColumn;
      serialCommandPending = false;
      moveToColumn(requestedColumn);
    }

    wait(20, msec);
  }
}
