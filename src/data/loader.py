"""
Data loading and processing functions for budget dashboard
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime
import base64
import io
import shutil

from ..utils.helpers import get_data_dir, get_template_path

# Global variables to store month information
months = []
month_names = []
dashboard_errors = []

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

def load_data():
    """
    Load and process Excel files from the data directory
    Returns summary_df, all_transactions_df, category_monthly_df
    """
    # Get the data directory and Excel files
    data_dir = get_data_dir()
    print("Loading data from {}".format(data_dir))
    
    # Get excel files and extract month names
    global months, month_names, dashboard_errors
    excel_files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]
    
    # Reset global month lists
    months = []
    month_names = []
    
    # Extract month names from filenames
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

def process_upload(contents, filename, date, data_dir=None):
    """
    Process an uploaded file and save it to the data directory
    
    Args:
        contents: The file contents as a base64 string
        filename: The filename
        date: The upload date timestamp
        data_dir: Optional data directory, if not provided get_data_dir() will be used
    
    Returns:
        (success, error_message)
    """
    if not filename.endswith('.xlsx'):
        return False, f"Error: {filename} is not an Excel file. Only .xlsx files are supported."
            
    try:
        # Decode content
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Get data directory if not provided
        if data_dir is None:
            data_dir = get_data_dir()
        
        # Save file to data directory
        file_path = os.path.join(data_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(decoded)
        
        timestamp = datetime.fromtimestamp(date/1000).strftime('%Y-%m-%d %H:%M:%S')
        return True, f"Uploaded: {filename} ({timestamp})"
        
    except Exception as e:
        return False, f"Error processing {filename}: {str(e)}"