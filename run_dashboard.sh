#!/bin/bash
# Run the refactored budget dashboard application

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists
source "$SCRIPT_DIR/venv/bin/activate"
echo "Activated virtual environment"

# Run the application
python "$SCRIPT_DIR/run_dashboard.py"
