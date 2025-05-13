# Budget Dashboard

An interactive dashboard for analyzing personal budget data from Excel files.

## Features

- Visualize monthly income, expenses, and investments
- Track spending by category and person
- Label transactions as Needs, Wants, Luxury, or Savings
- View recommendations based on spending patterns
- Calculate emergency fund needs based on spending history
- Analyze spending trends over time
- Upload Excel files directly through the dashboard interface
- Dynamic loading of files from the data directory
- Template files provided for easy data creation
- **NEW:** Modular codebase for easier maintenance
- **NEW:** Read income data from cell O3 in Excel files
- **NEW:** Toast notifications showing summary information after refresh/upload

## Installation

### Option 1: Automatic Setup (Recommended)

1. Run the setup script:

```bash
# On Windows
python setup.py

# On macOS/Linux
python3 setup.py
```

2. The setup script will:
   - Create a virtual environment
   - Install all dependencies
   - Copy sample Excel files
   - Create a launcher script
   - Create a desktop shortcut (if possible)

### Option 2: Manual Setup

1. Create a virtual environment:

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Dashboard

#### Option 1: Using the Launcher

```bash
# On Windows
run_dashboard.bat

# On macOS/Linux
./run_dashboard.sh
```

#### Option 2: Run Directly

```bash
# Make sure the virtual environment is activated
python run_dashboard.py
```

### Command Line Options

You can specify the directory containing Excel files:

```bash
python run_dashboard.py --data-dir /path/to/excel/files
```

## Excel File Format

The dashboard expects Excel files named by month (January.xlsx, Feb.xlsx, March.xlsx, April.xlsx) with the following format:

- Sheet 1: Summary sheet (can include cell O3 with total income value for the month)
- Sheet 2 or "Transactions" sheet: Contains transaction data
- Required columns: Category, Amount, Label (optional for N/W/L tagging)
- Optional columns: Date, Description, Who, Whom

**NEW:** If cell O3 in the first sheet contains a valid number, it will be used as the income value for that month. Otherwise, income will be estimated as 1.5x expenses.

## Labels for Transactions

You can label transactions in Excel files or through the dashboard:
- N = Needs (necessities)
- W = Wants (discretionary spending)
- L = Luxury (premium, non-essential items)
- S = Savings
- I = Investment

## Troubleshooting

- **Excel Loading Issues**: Make sure your Excel files use the correct format with the required columns
- **Missing Data**: Ensure data files are in the correct directory
- **Dependencies**: Run the setup script again if you encounter dependency errors
- **Excel Reading Errors**: Make sure xlrd version 1.2.0 is installed

## Customization

The dashboard code is organized in a modular structure under the `src` directory:

- `src/app.py` - Main application initialization
- `src/data/` - Data loading and processing
- `src/layouts/` - Dashboard layout components
- `src/components/` - Reusable UI components
- `src/callbacks/` - Dashboard interactivity
- `src/utils/` - Helper functions

You can modify these files to add new features or visualizations.

## Project Structure

```
budget_dashboard/
├── dashboard.py          # Original single-file implementation
├── dashboard_v2.py       # Entry point for refactored version
├── run_dashboard.py      # Runner script
├── run_dashboard.bat     # Windows launcher
├── run_dashboard.sh      # Unix launcher
├── requirements.txt      # Dependencies
├── setup.py              # Installation script
├── README.md             # This file
├── data/                 # Excel data files
├── templates/            # Template files
└── src/                  # Refactored modular code
    ├── app.py            # App initialization 
    ├── data/             # Data loading modules
    ├── layouts/          # Layout components
    ├── components/       # UI components
    ├── callbacks/        # Interactive callbacks
    └── utils/            # Helper functions
```