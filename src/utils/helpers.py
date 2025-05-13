"""
Helper functions for the budget dashboard application
"""
import os
import sys
import argparse
from datetime import datetime

def get_data_dir():
    """Get the data directory path"""
    # If running as a script directly
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_path = os.path.dirname(sys.executable)
    else:
        # Running as script
        app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Check for command line arguments
    parser = argparse.ArgumentParser(description='Budget Dashboard')
    parser.add_argument('--data-dir', type=str, help='Directory containing Excel files')
    args, _ = parser.parse_known_args()
    
    if args.data_dir:
        data_dir = os.path.abspath(args.data_dir)
        # Create directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        return data_dir
    
    # Default data directory is inside the app directory
    default_data_dir = os.path.join(app_path, 'data')
    
    # Create data directory if it doesn't exist
    if not os.path.exists(default_data_dir):
        os.makedirs(default_data_dir)
        print(f"Created data directory at {default_data_dir}")
    
    return default_data_dir

def format_inr(value):
    """Format a number as Indian Rupees"""
    return f"₹{value:,.2f}"

def get_template_path(filename):
    """Get the path to a template file"""
    # Check if file exists in the templates directory
    app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    templates_dir = os.path.join(app_path, 'templates')
    
    # If templates directory doesn't exist, create it
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        
    template_path = os.path.join(templates_dir, filename)
    
    # If the template doesn't exist in templates dir, check data dir
    if not os.path.exists(template_path):
        data_dir = get_data_dir()
        data_template_path = os.path.join(data_dir, filename)
        
        # If it exists in data dir, move it to templates dir
        if os.path.exists(data_template_path):
            # Copy it to templates dir
            import shutil
            shutil.copy2(data_template_path, template_path)
            print(f"Moved template {filename} to templates directory")
            return template_path
        else:
            # Template doesn't exist anywhere
            return None
    
    return template_path