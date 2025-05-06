import os
import subprocess
import sys
import argparse
import shutil
from pathlib import Path

def print_step(message):
    """Print a step message with formatting"""
    print(f"\n\033[1;34m===> {message}\033[0m")

def run_command(command, cwd=None):
    """Run a command and print its output"""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {result.stderr}")
        return False
    if result.stdout:
        print(result.stdout)
    return True

def check_python_version():
    """Check if Python version is 3.6+"""
    print_step("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print(f"Error: Python 3.6+ is required. You have {sys.version}")
        return False
    print(f"Using Python {version.major}.{version.minor}.{version.micro}")
    return True

def create_virtual_environment(venv_dir):
    """Create a virtual environment"""
    print_step(f"Creating virtual environment in {venv_dir}...")
    
    # Check if venv exists
    if os.path.exists(venv_dir):
        print(f"Virtual environment already exists at {venv_dir}")
        return True
    
    # Create venv
    return run_command([sys.executable, "-m", "venv", venv_dir])

def install_dependencies(venv_dir):
    """Install required packages"""
    print_step("Installing dependencies...")
    
    # Determine pip path
    if sys.platform == 'win32':
        pip_path = os.path.join(venv_dir, 'Scripts', 'pip')
    else:
        pip_path = os.path.join(venv_dir, 'bin', 'pip')
    
    # Upgrade pip
    run_command([pip_path, "install", "--upgrade", "pip"])
    
    # Install dependencies
    dependencies = [
        "pandas",
        "numpy",
        "plotly",
        "dash>=2.0.0",  # Ensure we have a recent version of Dash
        "dash-bootstrap-components",
        "xlrd==1.2.0",  # Specific version for Excel compatibility
        "openpyxl",
        "flask>=2.0.0",  # Required for file upload handling
        "werkzeug>=2.0.0"  # Required for file processing
    ]
    
    return run_command([pip_path, "install"] + dependencies)

def copy_sample_data(source_dir, data_dir):
    """Copy sample Excel files to data directory"""
    print_step("Setting up data directory...")
    
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Check for Excel files in the source directory
    excel_files = [f for f in os.listdir(source_dir) if f.endswith('.xlsx') and not f.startswith('~$')]
    
    if not excel_files:
        print("No Excel files found in the source directory")
        return False
    
    # Copy Excel files
    print(f"Copying {len(excel_files)} Excel files to {data_dir}")
    for file in excel_files:
        source_path = os.path.join(source_dir, file)
        dest_path = os.path.join(data_dir, file)
        shutil.copy2(source_path, dest_path)
        print(f"  Copied {file}")
    
    return True

def create_launcher_script(venv_dir, app_dir):
    """Create a script to launch the dashboard"""
    print_step("Creating launcher script...")
    
    if sys.platform == 'win32':
        # Windows batch script
        launcher_path = os.path.join(app_dir, 'run_dashboard.bat')
        with open(launcher_path, 'w') as f:
            f.write('@echo off\n')
            f.write(f'call "{os.path.join(venv_dir, "Scripts", "activate.bat")}"\n')
            f.write(f'python "{os.path.join(app_dir, "dashboard.py")}"\n')
            f.write('pause\n')
    else:
        # Unix shell script
        launcher_path = os.path.join(app_dir, 'run_dashboard.sh')
        with open(launcher_path, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write(f'source "{os.path.join(venv_dir, "bin", "activate")}"\n')
            f.write(f'python "{os.path.join(app_dir, "dashboard.py")}"\n')
        
        # Make executable
        os.chmod(launcher_path, 0o755)
    
    print(f"Created launcher script: {launcher_path}")
    return True

def setup_desktop_shortcut(app_dir):
    """Create desktop shortcut for the application"""
    print_step("Creating desktop shortcut...")
    
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    
    if not os.path.exists(desktop_path):
        print("Desktop directory not found")
        return False
    
    if sys.platform == 'win32':
        # Windows shortcut
        shortcut_path = os.path.join(desktop_path, "Budget Dashboard.lnk")
        try:
            import winshell
            from win32com.client import Dispatch
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = os.path.join(app_dir, 'run_dashboard.bat')
            shortcut.WorkingDirectory = app_dir
            shortcut.IconLocation = sys.executable
            shortcut.save()
            print(f"Created desktop shortcut: {shortcut_path}")
            return True
        except ImportError:
            print("Could not create Windows shortcut (winshell or win32com not installed)")
            return False
    else:
        # Unix .desktop file
        shortcut_path = os.path.join(desktop_path, "Budget Dashboard.desktop")
        with open(shortcut_path, 'w') as f:
            f.write("[Desktop Entry]\n")
            f.write("Type=Application\n")
            f.write("Name=Budget Dashboard\n")
            f.write(f"Exec={os.path.join(app_dir, 'run_dashboard.sh')}\n")
            f.write(f"Path={app_dir}\n")
            f.write("Terminal=false\n")
            f.write("Categories=Office;Finance;\n")
        
        # Make executable
        os.chmod(shortcut_path, 0o755)
        print(f"Created desktop shortcut: {shortcut_path}")
        return True

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description='Setup Budget Dashboard')
    parser.add_argument('--data-source', type=str, help='Directory containing Excel files')
    args = parser.parse_args()
    
    # Determine directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = script_dir
    data_dir = os.path.join(app_dir, 'data')
    venv_dir = os.path.join(app_dir, 'venv')
    
    print("Budget Dashboard Setup")
    print("======================")
    print(f"Application directory: {app_dir}")
    print(f"Data directory: {data_dir}")
    print(f"Virtual environment: {venv_dir}")
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Create virtual environment
    if not create_virtual_environment(venv_dir):
        print("Failed to create virtual environment")
        return 1
    
    # Install dependencies
    if not install_dependencies(venv_dir):
        print("Failed to install dependencies")
        return 1
    
    # Copy sample data
    source_dir = args.data_source if args.data_source else os.path.dirname(app_dir)
    if not copy_sample_data(source_dir, data_dir):
        print("Warning: Failed to copy sample data files")
    
    # Create launcher script
    if not create_launcher_script(venv_dir, app_dir):
        print("Failed to create launcher script")
        return 1
    
    # Create desktop shortcut
    try:
        setup_desktop_shortcut(app_dir)
    except Exception as e:
        print(f"Warning: Could not create desktop shortcut: {e}")
    
    print("\n\033[1;32mSetup completed successfully!\033[0m")
    
    if sys.platform == 'win32':
        print("\nTo run the dashboard:")
        print(f"1. Double-click on {os.path.join(app_dir, 'run_dashboard.bat')}")
        print("   OR")
        print("2. Use the desktop shortcut 'Budget Dashboard'")
    else:
        print("\nTo run the dashboard:")
        print(f"1. Execute: {os.path.join(app_dir, 'run_dashboard.sh')}")
        print("   OR")
        print("2. Use the desktop shortcut 'Budget Dashboard'")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())