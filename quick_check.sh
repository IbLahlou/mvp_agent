# Check Python version
if python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null; then
    python3 -m venv venv
else
    echo "Error: Python 3.10 or higher is required"
    exit 1
fi