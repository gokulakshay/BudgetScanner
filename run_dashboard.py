#!/usr/bin/env python3
"""
Budget Dashboard Launcher
-------------------------
This script is a simple launcher for the Budget Dashboard application.
It ensures the application runs correctly regardless of the environment.

Usage:
  python run_dashboard.py [--data-dir PATH]

Options:
  --data-dir PATH    Specify the directory containing Excel files
"""

import os
import sys
import argparse
import importlib.util

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "pandas",
        "numpy",
        "plotly",
        "dash",
        "dash_bootstrap_components",
        "xlrd"
    ]
    
    missing_packages = []
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease run setup.py first to install all dependencies.")
        print("  python setup.py")
        return False
    
    return True

def find_dashboard_module():
    """Find the dashboard.py module path"""
    # Check current directory first
    if os.path.exists("dashboard.py"):
        return "dashboard.py"
    
    # Check script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dashboard_path = os.path.join(script_dir, "dashboard.py")
    if os.path.exists(dashboard_path):
        return dashboard_path
    
    # Search standard locations
    potential_paths = [
        os.path.join(os.path.expanduser("~"), "budget_dashboard", "dashboard.py"),
        os.path.join(os.path.dirname(script_dir), "dashboard.py")
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            return path
    
    return None

def load_and_run_dashboard(dashboard_path, args):
    """Load the dashboard module and run it"""
    # Change to the directory of the dashboard script
    os.chdir(os.path.dirname(os.path.abspath(dashboard_path)))
    
    # Save original sys.argv and set new one with our args
    original_argv = sys.argv
    sys.argv = [dashboard_path]
    
    if args.data_dir:
        sys.argv.extend(["--data-dir", args.data_dir])
    
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("dashboard", dashboard_path)
        dashboard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dashboard)
        
        # Run the dashboard
        dashboard.main()
    except Exception as e:
        print(f"Error running dashboard: {e}")
        return 1
    finally:
        # Restore original sys.argv
        sys.argv = original_argv
    
    return 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run Budget Dashboard')
    parser.add_argument('--data-dir', type=str, help='Directory containing Excel files')
    args = parser.parse_args()
    
    print("Budget Dashboard Launcher")
    print("=========================")
    
    # Check if dependencies are installed
    if not check_dependencies():
        return 1
    
    # Find dashboard module
    dashboard_path = find_dashboard_module()
    if not dashboard_path:
        print("Error: Could not find dashboard.py")
        print("Please make sure the script is in the same directory as dashboard.py")
        return 1
    
    print(f"Using dashboard module: {dashboard_path}")
    
    # Load and run dashboard
    return load_and_run_dashboard(dashboard_path, args)

if __name__ == "__main__":
    sys.exit(main())