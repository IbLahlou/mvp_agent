#!/bin/bash

RECORD_DIR="src/services/service_records"
mkdir -p "$RECORD_DIR"

check_records() {
    echo "Checking records..."
    find "$RECORD_DIR" -name "*.md" -type f -exec sh -c '
        echo "Record: {}"
        head -n 5 "{}"
        echo "---"
    ' \;
}

clean_records() {
    echo "Cleaning old records..."
    find "$RECORD_DIR" -name "*.md" -type f -mtime +30 -delete
}

case "$1" in
    --check)
        check_records
        ;;
    --clean)
        clean_records
        ;;
    *)
        echo "Usage: $0 [--check|--clean]"
        ;;
esac
