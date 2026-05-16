#!/bin/bash
# Monk Clock GUI launcher
# Assumes venv is in the same directory as this script's parent
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/monkclock_gui.py" "$@"