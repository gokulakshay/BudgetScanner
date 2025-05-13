import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import flask
from dash import Dash, dcc, html, Input, Output, callback, dash_table, State, dash, no_update
import dash_bootstrap_components as dbc
from datetime import datetime
import sys
import argparse
import base64
import io
import shutil

def get_data_dir():
    """Get the data directory path"""
    # If running as a script directly
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_path = os.path.dirname(sys.executable)
    else:
        # Running as script
        app_path = os.path.dirname(os.path.abspath(__file__))
    
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

# This will be populated dynamically
months = []
month_names = []  # For display

# Function to load and process data
def get_excel_files():
    """Get list of Excel files in the data directory"""
    data_dir = get_data_dir()
    
    # List of template files to exclude from data loading
    template_files = ['Template.xlsx', 'BlankTemplate.xlsx']
    
    # Get all Excel files but exclude templates
    excel_files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx') and f not in template_files]
    
    return excel_files, data_dir

def has_excel_files():
    """Check if there are any Excel files in the data directory"""
    excel_files, _ = get_excel_files()
    return len(excel_files) > 0

def get_template_path(filename):
    """Get the path to a template file"""
    # Check if file exists in the templates directory
    app_path = os.path.dirname(os.path.abspath(__file__))
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

def load_data():
    # Get the data directory and Excel files
    data_dir = get_data_dir()
    print("Loading data from {}".format(data_dir))
    
    # Get excel files and extract month names
    global months, month_names
    excel_files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]
    
    # Reset global month lists
    months = []
    month_names = []
    
    for file in excel_files:
        # Extract month name without extension
        month = os.path.splitext(file)[0]
        months.append(month)
        
        # Convert abbreviated months to full names for display
        if month == "Jan": 
            month_name = "January"
        elif month == "Feb":
            month_name = "February"
        elif month == "Mar" or month == "March":
            month_name = "March"
        elif month == "Apr" or month == "April":
            month_name = "April"
        elif month == "May":
            month_name = "May"
        elif month == "Jun" or month == "June":
            month_name = "June"
        elif month == "Jul" or month == "July":
            month_name = "July"
        elif month == "Aug" or month == "August":
            month_name = "August"
        elif month == "Sep" or month == "Sept" or month == "September":
            month_name = "September"
        elif month == "Oct" or month == "October":
            month_name = "October"
        elif month == "Nov" or month == "November":
            month_name = "November"
        elif month == "Dec" or month == "December":
            month_name = "December"
        else:
            # If no match, use the file name as is
            month_name = month
            
        month_names.append(month_name)
    
    # Sort months chronologically if possible
    month_order = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    
    if month_names:
        # Create pairs of (month_file, month_name) for sorting
        pairs = list(zip(months, month_names))
        
        # Try to sort by month order
        try:
            sorted_pairs = sorted(pairs, key=lambda pair: month_order.get(pair[1], 13))
            months, month_names = zip(*sorted_pairs)
            # Convert back to lists
            months = list(months)
            month_names = list(month_names)
        except:
            # If sorting fails, keep original order
            pass
    
    # Lists to store processed data
    summary_data = {
        'Month': [],
        'Total Income': [],
        'Total Expenses': [],
        'Investments': [],
        'Surplus': [],
        'Top Expense Category': [],
        'Top Expense Amount': []
    }
    
    # Dictionary to store transactions by month
    all_transactions = {}
    
    # Dictionary to store category expenses by month
    category_monthly = {}
    
    # Track errors
    errors = []
    
    # Try to use xlrd for reading Excel files
    try:
        import xlrd
        print(f"Using xlrd version {xlrd.__VERSION__} to read Excel files...")
        
        # Process each file
        for month, month_name in zip(months, month_names):
            file_path = os.path.join(data_dir, f"{month}.xlsx")
            print(f"Processing {file_path}...")
            
            if not os.path.exists(file_path):
                error_msg = f"File not found: {file_path}"
                errors.append(error_msg)
                print(error_msg)
                continue
            
            try:
                # Open the workbook with xlrd
                wb = xlrd.open_workbook(file_path)
                print(f"  Available sheets: {wb.sheet_names()}")
                
                # Try to find the transactions sheet
                trans_sheet = None
                if len(wb.sheet_names()) >= 2:
                    trans_sheet = wb.sheet_by_index(1)  # Use the second sheet
                elif 'Transactions' in wb.sheet_names():
                    trans_sheet = wb.sheet_by_name('Transactions')
                elif wb.nsheets > 0:
                    trans_sheet = wb.sheet_by_index(0)  # Use the first sheet if no other option
                
                if trans_sheet is None:
                    error_msg = f"No sheets found in {file_path}"
                    errors.append(error_msg)
                    raise ValueError(error_msg)
                
                print(f"  Reading sheet: {trans_sheet.name}")
                
                # Get column names from the first row
                col_names = [trans_sheet.cell_value(0, col_idx) for col_idx in range(trans_sheet.ncols)]
                print(f"  Column names: {col_names}")
                
                # Create DataFrame from the sheet data
                data = []
                for row_idx in range(1, trans_sheet.nrows):  # Skip header row
                    row_dict = {}
                    for col_idx, col_name in enumerate(col_names):
                        if col_name:  # Skip empty column names
                            cell_value = trans_sheet.cell_value(row_idx, col_idx)
                            # Handle dates if cell type is XL_CELL_DATE
                            if trans_sheet.cell_type(row_idx, col_idx) == xlrd.XL_CELL_DATE:
                                date_tuple = xlrd.xldate_as_tuple(cell_value, wb.datemode)
                                # Convert to datetime 
                                from datetime import datetime
                                cell_value = datetime(*date_tuple)
                            row_dict[col_name] = cell_value
                    data.append(row_dict)
                
                trans_df = pd.DataFrame(data)
                
                # Ensure Date column is properly converted to datetime if it exists
                if 'Date' in trans_df.columns:
                    try:
                        trans_df['Date'] = pd.to_datetime(trans_df['Date'], errors='coerce')
                    except Exception as e:
                        print(f"  Warning: Error converting dates: {e}")
                        # If conversion fails, at least ensure the column exists
                        if 'Date' not in trans_df.columns:
                            from datetime import datetime
                            trans_df['Date'] = datetime.now()
                
                # Add Month column 
                trans_df['Month'] = month_name
                
                # Ensure all required columns exist
                required_columns = ['Category', 'Amount', 'Label']
                for col in required_columns:
                    if col not in trans_df.columns:
                        error_msg = f"Required column '{col}' not found in {file_path}"
                        errors.append(error_msg)
                        raise ValueError(error_msg)
                
                # Validate Label column values (must be N, W, or L)
                if 'Label' in trans_df.columns:
                    # Convert to uppercase strings and handle NAs
                    trans_df['Label'] = trans_df['Label'].astype(str).str.upper()
                    
                    # Map the short codes to full labels
                    label_mapping = {
                        'N': 'Needs',
                        'W': 'Wants',
                        'L': 'Luxury',
                        'S': 'Savings',
                        'I': 'Investment'
                    }
                    
                    # Check for invalid labels
                    valid_labels = list(label_mapping.keys())
                    invalid_labels = trans_df[~trans_df['Label'].isin(valid_labels + ['NAN', 'NONE', ''])]['Label'].unique()
                    
                    if len(invalid_labels) > 0:
                        error_msg = f"Invalid label values found in {file_path}: {', '.join(invalid_labels)}"
                        errors.append(error_msg)
                        raise ValueError(error_msg)
                    
                    # Map short codes to full labels
                    trans_df['Label'] = trans_df['Label'].map(lambda x: label_mapping.get(x, '') if x in valid_labels else '')
                    
                # Automatically assign 'Savings' label to investment transactions if not already labeled
                if 'Category' in trans_df.columns:
                    investment_mask = trans_df['Category'].astype(str).str.startswith('Investment') & (trans_df['Label'] == '')
                    trans_df.loc[investment_mask, 'Label'] = 'Savings'
                
                # Check for and add missing columns with defaults if needed
                if 'Date' not in trans_df.columns:
                    print(f"  Warning: 'Date' column not found in {file_path}, adding default values")
                    # Create default dates for the month
                    month_num = month_names.index(month_name) + 1
                    from datetime import datetime
                    trans_df['Date'] = datetime(2025, month_num, 1)
                
                if 'Description' not in trans_df.columns:
                    print(f"  Warning: 'Description' column not found in {file_path}, adding default values")
                    trans_df['Description'] = trans_df['Category'] + " expense"
                
                if 'Who' not in trans_df.columns:
                    print(f"  Warning: 'Who' column not found in {file_path}, adding default values")
                    trans_df['Who'] = 'Unknown'
                
                if 'Whom' not in trans_df.columns:
                    print(f"  Warning: 'Whom' column not found in {file_path}, adding default values")
                    trans_df['Whom'] = 'Vendor'
                
                # Store transactions
                all_transactions[month_name] = trans_df
                
                # Calculate total expenses (excluding investments)
                investment_mask = trans_df['Category'].astype(str).str.startswith('Investment')
                regular_expenses = trans_df[~investment_mask]['Amount'].sum()
                investment_amount = trans_df[investment_mask]['Amount'].sum()
                
                # Try to read income from cell O3 in the first sheet
                try:
                    # Get the first sheet in the workbook
                    first_sheet = wb.sheet_by_index(0)
                    
                    # Read income from cell O3 (row 2, column 14 in 0-indexed system)
                    if first_sheet.ncols > 14 and first_sheet.nrows > 2:
                        income_cell_value = first_sheet.cell_value(2, 14)  # O3 in 0-indexed is (2,14)
                        # Convert to numeric if possible
                        try:
                            income = float(income_cell_value)
                            print(f"  Income read from cell O3: ₹{income:.2f}")
                        except (ValueError, TypeError):
                            # Fallback to formula if cell doesn't contain a valid number
                            income = regular_expenses * 1.5
                            print(f"  Could not convert O3 cell value '{income_cell_value}' to number, using calculated income: ₹{income:.2f}")
                    else:
                        # Sheet doesn't have enough rows/columns, use calculated income
                        income = regular_expenses * 1.5
                        print(f"  First sheet doesn't have cell O3, using calculated income: ₹{income:.2f}")
                except Exception as e:
                    # Fallback to formula if there's any error reading the cell
                    income = regular_expenses * 1.5
                    print(f"  Error reading income from cell O3: {str(e)}, using calculated income: ₹{income:.2f}")
                
                # Calculate surplus
                surplus = income - regular_expenses
                
                # Group expenses by category (excluding investments)
                category_expenses_month = trans_df[~investment_mask].groupby('Category')['Amount'].sum().to_dict()
                category_monthly[month_name] = category_expenses_month
                
                # Find top expense category
                if not trans_df[~investment_mask].empty:
                    top_category_series = trans_df[~investment_mask].groupby('Category')['Amount'].sum()
                    top_category_name = top_category_series.idxmax() if not top_category_series.empty else "Unknown"
                    top_category_amount = top_category_series.max() if not top_category_series.empty else 0
                else:
                    top_category_name = "Unknown"
                    top_category_amount = 0
                
                # Store summary data
                summary_data['Month'].append(month_name)
                summary_data['Total Income'].append(income)
                summary_data['Total Expenses'].append(regular_expenses)
                summary_data['Investments'].append(investment_amount)
                summary_data['Surplus'].append(surplus)
                summary_data['Top Expense Category'].append(top_category_name)
                summary_data['Top Expense Amount'].append(top_category_amount)
                
                print(f"  Income: ₹{income:.2f}")
                print(f"  Regular Expenses: ₹{regular_expenses:.2f}")
                print(f"  Investments: ₹{investment_amount:.2f}")
                print(f"  Surplus: ₹{surplus:.2f}")
                
            except Exception as e:
                error_msg = f"Error processing {file_path}: {str(e)}"
                errors.append(error_msg)
                print(error_msg)
    
    except Exception as e:
        error_msg = f"Error initializing xlrd: {str(e)}"
        errors.append(error_msg)
        print(error_msg)
    
    # If we couldn't load any data, return empty DataFrames and error messages
    if not all_transactions:
        error_msg = "Failed to load any data from Excel files. Please check file format and try again."
        errors.append(error_msg)
        print(error_msg)
        
        # Create empty DataFrames
        summary_df = pd.DataFrame(columns=['Month', 'Total Income', 'Total Expenses', 'Investments', 'Surplus', 'Top Expense Category', 'Top Expense Amount'])
        all_trans_df = pd.DataFrame(columns=['Date', 'Description', 'Category', 'Amount', 'Who', 'Whom', 'Month', 'Label'])
        monthly_category_df = pd.DataFrame(columns=['Category'] + month_names)
        
        # Pass errors as global variable to be displayed in the dashboard
        global dashboard_errors
        dashboard_errors = errors
        
        return summary_df, all_trans_df, monthly_category_df
    
    # Create summary DataFrame from real data
    summary_df = pd.DataFrame(summary_data)
    
    # Combine all transactions into a single DataFrame
    all_trans_df = pd.concat(all_transactions.values(), ignore_index=True)
    
    # Create category analysis
    # First, get all unique categories
    all_categories = set()
    for month_expenses in category_monthly.values():
        all_categories.update(month_expenses.keys())
    
    # Create DataFrame with months as columns
    monthly_category_data = []
    for category in sorted(all_categories):
        row = {'Category': category}
        for month in month_names:
            if month in category_monthly and category in category_monthly[month]:
                row[month] = category_monthly[month][category]
            else:
                row[month] = 0
        monthly_category_data.append(row)
    
    monthly_category_df = pd.DataFrame(monthly_category_data)
    
    return summary_df, all_trans_df, monthly_category_df

