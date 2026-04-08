import time

from gantry_serial import build_gantry_link_from_env


def main():
    link = build_gantry_link_from_env()
    if link is None:
        print("Set CONNECT4_ENABLE_SERIAL=1 and CONNECT4_SERIAL_PORT before running this test.")
        return

    connected, status = link.connect()
    print(status)
    if not connected:
        return

    try:
        while True:
            raw = input("Column to send (1-7, q to quit): ").strip().lower()
            if raw in {"q", "quit", "exit"}:
                break

            try:
                column = int(raw)
            except ValueError:
                print("Enter a whole number between 1 and 7.")
                continue

            if not 1 <= column <= 7:
                print("Column must be between 1 and 7.")
                continue

            sent, reply = link.send_column(column - 1)
            print(reply)
            time.sleep(0.2)
    finally:
        link.close()


if __name__ == "__main__":
    main()
