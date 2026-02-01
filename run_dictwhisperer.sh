#!/bin/bash

# Determine the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Navigate to project directory
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    
    echo "Installing dependencies..."
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install -e .
else
    # Always activate
    source .venv/bin/activate
fi

# Run the GUI
echo "Starting DictWhisperer..."
python3 -m dictwhisperer.gui
