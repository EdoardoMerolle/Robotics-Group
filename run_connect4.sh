#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/.venv"

if [[ ! -d "$VENV_PATH" ]]; then
    echo "Virtual environment not found at $VENV_PATH"
    echo "Create it with: python3 -m venv .venv"
    return 1 2>/dev/null || exit 1
fi

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Running in a subshell. Use 'source ./run_connect4.sh' if you want to stay inside the venv afterwards."
fi

source "$VENV_PATH/bin/activate"
cd "$SCRIPT_DIR"

MODE="${1:-webcam}"

case "$MODE" in
    webcam)
        python3 connect4_webcam.py
        ;;
    terminal|ai|test)
        python3 connect4_ai_test.py
        ;;
    *)
        echo "Unknown mode: $MODE"
        echo "Usage: ./run_connect4.sh [webcam|terminal]"
        return 1 2>/dev/null || exit 1
        ;;
esac
