# Budget Dashboard

An interactive dashboard for analyzing personal budget data from Excel files.

## Features

- Visualize monthly income, expenses, and investments
- Track spending by category and person
- Label transactions as Needs, Wants, Luxury, or Savings
- View recommendations based on spending patterns
- Calculate emergency fund needs based on spending history
- Analyze spending trends over time
- **NEW:** Upload Excel files directly through the dashboard interface
- **NEW:** Dynamic loading of files from the data directory
- **NEW:** Template files provided for easy data creation

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
python dashboard.py
```

### Command Line Options

You can specify the directory containing Excel files:

```bash
python dashboard.py --data-dir /path/to/excel/files
```

## Excel File Format

The dashboard expects Excel files named by month (January.xlsx, Feb.xlsx, March.xlsx, April.xlsx) with the following format:

- The transaction data should be in a sheet named "Transactions" or the second sheet
- Required columns: Category, Amount, Label (optional for N/W/L tagging)
- Optional columns: Date, Description, Who, Whom

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

You can modify the dashboard code in dashboard.py to add new features or visualizations.