# Define function to format currency values in INR
def format_inr(value):
    return f"₹{value:,.2f}"

# Initialize global DataFrames for use across callbacks
summary_df = pd.DataFrame()
all_transactions_df = pd.DataFrame()
category_monthly_df = pd.DataFrame()

def create_app():
    """Create and return the Dash app instance"""
    # Reset global variables first to ensure fresh loading
    global summary_df, all_transactions_df, category_monthly_df, months, month_names
    
    # Initialize empty lists for months
    months = []
    month_names = []
    
    # Load data fresh
    print("Initial loading of data...")
    summary_df, all_transactions_df, category_monthly_df = load_data()
    
    # Clean up data - handle null values
    if not all_transactions_df.empty:
        # Fill NaN values in categorical columns
        all_transactions_df['Who'] = all_transactions_df['Who'].fillna('Unknown')
        all_transactions_df['Category'] = all_transactions_df['Category'].fillna('Uncategorized')
        all_transactions_df['Description'] = all_transactions_df['Description'].fillna('-')
        all_transactions_df['Whom'] = all_transactions_df['Whom'].fillna('Unknown')
        all_transactions_df['Label'] = all_transactions_df['Label'].fillna('')
        
        # Automatically mark investments as savings
        investment_mask = all_transactions_df['Category'].astype(str).str.startswith('Investment')
        all_transactions_df.loc[investment_mask, 'Label'] = 'Savings'
    
    # Calculate YTD values
    ytd_income = summary_df['Total Income'].sum() if not summary_df.empty else 0
    ytd_expenses = summary_df['Total Expenses'].sum() if not summary_df.empty else 0
    ytd_investments = summary_df['Investments'].sum() if not summary_df.empty else 0
    ytd_surplus = summary_df['Surplus'].sum() if not summary_df.empty else 0
    
    print(f"Initial data load complete. YTD Income: {ytd_income}, YTD Expenses: {ytd_expenses}")
    
    # Calculate averages, preventing division by zero
    month_count = max(1, len(months))  # Ensure at least 1 to prevent division by zero
    avg_monthly_income = ytd_income / month_count
    avg_monthly_expenses = ytd_expenses / month_count
    avg_monthly_investments = ytd_investments / month_count
    avg_monthly_surplus = ytd_surplus / month_count
    
    # Calculate average monthly needs based on labeled transactions
    if not all_transactions_df.empty and 'Label' in all_transactions_df.columns:
        # Get transactions labeled as 'Needs'
        needs_transactions = all_transactions_df[all_transactions_df['Label'] == 'Needs']
        if not needs_transactions.empty:
            # Calculate total needs expenses across all months
            total_needs = needs_transactions['Amount'].sum()
            # Calculate average monthly needs (total / number of months)
            avg_monthly_needs = total_needs / len(months)
            # Calculate emergency fund suggestion (6 times monthly needs)
            emergency_fund_suggestion = avg_monthly_needs * 6
        else:
            # Default values if no needs are found
            avg_monthly_needs = avg_monthly_expenses * 0.5  # Assume 50% of expenses are needs if no labels
            emergency_fund_suggestion = avg_monthly_needs * 6
    else:
        # Default values if no labeled data exists
        avg_monthly_needs = avg_monthly_expenses * 0.5
        emergency_fund_suggestion = avg_monthly_needs * 6
    
    # Find highest/lowest months safely
    if not summary_df.empty and len(summary_df) > 0:
        # Only try to find max/min values if we have data
        try:
            highest_expense_month = summary_df.loc[summary_df['Total Expenses'].idxmax(), 'Month']
            highest_expense_amount = summary_df['Total Expenses'].max()
            highest_surplus_month = summary_df.loc[summary_df['Surplus'].idxmax(), 'Month']
            highest_surplus_amount = summary_df['Surplus'].max()
            highest_investment_month = summary_df.loc[summary_df['Investments'].idxmax(), 'Month'] 
            highest_investment_amount = summary_df['Investments'].max()
            lowest_expense_month = summary_df.loc[summary_df['Total Expenses'].idxmin(), 'Month']
            lowest_expense_amount = summary_df['Total Expenses'].min()
            top_expense_category = summary_df.loc[summary_df['Top Expense Amount'].idxmax(), 'Top Expense Category'] if summary_df['Top Expense Amount'].notna().any() else 'Unknown'
        except:
            # If anything fails, use defaults
            highest_expense_month = highest_surplus_month = highest_investment_month = lowest_expense_month = 'Unknown'
            highest_expense_amount = highest_surplus_amount = highest_investment_amount = lowest_expense_amount = 0
            top_expense_category = 'Unknown'
    else:
        highest_expense_month = highest_surplus_month = highest_investment_month = lowest_expense_month = 'Unknown'
        highest_expense_amount = highest_surplus_amount = highest_investment_amount = lowest_expense_amount = 0
        top_expense_category = 'Unknown'
    
    # Initialize global variable for dashboard errors
    global dashboard_errors
    dashboard_errors = []
    
    # Initialize the Dash app with callback exceptions suppressed
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
    
    # Initialize a toast container for displaying refresh notifications
    toast_container = html.Div(
        [
            dbc.Toast(
                id="refresh-toast",
                header="Dashboard Refreshed",
                is_open=False,
                dismissable=True,
                duration=8000,  # Duration in milliseconds (8 seconds)
                icon="success",
                style={"position": "fixed", "top": 20, "right": 20, "width": "400px", "zIndex": 1000}
            ),
        ]
    )
    
    # Get unique people and categories for dropdown options, removing null values
    if not all_transactions_df.empty:
        unique_people = [person for person in all_transactions_df['Who'].unique() if person is not None and pd.notna(person)]
        unique_categories = [cat for cat in all_transactions_df['Category'].unique() if cat is not None and pd.notna(cat)]
    else:
        unique_people = []
        unique_categories = []
    
    # Create transaction label options
    label_options = [
        {'label': 'Needs (N)', 'value': 'Needs'},
        {'label': 'Wants (W)', 'value': 'Wants'},
        {'label': 'Luxury (L)', 'value': 'Luxury'},
        {'label': 'Savings (S)', 'value': 'Savings'},
        {'label': 'Investment (I)', 'value': 'Investment'}
    ]
    
    # Define the app layout
    app.layout = dbc.Container([
        # Toast container for notifications
        toast_container,
        
        dbc.Row([
            dbc.Col([
                html.H1("Personal Budget Dashboard - 2025", className="text-center mt-3 mb-4"),
            ], width=12)
        ]),
        
        # File Upload Component
        dbc.Row([
            dbc.Col([
                html.H4("Upload Excel Files", className="text-center mb-2"),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    # Allow multiple files to be uploaded
                    multiple=True
                ),
                html.Div(id='upload-output'),
                
                # Available Files
                html.Div([
                    html.H5("Available Files:", className="mt-3 mb-2"),
                    html.Div(id='available-files')
                ]),
                
                # No files message
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3("No Excel Files Found", className="text-center text-danger mb-3"),
                                html.P("Please upload at least one Excel file to see the dashboard.", 
                                      className="text-center"),
                                html.P("The Excel files should contain transaction data with columns for Date, Amount, Description, Category, etc.", 
                                      className="text-center font-italic"),
                                html.Hr(),
                                html.H4("Templates", className="text-center mt-3"),
                                html.P("You can use these template files as a guide:", 
                                      className="text-center"),
                                html.Div([
                                    html.A(
                                        "Download Template with Sample Data", 
                                        href="/download/Template.xlsx",
                                        className="btn btn-info mr-2",
                                        style={"marginRight": "10px"}
                                    ),
                                    html.A(
                                        "Download Blank Template", 
                                        href="/download/BlankTemplate.xlsx",
                                        className="btn btn-outline-info"
                                    )
                                ], className="text-center mb-3"),
                                html.P([
                                    "File Format: Excel (.xlsx) with two sheets:",
                                    html.Ul([
                                        html.Li("Sheet 1: 'Summary' with instructions"),
                                        html.Li("Sheet 2: 'Transactions' with actual data")
                                    ])
                                ], className="small text-muted text-center")
                            ],
                            className="p-4 border rounded bg-light"
                        )
                    ],
                    id="no-files-message",
                    style={'display': 'none' if has_excel_files() else 'block', 'marginTop': '20px'}
                ),
                
                # Refresh button
                html.Button('Refresh Dashboard', id='refresh-button', 
                           className='btn btn-primary mt-3 mb-3'),
                html.Div(id='refresh-output'),
                html.Hr()
            ], width=12)
        ]),
        
        # Dashboard Content - only shown when files are available
        html.Div(id="dashboard-content", style={'display': 'block' if has_excel_files() else 'none'}, children=[
        
        # Error message row - only visible when there are errors
        dbc.Row([
            dbc.Col([
                html.Div(
                    [
                        html.H4("Error: Unable to Load Data", className="text-danger"),
                        html.P("The following errors occurred while trying to read the Excel files:"),
                        html.Ul([html.Li(error) for error in dashboard_errors]),
                        html.Hr(),
                        html.P([
                            "Troubleshooting steps:",
                            html.Ul([
                                html.Li("Make sure all Excel files exist in the correct location"),
                                html.Li("Check that the Excel files have a 'Transactions' sheet or at least a second sheet with transaction data"),
                                html.Li("Verify that all required columns (Category, Amount) exist in the sheets"),
                                html.Li("Try opening and resaving the Excel files to fix any potential corruption")
                            ])
                        ])
                    ],
                    id="error-container",
                    style={
                        'display': 'block' if dashboard_errors else 'none',
                        'backgroundColor': '#ffeeee',
                        'padding': '15px',
                        'borderRadius': '5px',
                        'marginBottom': '20px'
                    }
                )
            ], width=12)
        ]),
        
        # YTD Summary Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Total Income (YTD)", className="text-center"),
                    dbc.CardBody([
                        html.H3(format_inr(ytd_income), id="ytd-income-display", className="text-center text-success")
                    ])
                ], className="mb-4")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Total Expenses (YTD)", className="text-center"),
                    dbc.CardBody([
                        html.H3(format_inr(ytd_expenses), id="ytd-expenses-display", className="text-center text-danger")
                    ])
                ], className="mb-4")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Total Investments (YTD)", className="text-center"),
                    dbc.CardBody([
                        html.H3(format_inr(ytd_investments), id="ytd-investments-display", className="text-center text-info")
                    ])
                ], className="mb-4")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Total Surplus (YTD)", className="text-center"),
                    dbc.CardBody([
                        html.H3(format_inr(ytd_surplus), id="ytd-surplus-display", className="text-center text-primary")
                    ])
                ], className="mb-4")
            ], width=3)
        ]),
        
        # N/W/L Financial Planning Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        "Suggested Monthly Needs",
                        html.Span(" ℹ️", id="monthly-needs-info", style={"cursor": "pointer"})
                    ], className="text-center d-flex justify-content-center align-items-center"),
                    dbc.CardBody([
                        html.H3(format_inr(avg_monthly_needs), className="text-center", style={"color": "#00897B"})
                    ]),
                    dbc.Tooltip(
                        "Based on your 'Needs' labeled transactions. This is the amount you should budget monthly for necessities.",
                        target="monthly-needs-info"
                    )
                ], className="mb-4")
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        "Suggested Emergency Fund",
                        html.Span(" ℹ️", id="emergency-fund-info", style={"cursor": "pointer"})
                    ], className="text-center d-flex justify-content-center align-items-center"),
                    dbc.CardBody([
                        html.H3(format_inr(emergency_fund_suggestion), className="text-center", style={"color": "#E53935"})
                    ]),
                    dbc.Tooltip(
                        "Calculated as 6 months of your monthly needs. This is the recommended amount to keep as an emergency fund.",
                        target="emergency-fund-info"
                    )
                ], className="mb-4")
            ], width=6)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Avg. Monthly Income", className="text-center"),
                    dbc.CardBody([
                        html.H3(format_inr(avg_monthly_income), className="text-center")
                    ])
                ], className="mb-4")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Avg. Monthly Expenses", className="text-center"),
                    dbc.CardBody([
                        html.H3(format_inr(avg_monthly_expenses), className="text-center")
                    ])
                ], className="mb-4")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Avg. Monthly Investments", className="text-center"),
                    dbc.CardBody([
                        html.H3(format_inr(avg_monthly_investments), className="text-center")
                    ])
                ], className="mb-4")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Avg. Monthly Surplus", className="text-center"),
                    dbc.CardBody([
                        html.H3(format_inr(avg_monthly_surplus), className="text-center")
                    ])
                ], className="mb-4")
            ], width=3)
        ]),
        
        # Tabs for different visualizations
        dbc.Tabs([
            # Needs, Wants, Luxury Analysis Tab
            dbc.Tab(label="N/W/L Analysis", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Needs, Wants, Luxury Distribution", className="text-center mt-4 mb-2"),
                        dcc.Graph(id='nwl-pie-chart')
                    ], width=6),
                    
                    dbc.Col([
                        html.H4("N/W/L Monthly Trends", className="text-center mt-4 mb-2"),
                        dcc.Graph(id='nwl-trend-chart')
                    ], width=6)
                ]),
                
                dbc.Row([
                    dbc.Col([
                        html.H4("N/W/L by Category", className="text-center mt-4 mb-2"),
                        dcc.Graph(id='nwl-category-chart')
                    ], width=12)
                ]),
                
                dbc.Row([
                    dbc.Col([
                        html.H4("N/W/L Rules Reference", className="text-center mt-4 mb-2"),
                        html.Div([
                            html.P("This analysis is based on labels in the Excel files with the following meanings:"),
                            html.Ul([
                                html.Li(html.B("N (Needs)"), style={'color': '#00897B'}),
                                html.Li(html.B("W (Wants)"), style={'color': '#1976D2'}),
                                html.Li(html.B("L (Luxury)"), style={'color': '#E53935'}),
                                html.Li(html.B("S (Savings)"), style={'color': '#43A047'}),
                                html.Li(html.B("I (Investment)"), style={'color': '#7B1FA2'})
                            ])
                        ], className="p-3", style={'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
                    ], width=12)
                ])
            ]),
            
            # Monthly Overview Tab
            dbc.Tab(label="Monthly Overview", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Income, Expenses, and Investments by Month", className="text-center mt-4 mb-2"),
                        dcc.Graph(
                            figure=px.bar(
                                summary_df, 
                                x='Month', 
                                y=['Total Income', 'Total Expenses', 'Investments'],
                                barmode='group',
                                title="Monthly Financial Overview",
                                labels={'value': 'Amount (₹)', 'variable': 'Type'},
                                color_discrete_map={
                                    'Total Income': 'green', 
                                    'Total Expenses': 'red',
                                    'Investments': 'blue'
                                }
                            )
                        )
                    ], width=12),
                ]),
                
                dbc.Row([
                    dbc.Col([
                        html.H4("Surplus by Month", className="text-center mt-4 mb-2"),
                        dcc.Graph(
                            figure=px.line(
                                summary_df, 
                                x='Month', 
                                y='Surplus',
                                title="Monthly Surplus Trend",
                                labels={'Surplus': 'Amount (₹)'},
                                markers=True
                            )
                        )
                    ], width=6),
                    
                    dbc.Col([
                        html.H4("Investments by Month", className="text-center mt-4 mb-2"),
                        dcc.Graph(
                            figure=px.line(
                                summary_df, 
                                x='Month', 
                                y='Investments',
                                title="Monthly Investments Trend",
                                labels={'Investments': 'Amount (₹)'},
                                markers=True
                            )
                        )
                    ], width=6)
                ])
            ]),
            
            # Category Analysis Tab
            dbc.Tab(label="Category Analysis", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Expense Categories by Month", className="text-center mt-4 mb-2"),
                        html.Div([
                            dcc.Dropdown(
                                id='month-dropdown',
                                options=[{'label': month, 'value': month} for month in month_names] if month_names else [],
                                value=month_names[0] if month_names else None,
                                className="mb-2"
                            ),
                            dcc.Graph(id='category-pie-chart')
                        ])
                    ], width=6),
                    
                    dbc.Col([
                        html.H4("Category Trends Over Time", className="text-center mt-4 mb-2"),
                        html.Div([
                            dcc.Dropdown(
                                id='category-dropdown',
                                options=[{'label': cat, 'value': cat} for cat in unique_categories] if unique_categories else [],
                                value=unique_categories[0] if unique_categories and len(unique_categories) > 0 else None,
                                className="mb-2"
                            ),
                            dcc.Graph(id='category-trend-chart')
                        ])
                    ], width=6)
                ]),
                
                dbc.Row([
                    dbc.Col([
                        html.H4("Top Expense Categories (Overall)", className="text-center mt-4 mb-2"),
                        dcc.Graph(id='top-categories-chart')
                    ], width=12)
                ])
            ]),
            
            # Transaction Details Tab
            dbc.Tab(label="Transaction Details", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Filter Transactions", className="text-center mt-4 mb-2"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Month:"),
                                dcc.Dropdown(
                                    id='transaction-month-dropdown',
                                    options=[{'label': 'All Months', 'value': 'all'}] + 
                                            ([{'label': month, 'value': month} for month in month_names] if month_names else []),
                                    value='all',
                                    className="mb-2"
                                )
                            ], width=4),
                            dbc.Col([
                                html.Label("Category:"),
                                dcc.Dropdown(
                                    id='transaction-category-dropdown',
                                    options=[{'label': 'All Categories', 'value': 'all'}] + 
                                            ([{'label': cat, 'value': cat} for cat in unique_categories] if unique_categories else []),
                                    value='all',
                                    className="mb-2"
                                )
                            ], width=4),
                            dbc.Col([
                                html.Label("Person:"),
                                dcc.Dropdown(
                                    id='transaction-person-dropdown',
                                    options=[{'label': 'All People', 'value': 'all'}] + 
                                            ([{'label': person, 'value': person} for person in unique_people] if unique_people else []),
                                    value='all',
                                    className="mb-2"
                                )
                            ], width=4)
                        ])
                    ], width=12)
                ]),
                
                dbc.Row([
                    dbc.Col([
                        html.Div(id='transactions-table')
                    ], width=12)
                ])
            ]),
            
            # Transaction Labeling Tab
            dbc.Tab(label="Transaction Labeling", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Assign Labels to Transactions", className="text-center mt-4 mb-2"),
                        html.P("Assign each transaction a label (Needs, Wants, Luxury, Savings) and track your spending patterns", className="text-center"),
                        html.P("Note: Transactions with categories starting with 'Investment' are automatically labeled as 'Savings'", 
                               className="text-center font-italic"),
                        
                        # Month filter
                        dbc.Row([
                            dbc.Col([
                                html.Label("Filter by Month:"),
                                dcc.Dropdown(
                                    id='label-month-dropdown',
                                    options=[{'label': 'All Months', 'value': 'all'}] + 
                                            ([{'label': month, 'value': month} for month in month_names] if month_names else []),
                                    value='all',
                                    className="mb-2"
                                )
                            ], width=4),
                            
                            # Bulk Label section
                            dbc.Col([
                                html.Label("Bulk Label by Category:"),
                                dcc.Dropdown(
                                    id='bulk-category-dropdown',
                                    options=[{'label': cat, 'value': cat} for cat in unique_categories] if unique_categories else [],
                                    value=None,
                                    className="mb-2"
                                )
                            ], width=4),
                            
                            dbc.Col([
                                html.Label("Assign Label:"),
                                dcc.Dropdown(
                                    id='bulk-label-dropdown',
                                    options=label_options,
                                    value=None,
                                    className="mb-2"
                                ),
                                html.Button("Apply Bulk Label", id="apply-bulk-label", className="btn btn-primary mt-2")
                            ], width=4)
                        ]),
                        
                        # Editable Transactions Table
                        dash_table.DataTable(
                            id='label-transactions-table',
                            columns=[
                                {"name": "Date", "id": "Date", "type": "datetime"},
                                {"name": "Description", "id": "Description"},
                                {"name": "Category", "id": "Category"},
                                {"name": "Amount (₹)", "id": "Amount", "type": "numeric", "format": {"specifier": ",.2f"}},
                                {"name": "Who", "id": "Who"},
                                {"name": "Label", "id": "Label", "presentation": "dropdown", "editable": True},
                            ],
                            data=all_transactions_df.to_dict('records'),
                            dropdown={
                                'Label': {
                                    'options': label_options
                                }
                            },
                            editable=True,
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",
                            page_action="native",
                            page_size=15,
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'left',
                                'padding': '10px',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis'
                            },
                            style_header={
                                'backgroundColor': 'lightgrey',
                                'fontWeight': 'bold'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(248, 248, 248)'
                                },
                                {
                                    'if': {'filter_query': '{Label} = "Savings"'},
                                    'backgroundColor': 'rgba(200, 230, 255, 0.5)'
                                }
                            ],
                        ),
                        
                        # Save Button
                        html.Button("Save Labels", id="save-labels", className="btn btn-success mt-3"),
                        html.Div(id="save-status", className="mt-2")
                        
                    ], width=12)
                ])
            ]),
            
            # Label Analysis Tab
            dbc.Tab(label="Label Analysis", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Spending by Label", className="text-center mt-4 mb-2"),
                        dcc.Graph(id='label-pie-chart')
                    ], width=6),
                    
                    dbc.Col([
                        html.H4("Monthly Trends by Label", className="text-center mt-4 mb-2"),
                        dcc.Graph(id='label-trend-chart')
                    ], width=6)
                ]),
                
                dbc.Row([
                    dbc.Col([
                        html.H4("Label Distribution by Category", className="text-center mt-4 mb-2"),
                        dcc.Graph(id='label-category-chart')
                    ], width=12)
                ])
            ]),
            
            # Spending Patterns Tab
            dbc.Tab(label="Spending Patterns", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Spending by Person", className="text-center mt-4 mb-2"),
                        dcc.Graph(
                            id='spending-by-person-chart'
                        )
                    ], width=6),
                    
                    dbc.Col([
                        html.H4("Spending Trends by Person", className="text-center mt-4 mb-2"),
                        dcc.Graph(
                            id='spending-trends-by-person-chart'
                        )
                    ], width=6)
                ]),
                
                dbc.Row([
                    dbc.Col([
                        html.H4("Daily Spending Pattern", className="text-center mt-4 mb-2"),
                        dcc.Graph(
                            id='daily-spending-pattern-chart'
                        )
                    ], width=12)
                ])
            ]),
            
            # Insights & Recommendations Tab
            dbc.Tab(label="Insights & Recommendations", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Budget Insights", className="text-center mt-4 mb-2"),
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Key Metrics"),
                                html.Ul([
                                    html.Li(f"Monthly average surplus: {format_inr(avg_monthly_surplus)}"),
                                    html.Li(f"Monthly average investments: {format_inr(avg_monthly_investments)}"),
                                    html.Li(f"Top expense category: {top_expense_category}")
                                ]),
                                html.H5("Monthly Analysis", className="mt-4"),
                                html.Ul([
                                    html.Li(f"Highest expense month: {highest_expense_month} ({format_inr(highest_expense_amount)})"),
                                    html.Li(f"Highest surplus month: {highest_surplus_month} ({format_inr(highest_surplus_amount)})"),
                                    html.Li(f"Highest investment month: {highest_investment_month} ({format_inr(highest_investment_amount)})"),
                                ])
                            ])
                        ], className="mb-4")
                    ], width=6),
                    
                    dbc.Col([
                        html.H4("Recommendations", className="text-center mt-4 mb-2"),
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Budget Optimization"),
                                html.Ul([
                                    html.Li(f"Focus on reducing spending in the top expense category: {top_expense_category}"),
                                    html.Li(f"Target a monthly investment of at least {format_inr(avg_monthly_investments*1.1)} (10% increase)"),
                                    html.Li("Compare expenses against income percentage for better budgeting"),
                                    html.Li("Track month-over-month category changes to identify spending patterns")
                                ]),
                                html.H5("Future Planning", className="mt-4"),
                                html.Ul([
                                    html.Li("Consider allocating more of your surplus to investments"),
                                    html.Li("Identify recurring expenses that could be reduced or eliminated"),
                                    html.Li("Establish category-specific budget targets for better expense management")
                                ])
                            ])
                        ])
                    ], width=6)
                ])
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                html.P(f"Dashboard generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                       className="text-center text-muted mt-4 mb-2")
            ], width=12)
        ]),
        
        ]), # End of dashboard-content div
        
        # Store component to keep track of the labeled transactions
        dcc.Store(id='transactions-store', data=all_transactions_df.to_dict('records'))
    ], fluid=True)
    
    # Define callbacks for interactive elements
    @app.callback(
        Output('category-pie-chart', 'figure'),
        Input('month-dropdown', 'value')
    )
    def update_pie_chart(selected_month):
        # Filter transactions for the selected month
        month_data = all_transactions_df[all_transactions_df['Month'] == selected_month].copy()
        
        # Ensure Amount is numeric
        month_data['Amount'] = pd.to_numeric(month_data['Amount'], errors='coerce')
        month_data = month_data.dropna(subset=['Amount'])  # Drop rows where Amount couldn't be converted
        
        # Check if we have any data to work with
        if month_data.empty:
            return px.pie(title=f"No transaction data for {selected_month}")
        
        # Exclude investment categories
        investment_mask = month_data['Category'].astype(str).str.startswith('Investment')
        regular_expense_data = month_data[~investment_mask]
        
        # Check if we have expense data after filtering
        if regular_expense_data.empty:
            return px.pie(title=f"No expense data for {selected_month} (excluding investments)")
        
        # Group by category
        category_expenses = regular_expense_data.groupby('Category')['Amount'].sum().reset_index()
        
        # Create pie chart
        fig = px.pie(
            category_expenses,
            values='Amount',
            names='Category',
            title=f"Expense Categories for {selected_month} (Excluding Investments)"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig
    
    @app.callback(
        Output('category-trend-chart', 'figure'),
        Input('category-dropdown', 'value')
    )
    def update_category_trend(selected_category):
        if selected_category:
            # Create a DataFrame with just this category's expenses over time
            category_data = category_monthly_df[category_monthly_df['Category'] == selected_category].copy()
            
            if not category_data.empty:
                # Melt to convert months to rows
                trend_data = pd.melt(
                    category_data, 
                    id_vars=['Category'], 
                    value_vars=month_names,
                    var_name='Month', 
                    value_name='Amount'
                )
                
                # Ensure Amount is numeric
                trend_data['Amount'] = pd.to_numeric(trend_data['Amount'], errors='coerce')
                trend_data = trend_data.fillna(0)  # Fill NaN values with zero for this chart
                
                # Create line chart
                fig = px.line(
                    trend_data,
                    x='Month',
                    y='Amount',
                    title=f"{selected_category} Expenses Over Time",
                    markers=True
                )
                fig.update_layout(yaxis_title="Amount (₹)")
                return fig
        
        # Fallback empty chart
        return px.line(title="Select a category to see trend")
    
    @app.callback(
        Output('top-categories-chart', 'figure'),
        Input('month-dropdown', 'value')  # Dummy input to trigger the callback
    )
    def update_top_categories(_):
        # Make a copy to avoid modifying the original
        expense_data = all_transactions_df.copy()
        
        # Ensure Amount is numeric
        expense_data['Amount'] = pd.to_numeric(expense_data['Amount'], errors='coerce')
        expense_data = expense_data.dropna(subset=['Amount'])  # Drop rows where Amount couldn't be converted
        
        # Filter out investment categories
        investment_mask = expense_data['Category'].astype(str).str.startswith('Investment')
        regular_expense_data = expense_data[~investment_mask]
        
        if regular_expense_data.empty:
            return px.bar(title="No expense data available")
        
        # Get overall expenses by category
        category_totals = regular_expense_data.groupby('Category')['Amount'].sum().reset_index()
        
        # Make sure we have categories to display
        if len(category_totals) == 0:
            return px.bar(title="No categories found")
        
        # Sort and take top 10
        category_totals = category_totals.sort_values('Amount', ascending=False)
        category_totals = category_totals.head(min(10, len(category_totals)))
        
        # Create bar chart
        fig = px.bar(
            category_totals,
            x='Category',
            y='Amount',
            title="Top 10 Expense Categories (All Months, Excluding Investments)",
            labels={'Amount': 'Amount (₹)'}
        )
        return fig
    
    @app.callback(
        Output('transactions-table', 'children'),
        [
            Input('transaction-month-dropdown', 'value'),
            Input('transaction-category-dropdown', 'value'),
            Input('transaction-person-dropdown', 'value')
        ]
    )
    def update_transactions_table(selected_month, selected_category, selected_person):
        # Start with all transactions
        filtered_df = all_transactions_df.copy()
        
        # Apply filters
        if selected_month != 'all':
            filtered_df = filtered_df[filtered_df['Month'] == selected_month]
            
        if selected_category != 'all':
            filtered_df = filtered_df[filtered_df['Category'] == selected_category]
            
        if selected_person != 'all':
            filtered_df = filtered_df[filtered_df['Who'] == selected_person]
        
        # Ensure Date column exists and convert to datetime for consistent sorting
        if 'Date' in filtered_df.columns and not filtered_df.empty:
            # Convert string dates to datetime
            try:
                # First try to convert using pandas to_datetime
                filtered_df['Date'] = pd.to_datetime(filtered_df['Date'], errors='coerce')
                # Sort by date (handling NaT values)
                filtered_df = filtered_df.sort_values('Date', ascending=False, na_position='last')
            except Exception as e:
                print(f"Error sorting by date: {e}")
                # If sorting fails, return the unsorted data
        else:
            # Sort by Month if Date is not available
            if 'Month' in filtered_df.columns:
                # Use a month order mapping for proper sorting
                month_order = {month: i for i, month in enumerate(month_names)}
                filtered_df['MonthOrder'] = filtered_df['Month'].map(month_order)
                filtered_df = filtered_df.sort_values('MonthOrder', ascending=False)
                if 'MonthOrder' in filtered_df.columns:
                    filtered_df = filtered_df.drop('MonthOrder', axis=1)
        
        # Create DataTable
        if not filtered_df.empty:
            return dash_table.DataTable(
                id='table',
                columns=[
                    {"name": "Date", "id": "Date", "type": "datetime"},
                    {"name": "Description", "id": "Description"},
                    {"name": "Category", "id": "Category"},
                    {"name": "Amount (₹)", "id": "Amount", "type": "numeric", "format": {"specifier": ",.2f"}},
                    {"name": "Who", "id": "Who"},
                    {"name": "Whom", "id": "Whom"},
                    {"name": "Label", "id": "Label", "presentation": "dropdown", "editable": True}
                ],
                data=filtered_df.to_dict('records'),
                dropdown={
                    'Label': {
                        'options': label_options
                    }
                },
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis'
                },
                style_header={
                    'backgroundColor': 'lightgrey',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    },
                    {
                        'if': {'filter_query': '{Label} = "Savings"'},
                        'backgroundColor': 'rgba(200, 230, 255, 0.5)'
                    }
                ],
                page_size=15,
                sort_action='native',
                filter_action='native'
            )
        else:
            return html.Div("No transactions match the selected filters.", className="text-center m-5")
    
    # Callback for the editable labels datatable
    @app.callback(
        Output('label-transactions-table', 'data'),
        Input('label-month-dropdown', 'value'),
        State('transactions-store', 'data')
    )
    def filter_label_table(selected_month, transactions_data):
        df = pd.DataFrame(transactions_data)
        
        if selected_month != 'all':
            df = df[df['Month'] == selected_month]
        
        # Ensure dates are properly formatted before returning
        if 'Date' in df.columns and not df.empty:
            try:
                # Convert any string dates to datetime for consistent display
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                # Sort by date
                df = df.sort_values('Date', ascending=False, na_position='last')
            except Exception as e:
                print(f"Error processing dates in label table: {e}")
        
        return df.to_dict('records')
    
    # Callback for bulk label application
    @app.callback(
        Output('transactions-store', 'data'),
        Input('apply-bulk-label', 'n_clicks'),
        State('bulk-category-dropdown', 'value'),
        State('bulk-label-dropdown', 'value'),
        State('transactions-store', 'data'),
        prevent_initial_call=True
    )
    def apply_bulk_label(n_clicks, category, label, transactions_data):
        if n_clicks is None or category is None or label is None:
            return transactions_data
        
        df = pd.DataFrame(transactions_data)
        
        # Apply the label to all transactions with the selected category
        df.loc[df['Category'] == category, 'Label'] = label
        
        return df.to_dict('records')
    
    # Callback to update labels from the label table
    @app.callback(
        Output('transactions-store', 'data', allow_duplicate=True),
        Input('label-transactions-table', 'data'),
        State('transactions-store', 'data'),
        prevent_initial_call=True
    )
    def update_labels(table_data, store_data):
        if not table_data:
            return store_data
        
        table_df = pd.DataFrame(table_data)
        store_df = pd.DataFrame(store_data)
        
        # For each row in table_data, update the corresponding row in store_data
        for _, row in table_df.iterrows():
            # Find matching row(s) in store_df
            # Need to match on multiple columns to ensure uniqueness
            mask = (store_df['Date'] == row['Date']) & \
                   (store_df['Description'] == row['Description']) & \
                   (store_df['Amount'] == row['Amount']) & \
                   (store_df['Who'] == row['Who'])
            
            # Update the Label column for matching rows
            if any(mask):
                store_df.loc[mask, 'Label'] = row['Label']
        
        return store_df.to_dict('records')
    
    # Callback to display save status
    @app.callback(
        Output('save-status', 'children'),
        Input('save-labels', 'n_clicks'),
        State('transactions-store', 'data'),
        prevent_initial_call=True
    )
    def save_labels(n_clicks, transactions_data):
        if n_clicks is None:
            return ""
        
        try:
            # Update all_transactions_df with the labeled data
            df = pd.DataFrame(transactions_data)
            
            # Get the data directory and save CSV there
            data_dir = get_data_dir()
            csv_path = os.path.join(data_dir, 'labeled_transactions.csv')
            df.to_csv(csv_path, index=False)
            
            # Map full labels back to short codes for Excel
            label_to_code = {
                'Needs': 'N',
                'Wants': 'W',
                'Luxury': 'L',
                'Savings': 'S',
                'Investment': 'I'
            }
            
            # Try to update the Excel files with the new labels
            for month_name in month_names:
                file_path = os.path.join(data_dir, f"{month}.xlsx" if month_name == 'February' else f"{month_name}.xlsx")
                month_data = df[df['Month'] == month_name]
                
                if not os.path.exists(file_path):
                    print(f"Warning: Cannot save labels to {file_path} - file does not exist")
                    continue
                    
                try:
                    # Create a mapping of transactions to their labels
                    transactions_with_labels = {}
                    for idx, row in month_data.iterrows():
                        if pd.notna(row['Label']) and row['Label'] != '':
                            # Use a composite key to identify the transaction
                            key = (
                                str(row['Date']),
                                str(row['Description']), 
                                float(row['Amount']),
                                str(row['Who'])
                            )
                            # Map the full label to the code
                            transactions_with_labels[key] = label_to_code.get(row['Label'], '')
                    
                    print(f"Found {len(transactions_with_labels)} labeled transactions for {month_name}")
                except Exception as e:
                    print(f"Error preparing labels for {file_path}: {e}")
            
            # Count labeled transactions by type
            label_counts = {}
            for label in ['Needs', 'Wants', 'Luxury', 'Savings', 'Investment']:
                count = len(df[df['Label'] == label])
                if count > 0:
                    label_counts[label] = count
            
            # Count labeled transactions
            labeled_count = len(df[df['Label'] != ''])
            total_count = len(df)
            
            # Calculate percentages
            label_percentages = {}
            for label, count in label_counts.items():
                percentage = (count / total_count) * 100
                label_percentages[label] = percentage
            
            # Generate label stats formatted as table rows
            label_stats_rows = []
            for label, count in label_counts.items():
                percentage = label_percentages[label]
                label_stats_rows.append(
                    html.Tr([
                        html.Td(label),
                        html.Td(f"{count}"),
                        html.Td(f"{percentage:.1f}%")
                    ])
                )
            
            # Generate final status message with table
            return html.Div([
                html.H5("Labels saved successfully!", style={'color': 'green', 'marginBottom': '10px'}),
                html.P(f"Saved {labeled_count} labeled transactions out of {total_count} total transactions."),
                
                html.H6("Label Distribution:", style={'marginTop': '15px', 'marginBottom': '5px'}),
                html.Table([
                    html.Thead(
                        html.Tr([
                            html.Th("Label", style={'minWidth': '100px', 'textAlign': 'left'}),
                            html.Th("Count", style={'minWidth': '80px', 'textAlign': 'left'}),
                            html.Th("Percentage", style={'minWidth': '100px', 'textAlign': 'left'})
                        ])
                    ),
                    html.Tbody(label_stats_rows)
                ], style={'borderCollapse': 'collapse', 'width': '100%'}),
                
                html.P(f"The labeled transactions have been saved to {csv_path}", 
                      style={'marginTop': '15px', 'fontStyle': 'italic'})
            ], style={'backgroundColor': '#f8f9fa', 'padding': '15px', 'borderRadius': '5px'})
            
        except Exception as e:
            error_msg = f"Error saving labels: {str(e)}"
            print(error_msg)
            return html.Div([
                html.P("Error saving labels!", style={'color': 'red', 'fontWeight': 'bold'}),
                html.P(error_msg)
            ], style={'backgroundColor': '#fff3f3', 'padding': '15px', 'borderRadius': '5px'})
    
    # Callbacks for spending patterns
    @app.callback(
        Output('spending-by-person-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_spending_by_person(transactions_data):
        df = pd.DataFrame(transactions_data)
        
        if df.empty or 'Who' not in df.columns:
            return px.pie(title="No person data available")
        
        # Group by Who
        person_expenses = df.groupby('Who')['Amount'].sum().reset_index()
        
        # Create pie chart
        fig = px.pie(
            person_expenses,
            values='Amount',
            names='Who',
            title="Expenses by Person"
        )
        return fig
    
    @app.callback(
        Output('spending-trends-by-person-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_spending_trends_by_person(transactions_data):
        df = pd.DataFrame(transactions_data)
        
        if df.empty or 'Who' not in df.columns:
            return px.line(title="No person data available")
        
        # Group by Month and Who
        monthly_person_expenses = df.groupby(['Month', 'Who'])['Amount'].sum().reset_index()
        
        # Create line chart
        fig = px.line(
            monthly_person_expenses,
            x='Month',
            y='Amount',
            color='Who',
            title="Monthly Spending by Person",
            markers=True
        )
        fig.update_layout(yaxis_title="Amount (₹)")
        return fig
    
    @app.callback(
        Output('daily-spending-pattern-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_daily_spending_pattern(transactions_data):
        df = pd.DataFrame(transactions_data)
        
        if df.empty:
            return px.scatter(title="No transaction data available")
        
        # Create scatter plot
        hover_data = ['Description']
        if 'Who' in df.columns:
            hover_data.append('Who')
            
        fig = px.scatter(
            df,
            x='Date',
            y='Amount',
            color='Category',
            size='Amount',
            hover_data=hover_data,
            title="Daily Spending Pattern"
        )
        fig.update_layout(yaxis_title="Amount (₹)")
        return fig
    
    # Callbacks for the Label Analysis tab
    @app.callback(
        Output('label-pie-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_label_pie_chart(transactions_data):
        df = pd.DataFrame(transactions_data)
        
        # Check if Label column exists
        if 'Label' not in df.columns:
            return px.pie(title="No label data available")
        
        # Skip empty labels
        df = df[df['Label'].notna() & (df['Label'] != '')]
        
        if df.empty:
            return px.pie(title="No labeled transactions")
        
        # Ensure Amount is numeric
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df = df.dropna(subset=['Amount'])  # Drop rows where Amount couldn't be converted
        
        if df.empty:
            return px.pie(title="No valid transaction amounts")
        
        # Group by label
        label_expenses = df.groupby('Label')['Amount'].sum().reset_index()
        
        # Create pie chart
        fig = px.pie(
            label_expenses,
            values='Amount',
            names='Label',
            title="Expense Distribution by Label"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig
    
    @app.callback(
        Output('label-trend-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_label_trend(transactions_data):
        df = pd.DataFrame(transactions_data)
        
        # Check if Label column exists
        if 'Label' not in df.columns:
            return px.line(title="No label data available")
        
        # Skip empty labels
        df = df[df['Label'].notna() & (df['Label'] != '')]
        
        if df.empty:
            return px.line(title="No labeled transactions")
        
        # Ensure Amount is numeric
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df = df.dropna(subset=['Amount'])  # Drop rows where Amount couldn't be converted
        
        if df.empty:
            return px.line(title="No valid transaction amounts")
        
        # Group by month and label
        monthly_label_expenses = df.groupby(['Month', 'Label'])['Amount'].sum().reset_index()
        
        # Create line chart
        fig = px.line(
            monthly_label_expenses,
            x='Month',
            y='Amount',
            color='Label',
            title="Monthly Expenses by Label",
            markers=True
        )
        fig.update_layout(yaxis_title="Amount (₹)")
        return fig
    
    @app.callback(
        Output('label-category-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_label_category_chart(transactions_data):
        try:
            df = pd.DataFrame(transactions_data)
            
            # Print first few rows for debugging
            print("Label category chart - first few rows of data:", df.head())
            
            # Check if Label column exists
            if 'Label' not in df.columns:
                print("Label column not found")
                return px.bar(title="No label data available")
            
            # Skip empty labels
            df = df[df['Label'].notna() & (df['Label'] != '')]
            
            if df.empty:
                print("No labeled transactions")
                return px.bar(title="No labeled transactions")
            
            # Ensure Amount column exists
            if 'Amount' not in df.columns:
                print("Amount column not found")
                return px.bar(title="Amount column not found in data")
            
            print("Data types before conversion:", df.dtypes)
            
            # Ensure Amount is numeric - convert strings to float
            df['Amount'] = df['Amount'].astype(float)
            
            # Drop any rows with NaN Amount values
            df = df.dropna(subset=['Amount'])
            
            if df.empty:
                print("No valid transaction amounts")
                return px.bar(title="No valid transaction amounts")
            
            print("Data types after conversion:", df.dtypes)
            
            # Group by category and label
            category_label_expenses = df.groupby(['Category', 'Label'])['Amount'].sum().reset_index()
            
            # Get total amount by category for sorting
            category_sums = df.groupby('Category')['Amount'].sum().reset_index()
            
            # Sort by amount in descending order
            sorted_categories = category_sums.sort_values('Amount', ascending=False)
            
            # Get top 10 categories (or fewer if there are less than 10)
            top_count = min(10, len(sorted_categories))
            top_categories = sorted_categories['Category'].iloc[:top_count].tolist()
            
            if not top_categories:
                print("No categories found")
                return px.bar(title="No categories found")
            
            # Filter to include only top categories
            filtered_data = category_label_expenses[category_label_expenses['Category'].isin(top_categories)]
            
            if filtered_data.empty:
                print("No data after filtering")
                return px.bar(title="No data after filtering")
            
            # Create bar chart
            fig = px.bar(
                filtered_data,
                x='Category',
                y='Amount',
                color='Label',
                title="Label Distribution by Top Categories",
                barmode='stack'
            )
            fig.update_layout(yaxis_title="Amount (₹)")
            return fig
        except Exception as e:
            print(f"Error in label-category-chart: {e}")
            return px.bar(title=f"Error: {str(e)}")
    
    # Callbacks for the N/W/L analysis tab
    @app.callback(
        Output('nwl-pie-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_nwl_pie_chart(transactions_data):
        try:
            df = pd.DataFrame(transactions_data)
            
            # Check if the DataFrame has the required columns
            if df.empty or 'Label' not in df.columns or 'Amount' not in df.columns:
                return px.pie(title="No data available or missing required columns")
            
            # Skip transactions without a label
            df = df[df['Label'].notna() & (df['Label'] != '')]
            
            if df.empty:
                return px.pie(title="No labeled transactions")
            
            # Use only Needs, Wants, Luxury labels (not Savings/Investment)
            nwl_labels = ['Needs', 'Wants', 'Luxury']
            df = df[df['Label'].isin(nwl_labels)]
            
            if df.empty:
                return px.pie(title="No N/W/L transactions found")
            
            # Ensure Amount is numeric
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            df = df.dropna(subset=['Amount'])  # Drop rows where Amount couldn't be converted
            
            if df.empty:
                return px.pie(title="No valid data after conversion")
            
            # Group by label
            label_expenses = df.groupby('Label')['Amount'].sum().reset_index()
            
            # Create pie chart with specific colors
            colors = {'Needs': '#00897B', 'Wants': '#1976D2', 'Luxury': '#E53935'}
            
            fig = px.pie(
                label_expenses,
                values='Amount',
                names='Label',
                title="Expense Distribution by Needs, Wants, Luxury",
                color='Label',
                color_discrete_map=colors
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            return fig
        except Exception as e:
            # Return an error figure if any exception occurs
            return px.pie(title=f"Error generating chart: {str(e)}")
    
    @app.callback(
        Output('nwl-trend-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_nwl_trend_chart(transactions_data):
        try:
            df = pd.DataFrame(transactions_data)
            
            # Check if the DataFrame has the required columns
            if df.empty or 'Label' not in df.columns or 'Amount' not in df.columns or 'Month' not in df.columns:
                return px.line(title="No data available or missing required columns")
            
            # Skip transactions without a label
            df = df[df['Label'].notna() & (df['Label'] != '')]
            
            if df.empty:
                return px.line(title="No labeled transactions")
            
            # Use only Needs, Wants, Luxury labels
            nwl_labels = ['Needs', 'Wants', 'Luxury']
            df = df[df['Label'].isin(nwl_labels)]
            
            if df.empty:
                return px.line(title="No N/W/L transactions found")
            
            # Ensure Amount is numeric
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            df = df.dropna(subset=['Amount'])  # Drop rows where Amount couldn't be converted
            
            if df.empty:
                return px.line(title="No valid data after conversion")
            
            # Group by month and label
            monthly_label_expenses = df.groupby(['Month', 'Label'])['Amount'].sum().reset_index()
            
            # Create line chart with specific colors
            colors = {'Needs': '#00897B', 'Wants': '#1976D2', 'Luxury': '#E53935'}
            
            fig = px.line(
                monthly_label_expenses,
                x='Month',
                y='Amount',
                color='Label',
                title="Monthly Spending by Needs, Wants, Luxury",
                markers=True,
                color_discrete_map=colors
            )
            fig.update_layout(yaxis_title="Amount (₹)")
            return fig
        except Exception as e:
            # Return an error figure if any exception occurs
            return px.line(title=f"Error generating chart: {str(e)}")
    
    # Callback for file upload
    @app.callback(
        [Output('upload-output', 'children'),
         Output('dashboard-content', 'style'),
         Output('no-files-message', 'style'),
         Output('transactions-store', 'data', allow_duplicate=True),
         # Add outputs for the YTD cards
         Output('ytd-income-display', 'children', allow_duplicate=True),
         Output('ytd-expenses-display', 'children', allow_duplicate=True),
         Output('ytd-investments-display', 'children', allow_duplicate=True),
         Output('ytd-surplus-display', 'children', allow_duplicate=True),
         # Add output for the toast
         Output('refresh-toast', 'is_open', allow_duplicate=True),
         Output('refresh-toast', 'header', allow_duplicate=True),
         Output('refresh-toast', 'children', allow_duplicate=True)],
        Input('upload-data', 'contents'),
        State('upload-data', 'filename'),
        State('upload-data', 'last_modified'),
        prevent_initial_call=True  # Add this to work with allow_duplicate
    )
    def update_output(list_of_contents, list_of_filenames, list_of_dates):
        if list_of_contents is None:
            # Get current state of files
            has_files = has_excel_files()
            dashboard_style = {'display': 'block'} if has_files else {'display': 'none'}
            no_files_style = {'display': 'none'} if has_files else {'display': 'block', 'marginTop': '20px'}
            return html.Div("Upload your Excel files to get started."), dashboard_style, no_files_style, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, dash.no_update, dash.no_update
        
        upload_results = []
        data_dir = get_data_dir()
        upload_success = False
        
        for content, filename, date in zip(list_of_contents, list_of_filenames, list_of_dates):
            # Only accept Excel files
            if not filename.endswith('.xlsx'):
                upload_results.append(html.Div("Error: {} is not an Excel file. Only .xlsx files are supported.".format(filename), 
                                              style={'color': 'red'}))
                continue
                
            try:
                # Decode content
                content_type, content_string = content.split(',')
                decoded = base64.b64decode(content_string)
                
                # Save file to data directory
                file_path = os.path.join(data_dir, filename)
                with open(file_path, 'wb') as f:
                    f.write(decoded)
                
                # Mark that we had at least one successful upload
                upload_success = True
                
                # Add success message
                upload_results.append(html.Div([
                    html.Span("✅ Uploaded: {}".format(filename), style={'color': 'green'}),
                    html.Span(" ({})".format(datetime.fromtimestamp(date/1000).strftime('%Y-%m-%d %H:%M:%S')))
                ]))
                
                print(f"Successfully uploaded file: {filename}")
                
            except Exception as e:
                upload_results.append(html.Div("Error processing {}: {}".format(filename, str(e)), 
                                              style={'color': 'red'}))
                print(f"Error uploading file {filename}: {str(e)}")
        
        # If any upload was successful, reload data
        if upload_success:
            try:
                print("Upload was successful, performing complete data reload...")
                
                # Reset global data structures to force complete reload
                global summary_df, all_transactions_df, category_monthly_df, months, month_names
                
                # Reset month lists to ensure fresh load
                months = []
                month_names = []
                
                # Force reload of all data
                summary_df, all_transactions_df, category_monthly_df = load_data()
                
                # Calculate YTD values freshly
                ytd_income = summary_df['Total Income'].sum() if not summary_df.empty else 0
                ytd_expenses = summary_df['Total Expenses'].sum() if not summary_df.empty else 0
                ytd_investments = summary_df['Investments'].sum() if not summary_df.empty else 0
                ytd_surplus = summary_df['Surplus'].sum() if not summary_df.empty else 0
                
                print(f"Data reload complete. YTD Income: {ytd_income}, YTD Expenses: {ytd_expenses}, YTD Investments: {ytd_investments}, YTD Surplus: {ytd_surplus}")
                
                # Add automatic refresh message
                upload_results.append(html.Div([
                    html.Div(
                        "Data loaded successfully. Dashboard is now updated.",
                        style={'fontWeight': 'bold', 'marginTop': '10px', 'color': 'green'}
                    ),
                    html.Div(
                        f"Total Income (YTD): ₹{ytd_income:,.2f} | Total Expenses (YTD): ₹{ytd_expenses:,.2f}",
                        style={'fontSize': '0.9em', 'color': '#555', 'marginTop': '5px'}
                    )
                ]))
                
                # Prepare transaction data for updating all charts
                transactions_data = all_transactions_df.to_dict('records') if not all_transactions_df.empty else []
                
                # Format the values for YTD cards
                income_display = format_inr(ytd_income)
                expenses_display = format_inr(ytd_expenses)
                investments_display = format_inr(ytd_investments)
                surplus_display = format_inr(ytd_surplus)
                
                # Check if we have files after upload
                has_files = has_excel_files()
                dashboard_style = {'display': 'block'} if has_files else {'display': 'none'}
                no_files_style = {'display': 'none'} if has_files else {'display': 'block', 'marginTop': '20px'}
                
                # Create toast content with uploaded files summary
                timestamp = datetime.now().strftime('%H:%M:%S')
                excel_files, _ = get_excel_files()
                file_count = len(excel_files)
                month_count = len(month_names)
                
                uploaded_files = [f for f in list_of_filenames if f.endswith('.xlsx')]
                
                toast_header = f"Files Uploaded Successfully ({timestamp})"
                toast_content = html.Div([
                    html.H5("Upload Summary", className="mb-2"),
                    html.P([
                        f"Uploaded ", html.B(f"{len(uploaded_files)}"), " new files"
                    ]),
                    html.Ul([html.Li(filename) for filename in uploaded_files]),
                    html.Hr(className="my-2"),
                    html.P(f"Total files now available: {file_count} files covering {month_count} months"),
                    html.P("Year to Date Totals:", className="font-weight-bold mt-3 mb-1"),
                    html.Ul([
                        html.Li([html.Span("Income: "), html.Span(income_display, className="text-success")]),
                        html.Li([html.Span("Expenses: "), html.Span(expenses_display, className="text-danger")]),
                        html.Li([html.Span("Investments: "), html.Span(investments_display, className="text-info")]),
                        html.Li([html.Span("Surplus: "), html.Span(surplus_display, className="text-primary")])
                    ])
                ])
                
                # Return all values including YTD card updates and toast
                return html.Div(upload_results), dashboard_style, no_files_style, transactions_data, income_display, expenses_display, investments_display, surplus_display, True, toast_header, toast_content
            except Exception as e:
                error_msg = str(e)
                print(f"Error during data reload after upload: {error_msg}")
                upload_results.append(html.Div([
                    html.Div(
                        "Error loading data after upload. Click 'Refresh Dashboard' to try again.",
                        style={'fontWeight': 'bold', 'marginTop': '10px', 'color': 'red'}
                    ),
                    html.Div(
                        f"Error details: {error_msg}",
                        style={'fontSize': '0.8em', 'color': '#d32f2f', 'marginTop': '5px'}
                    )
                ]))
                transactions_data = dash.no_update
                # Create error toast content
                error_toast_content = html.Div([
                    html.H5("Upload Error", className="mb-2 text-danger"),
                    html.P("An error occurred while processing the uploaded files:"),
                    html.P(error_msg, className="p-2 bg-light border rounded text-danger")
                ])
                
                # Keep YTD displays the same if there's an error
                return html.Div(upload_results), dashboard_style, no_files_style, transactions_data, dash.no_update, dash.no_update, dash.no_update, dash.no_update, True, "Upload Error", error_toast_content
        else:
            # Add message to use refresh button if no successful uploads
            upload_results.append(html.Div(
                "No files were successfully uploaded. Verify file format and try again.",
                style={'fontWeight': 'bold', 'marginTop': '10px', 'color': 'orange'}
            ))
            transactions_data = dash.no_update
            # Keep YTD displays the same if there's no successful upload
            return html.Div(upload_results), dashboard_style, no_files_style, transactions_data, dash.no_update, dash.no_update, dash.no_update, dash.no_update, True, "Upload Warning", html.P("No files were successfully uploaded. Please check the file format and try again.")
        
        # Check if we have files after upload
        has_files = has_excel_files()
        dashboard_style = {'display': 'block'} if has_files else {'display': 'none'}
        no_files_style = {'display': 'none'} if has_files else {'display': 'block', 'marginTop': '20px'}
    
    # Callback to refresh available files list - simpler version without delete buttons
    @app.callback(
        Output('available-files', 'children'),
        [Input('refresh-button', 'n_clicks'),
         Input('upload-output', 'children')]  # Also trigger on new upload
    )
    def update_available_files(n_clicks, upload_output):
        # Get the list of Excel files
        excel_files, data_dir = get_excel_files()
        
        if not excel_files:
            return html.Div("No Excel files found in the data directory.", 
                          style={'fontStyle': 'italic'})
        
        # Create list of available files (without individual delete buttons to avoid callback issues)
        file_list = []
        for file in excel_files:
            file_list.append(html.Div([
                html.Span(file, style={'marginRight': '10px'})
            ], style={'margin': '5px 0'}))
        
        # Add a note about deletion
        file_list.append(html.Div([
            html.Hr(),
            html.P("To delete files, use your file explorer to remove them from the data directory, then click 'Refresh Dashboard'.", 
                  style={'fontStyle': 'italic', 'fontSize': '0.9em'})
        ]))
        
        return html.Div(file_list)
    
    # Callback to refresh the dashboard and toggle visibility
    @app.callback(
        [Output('refresh-output', 'children', allow_duplicate=True),
         Output('dashboard-content', 'style', allow_duplicate=True),
         Output('no-files-message', 'style', allow_duplicate=True),
         Output('transactions-store', 'data', allow_duplicate=True),
         # Add outputs for the YTD cards
         Output('ytd-income-display', 'children', allow_duplicate=True),
         Output('ytd-expenses-display', 'children', allow_duplicate=True),
         Output('ytd-investments-display', 'children', allow_duplicate=True),
         Output('ytd-surplus-display', 'children', allow_duplicate=True),
         # Add output for the toast
         Output('refresh-toast', 'is_open', allow_duplicate=True),
         Output('refresh-toast', 'header', allow_duplicate=True),
         Output('refresh-toast', 'children', allow_duplicate=True)],
        Input('refresh-button', 'n_clicks'),
        prevent_initial_call=True
    )
    def refresh_dashboard(n_clicks):
        if n_clicks:
            # Reload data completely - this is important for proper refresh
            try:
                print("Performing complete dashboard refresh...")
                
                # Reset global data structures to force complete reload
                global summary_df, all_transactions_df, category_monthly_df, months, month_names
                
                # Reset month lists to ensure fresh load
                months = []
                month_names = []
                
                # Force reload of all data
                summary_df, all_transactions_df, category_monthly_df = load_data()
                
                # Calculate YTD values freshly
                ytd_income = summary_df['Total Income'].sum() if not summary_df.empty else 0
                ytd_expenses = summary_df['Total Expenses'].sum() if not summary_df.empty else 0
                ytd_investments = summary_df['Investments'].sum() if not summary_df.empty else 0
                ytd_surplus = summary_df['Surplus'].sum() if not summary_df.empty else 0
                
                print(f"YTD Income after refresh: {ytd_income}")
                print(f"YTD Expenses after refresh: {ytd_expenses}")
                
                # Check if files exist after refresh
                has_files = has_excel_files()
                
                # Set visibility of dashboard and no-files message
                dashboard_style = {'display': 'block'} if has_files else {'display': 'none'}
                no_files_style = {'display': 'none'} if has_files else {'display': 'block', 'marginTop': '20px'}
                
                # Get transaction data for updating all charts
                transactions_data = all_transactions_df.to_dict('records') if not all_transactions_df.empty else []
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                print(f"Dashboard refresh completed at {timestamp}")
                
                # Format the values for display
                income_display = format_inr(ytd_income)
                expenses_display = format_inr(ytd_expenses)
                investments_display = format_inr(ytd_investments)
                surplus_display = format_inr(ytd_surplus)
                
                # Get information about files loaded
                excel_files, _ = get_excel_files()
                file_count = len(excel_files)
                month_count = len(month_names)
                
                # Create toast contents with summary data
                toast_header = f"Dashboard Refreshed ({timestamp})"
                toast_content = html.Div([
                    html.H5("Refresh Summary", className="mb-2"),
                    html.P([
                        f"Files loaded: ", html.B(f"{file_count}"), 
                        " files covering ", html.B(f"{month_count}"), " months"
                    ]),
                    html.Hr(className="my-2"),
                    html.P("Year to Date Totals:", className="font-weight-bold mt-3 mb-1"),
                    html.Ul([
                        html.Li([html.Span("Income: "), html.Span(income_display, className="text-success")]),
                        html.Li([html.Span("Expenses: "), html.Span(expenses_display, className="text-danger")]),
                        html.Li([html.Span("Investments: "), html.Span(investments_display, className="text-info")]),
                        html.Li([html.Span("Surplus: "), html.Span(surplus_display, className="text-primary")])
                    ]),
                    html.P(f"Monthly Averages (across {month_count} months):", className="font-weight-bold mt-3 mb-1"),
                    html.Ul([
                        html.Li(f"Income: {format_inr(ytd_income/max(1, month_count))}"),
                        html.Li(f"Expenses: {format_inr(ytd_expenses/max(1, month_count))}"),
                        html.Li(f"Investments: {format_inr(ytd_investments/max(1, month_count))}")
                    ])
                ])
                
                return (
                    html.Div([
                        html.Span("Dashboard refreshed at {}".format(timestamp), style={'color': 'green'}),
                        html.Br(),
                        html.Span(f"Total Income (YTD): {income_display} | Total Expenses (YTD): {expenses_display}", 
                                 style={'fontSize': '0.9em', 'color': '#555'})
                    ]),
                    dashboard_style,
                    no_files_style,
                    transactions_data,  # Return updated transaction data to refresh all tabs
                    income_display,     # Update YTD cards
                    expenses_display,
                    investments_display,
                    surplus_display,
                    True,              # Show the toast
                    toast_header,      # Toast header
                    toast_content      # Toast content
                )
            except Exception as e:
                print(f"Error during refresh: {str(e)}")
                # Create error toast content
                error_toast_content = html.Div([
                    html.H5("Refresh Error", className="mb-2 text-danger"),
                    html.P("An error occurred while refreshing the dashboard:"),
                    html.P(str(e), className="p-2 bg-light border rounded text-danger")
                ])
                
                return (
                    html.Div("Error refreshing data: {}".format(str(e)), style={'color': 'red'}),
                    {'display': 'none'},
                    {'display': 'block', 'marginTop': '20px'},
                    [],  # Empty data for transactions store
                    dash.no_update,  # Don't update YTD cards on error
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    True,  # Show toast even on error
                    "Refresh Error",  # Toast header for error
                    error_toast_content  # Toast content for error
                )
        # Default case (no click event)
        return "", {'display': 'none'}, {'display': 'block', 'marginTop': '20px'}, [], dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, dash.no_update, dash.no_update
    
    @app.callback(
        Output('nwl-category-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_nwl_category_chart(transactions_data):
        df = pd.DataFrame(transactions_data)
        
        # Check if the DataFrame has the required columns
        if df.empty or 'Label' not in df.columns or 'Category' not in df.columns or 'Amount' not in df.columns:
            return px.bar(title="No data available or missing required columns")
        
        # Skip transactions without a label
        df = df[df['Label'].notna() & (df['Label'] != '')]
        
        if df.empty:
            return px.bar(title="No labeled transactions")
        
        # Use only Needs, Wants, Luxury labels
        nwl_labels = ['Needs', 'Wants', 'Luxury']
        df = df[df['Label'].isin(nwl_labels)]
        
        if df.empty:
            return px.bar(title="No N/W/L transactions found")
        
        # Ensure Amount is numeric
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df = df.dropna(subset=['Amount'])  # Drop rows where Amount couldn't be converted
        
        # Check again after potential cleanup
        if df.empty:
            return px.bar(title="No valid data after conversion")
        
        # Group by category and label
        try:
            category_label_expenses = df.groupby(['Category', 'Label'])['Amount'].sum().reset_index()
            
            # Get categories sorted by total amount
            category_totals = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
            
            # Take top 10 categories or all if less than 10
            num_categories = min(10, len(category_totals))
            top_categories = category_totals.head(num_categories).index.tolist()
            
            # Filter to include only top categories
            category_label_expenses = category_label_expenses[category_label_expenses['Category'].isin(top_categories)]
            
            # Create bar chart with specific colors
            colors = {'Needs': '#00897B', 'Wants': '#1976D2', 'Luxury': '#E53935'}
            
            fig = px.bar(
                category_label_expenses,
                x='Category',
                y='Amount',
                color='Label',
                title="Needs, Wants, Luxury Distribution by Top Categories",
                barmode='stack',
                color_discrete_map=colors
            )
            fig.update_layout(yaxis_title="Amount (₹)")
            return fig
        except Exception as e:
            # Return an error figure if any exception occurs
            return px.bar(title=f"Error generating chart: {str(e)}")
    
    return app

# Main function
def main():
    """Main entry point when running as a script"""
    app = create_app()
    
    # Add Flask routes for file downloads
    @app.server.route('/download/<path:filename>')
    def download_file(filename):
        """Allow users to download template files"""
        # For security, only allow specific template files to be downloaded
        allowed_files = ['Template.xlsx', 'BlankTemplate.xlsx']
        if filename not in allowed_files:
            return "File not allowed", 403
            
        # Get the template path
        template_path = get_template_path(filename)
        if not template_path or not os.path.exists(template_path):
            # If the template doesn't exist in the template directory, 
            # check in the data directory
            data_dir = get_data_dir()
            data_template_path = os.path.join(data_dir, filename)
            
            if os.path.exists(data_template_path):
                directory = data_dir
            else:
                print(f"Template file not found: {filename}")
                return "Template file not found", 404
        else:
            directory = os.path.dirname(template_path)
        
        # Send the file from the appropriate directory
        try:
            response = flask.send_from_directory(
                directory=directory,
                path=filename,
                as_attachment=True
            )
            
            # Set content disposition explicitly
            response.headers["Content-Disposition"] = f"attachment; filename={filename}"
            return response
        except Exception as e:
            print(f"Error sending file: {e}")
            return f"Error sending file: {e}", 500
    
    app.run(debug=True, port=8050)

# Run the app
if __name__ == '__main__':
    main()