#!/usr/bin/env python3
"""
Budget Dashboard Runner Script

This script runs the refactored budget dashboard application.
"""

import os
import sys

# Add the parent directory to sys.path to allow importing the src package
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.app import create_app

def main():
    """Create and run the budget dashboard application"""
    app = create_app()
    app.run(debug=True, port=8050)

if __name__ == '__main__':
    main()