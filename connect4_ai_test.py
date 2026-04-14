import main
from gantry_serial import build_gantry_link_from_env


AI_DEPTH = 5


def reset_board():
    # Start from a clean board for each session.
    main.board = []
    main.CreateBoard()


def print_status():
    main.PrintBoard()
    print(f"\nAI search depth: {AI_DEPTH}")


def get_human_move():
    # Read a legal move from the terminal.
    while True:
        try:
            col = int(input("\nYour move (1-7, 0 to quit): "))
        except KeyboardInterrupt:
            print("\nExiting.")
            return None
        except EOFError:
            print("\nNo input available. Exiting.")
            return None
        except ValueError:
            print("Enter a number between 0 and 7.")
            continue

        if col == 0:
            return None
        if not 1 <= col <= 7:
            print("Column must be between 1 and 7.")
            continue
        if col - 1 not in main.GetAvailableCols(main.board):
            print("That column is full.")
            continue
        return col - 1


def get_ai_move():
    return main.BestMove(main.board, main.symbol2, main.symbol1, maxDepth=AI_DEPTH)


def apply_move(col, symbol):
    updated = main.ApplyMove(main.board, col, symbol)
    if updated is None:
        return False
    main.board = updated
    return True


def choose_first_player():
    # Let the user choose who moves first.
    while True:
        try:
            choice = input("Who goes first? [h]uman / [a]i: ").strip().lower()
        except KeyboardInterrupt:
            print("\nExiting.")
            return None
        except EOFError:
            print("\nNo input available. Defaulting to human first.")
            return "human"
        if choice in {"h", "human"}:
            return "human"
        if choice in {"a", "ai"}:
            return "ai"
        print("Enter 'h' or 'a'.")


def main_loop():
    reset_board()
    current = choose_first_player()
    gantry_link = build_gantry_link_from_env()
    if current is None:
        return

    if gantry_link is not None:
        connected, status = gantry_link.connect()
        print(status)
        if not connected:
            gantry_link = None

    try:
        while True:
            # Alternate turns until someone wins or the board fills.
            print_status()

            if current == "human":
                col = get_human_move()
                if col is None:
                    print("Exiting.")
                    return
                apply_move(col, main.symbol1)
                if main.IsWinningBoard(main.symbol1, main.board):
                    print_status()
                    print("\nHuman wins.")
                    return
            else:
                col = get_ai_move()
                if col is None:
                    print("\nNo legal move available.")
                    return
                apply_move(col, main.symbol2)
                print(f"\nAI plays column {col + 1}.")
                if gantry_link is not None:
                    sent, status = gantry_link.send_column(col)
                    print(status)
                    if not sent:
                        gantry_link = None
                if main.IsWinningBoard(main.symbol2, main.board):
                    print_status()
                    print("\nAI wins.")
                    return

            if main.IsFull(main.board):
                print_status()
                print("\nDraw.")
                return
            current = "ai" if current == "human" else "human"
    finally:
        if gantry_link is not None:
            gantry_link.close()


if __name__ == "__main__":
    main_loop()
