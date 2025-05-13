#!/usr/bin/env python3
"""
Budget Dashboard Application Entry Point

This is the main entry point for running the budget dashboard application.
It creates and starts the Dash application server.
"""

from src.app import create_app

def main():
    """Main entry point when running as a script"""
    app = create_app()
    app.run(debug=True, port=8050)

if __name__ == '__main__':
    main()