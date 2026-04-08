import argparse
import glob
import time

from gantry_serial import GantrySerialLink, DEFAULT_BAUD_RATE

try:
    from serial.tools import list_ports
except ModuleNotFoundError:
    list_ports = None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send test column commands to the VEX EXP gantry controller."
    )
    parser.add_argument(
        "--port",
        help="Serial port for the EXP brain, for example /dev/ttyACM0 or COM3.",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=DEFAULT_BAUD_RATE,
        help=f"Serial baud rate. Default: {DEFAULT_BAUD_RATE}.",
    )
    parser.add_argument(
        "--mode",
        choices=["manual", "sweep"],
        default="manual",
        help="manual = type columns yourself, sweep = send a sequence automatically.",
    )
    parser.add_argument(
        "--columns",
        type=int,
        nargs="+",
        default=[1, 4, 7, 4, 2, 6, 4],
        help="Columns to send in sweep mode.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds to wait between commands in sweep mode.",
    )
    return parser.parse_args()


def discover_candidate_ports():
    candidates = []

    if list_ports is not None:
        candidates.extend(port.device for port in list_ports.comports())

    for pattern in ("/dev/ttyACM*", "/dev/ttyUSB*"):
        candidates.extend(sorted(glob.glob(pattern)))

    seen = set()
    unique_candidates = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            unique_candidates.append(candidate)
    return unique_candidates


def connect_with_auto_detect(port, baud_rate):
    ports_to_try = [port] if port else discover_candidate_ports()
    if not ports_to_try:
        return None, "No serial ports found. Connect the EXP brain and try again."

    last_status = None
    for candidate in ports_to_try:
        link = GantrySerialLink(port=candidate, baud_rate=baud_rate)
        connected, status = link.connect()
        print(status)
        if connected:
            return link, f"Using serial port {candidate}."
        last_status = status

    return None, last_status or "Could not connect to any detected serial port."


def send_manual(link):
    print("Manual mode.")
    print("Enter a column from 1 to 7, or q to quit.")

    while True:
        raw = input("Column: ").strip().lower()
        if raw in {"q", "quit", "exit"}:
            break

        try:
            column = int(raw)
        except ValueError:
            print("Please enter a whole number from 1 to 7.")
            continue

        if not 1 <= column <= 7:
            print("Column must be between 1 and 7.")
            continue

        sent, status = link.send_column(column - 1)
        print(status)
        if not sent:
            break


def send_sweep(link, columns, delay_seconds):
    print(f"Sweep mode. Sending columns: {columns}")

    for column in columns:
        if not 1 <= column <= 7:
            print(f"Skipping invalid column {column}.")
            continue

        sent, status = link.send_column(column - 1)
        print(status)
        if not sent:
            break

        time.sleep(delay_seconds)


def main():
    args = parse_args()
    link, status = connect_with_auto_detect(args.port, args.baud)
    print(status)
    if link is None:
        return

    try:
        if args.mode == "manual":
            send_manual(link)
        else:
            send_sweep(link, args.columns, args.delay)
    finally:
        link.close()


if __name__ == "__main__":
    main()
