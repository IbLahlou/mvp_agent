#!/bin/bash

LOGS_DIR="logs"

case "$1" in
    --latest)
        latest=$(ls -t "$LOGS_DIR"/*.md 2>/dev/null | head -n 1)
        if [ -f "$latest" ]; then
            cat "$latest"
        else
            echo "No logs found"
        fi
        ;;
    --list)
        ls -lt "$LOGS_DIR"/*.md 2>/dev/null
        ;;
    --clear)
        rm -f "$LOGS_DIR"/*.md
        echo "Logs cleared"
        ;;
    *)
        echo "Usage: $0 [--latest|--list|--clear]"
        ;;
esac
