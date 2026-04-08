import os
from typing import Optional, Tuple

try:
    import serial
    from serial import SerialException
except ModuleNotFoundError:
    serial = None
    SerialException = Exception


DEFAULT_BAUD_RATE = 115200
DEFAULT_TIMEOUT_SECONDS = 1.0


class GantrySerialLink:
    def __init__(self, port: str, baud_rate: int = DEFAULT_BAUD_RATE, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self._serial = None

    def connect(self) -> Tuple[bool, str]:
        if serial is None:
            return False, "pyserial is not installed. Run `pip install pyserial` first."

        if self._serial is not None and self._serial.is_open:
            return True, f"Serial link already open on {self.port}."

        try:
            self._serial = serial.Serial(self.port, self.baud_rate, timeout=self.timeout, write_timeout=self.timeout)
        except SerialException as error:
            return False, f"Could not open serial port {self.port}: {error}"

        return True, f"Serial link opened on {self.port} at {self.baud_rate} baud."

    def close(self) -> None:
        if self._serial is not None and self._serial.is_open:
            self._serial.close()

    def send_column(self, zero_based_column: int) -> Tuple[bool, str]:
        if not 0 <= zero_based_column <= 6:
            return False, f"Invalid column index {zero_based_column}. Expected 0-6."

        connected, status = self.connect()
        if not connected:
            return False, status

        one_based_column = zero_based_column + 1
        command = f"{one_based_column}\n".encode("ascii")

        try:
            self._serial.reset_input_buffer()
            self._serial.write(command)
            self._serial.flush()

            reply = self._serial.readline().decode("ascii", errors="ignore").strip()
            if reply:
                return True, f"Sent column {one_based_column}. Brain replied: {reply}"
            return True, f"Sent column {one_based_column}."
        except SerialException as error:
            return False, f"Serial write failed on {self.port}: {error}"


def build_gantry_link_from_env() -> Optional[GantrySerialLink]:
    enabled = os.getenv("CONNECT4_ENABLE_SERIAL", "").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return None

    port = os.getenv("CONNECT4_SERIAL_PORT", "").strip()
    if not port:
        return None

    baud_rate_text = os.getenv("CONNECT4_SERIAL_BAUD", str(DEFAULT_BAUD_RATE)).strip()
    try:
        baud_rate = int(baud_rate_text)
    except ValueError:
        baud_rate = DEFAULT_BAUD_RATE

    return GantrySerialLink(port=port, baud_rate=baud_rate)
