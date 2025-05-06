#!/usr/bin/env python3
"""
This script creates a template Excel file with sample data
to guide users on how to format their own budget data.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
import random

def create_template_excel():
    """Create a template Excel file with sample data."""
    # Define the output directory and file path
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    template_path = os.path.join(output_dir, 'Template.xlsx')
    
    # Create a sample date range for the current month
    today = datetime.now()
    start_date = datetime(today.year, today.month, 1)
    
    # If current month is not January, use January for the template
    if today.month != 1:
        start_date = datetime(today.year, 1, 1)
    
    # Generate 30 days of data
    dates = [start_date + timedelta(days=i) for i in range(30)]
    
    # Sample categories
    expense_categories = [
        'Housing', 'Utilities', 'Groceries', 'Dining Out', 'Transportation',
        'Health', 'Entertainment', 'Shopping', 'Education', 'Personal Care',
        'Insurance', 'Debt Payments', 'Subscriptions', 'Gifts & Donations'
    ]
    
    investment_categories = [
        'Investment: Stocks', 'Investment: Mutual Funds', 'Investment: Fixed Deposit', 
        'Investment: Gold', 'Investment: Retirement'
    ]
    
    # Sample people
    people = ['Self', 'Spouse', 'Family']
    
    # Sample vendors
    vendors = [
        'Local Grocery Store', 'Supermarket', 'Restaurant', 'Cafe', 'Gas Station',
        'Electric Company', 'Internet Provider', 'Mobile Provider', 'Pharmacy',
        'Department Store', 'Online Shop', 'Cinema', 'Gym', 'Bank', 'Insurance Company'
    ]
    
    # Sample labels (Needs, Wants, Luxury)
    labels = ['N', 'W', 'L', 'S', 'I']
    
    # Sample descriptions
    descriptions = {
        'Housing': ['Rent Payment', 'Maintenance', 'Property Tax'],
        'Utilities': ['Electricity Bill', 'Water Bill', 'Internet Bill', 'Mobile Bill'],
        'Groceries': ['Weekly Groceries', 'Fresh Produce', 'Household Supplies'],
        'Dining Out': ['Lunch with Colleagues', 'Dinner', 'Coffee', 'Restaurant'],
        'Transportation': ['Fuel', 'Bus Fare', 'Taxi', 'Vehicle Maintenance'],
        'Health': ['Doctor Visit', 'Medications', 'Health Insurance', 'Gym Membership'],
        'Entertainment': ['Movie Tickets', 'Streaming Service', 'Concert', 'Books'],
        'Shopping': ['Clothes', 'Electronics', 'Home Decor', 'Gifts'],
        'Education': ['Course Fee', 'Books', 'Online Class', 'School Supplies'],
        'Personal Care': ['Haircut', 'Skincare Products', 'Salon Visit'],
        'Insurance': ['Life Insurance', 'Vehicle Insurance', 'Home Insurance'],
        'Debt Payments': ['Credit Card Payment', 'Loan EMI', 'Interest Payment'],
        'Subscriptions': ['Streaming Service', 'Magazine', 'Software Subscription'],
        'Gifts & Donations': ['Birthday Gift', 'Charity Donation', 'Festival Gift']
    }
    
    # Generate random transactions
    transactions = []
    
    # Regular expenses
    for _ in range(40):  # 40 regular transactions
        date = random.choice(dates)
        category = random.choice(expense_categories)
        description = random.choice(descriptions.get(category, [f"{category} expense"]))
        amount = round(random.uniform(100, 5000), 2)  # Random amount between 100 and 5000
        who = random.choice(people)
        whom = random.choice(vendors)
        label = random.choice(['N', 'W', 'L'])  # Assign N, W, or L randomly
        
        transactions.append({
            'Date': date,
            'Amount': amount,
            'Description': description,
            'Category': category,
            'Who': who,
            'Whom': whom,
            'Label': label
        })
    
    # Investment transactions
    for _ in range(5):  # 5 investment transactions
        date = random.choice(dates)
        category = random.choice(investment_categories)
        description = f"{category.replace('Investment: ', '')} Contribution"
        amount = round(random.uniform(5000, 50000), 2)  # Higher amounts for investments
        who = random.choice(people)
        whom = 'Investment Platform'
        label = 'I'  # Investment label
        
        transactions.append({
            'Date': date,
            'Amount': amount,
            'Description': description,
            'Category': category,
            'Who': who,
            'Whom': whom,
            'Label': label
        })
    
    # Create DataFrame
    transactions_df = pd.DataFrame(transactions)
    
    # Sort by date
    transactions_df = transactions_df.sort_values('Date')
    
    # Create a summary sheet with instructions
    summary_data = {
        'Column': ['Date', 'Amount', 'Description', 'Category', 'Who', 'Whom', 'Label'],
        'Description': [
            'Date of the transaction (YYYY-MM-DD format)',
            'Amount spent/invested in your currency',
            'Brief description of the transaction',
            'Category of expense or investment',
            'Person who made the transaction',
            'Vendor or recipient of the payment',
            'Label: N (Needs), W (Wants), L (Luxury), S (Savings), I (Investment)'
        ],
        'Example': [
            datetime.now().strftime('%Y-%m-%d'),
            '1500.00',
            'Weekly Groceries',
            'Groceries',
            'Self',
            'Local Grocery Store',
            'N'
        ],
        'Required': ['Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No']
    }
    
    summary_df = pd.DataFrame(summary_data)
    
    # Create a new Excel writer
    with pd.ExcelWriter(template_path, engine='openpyxl') as writer:
        # Write summary sheet with instructions
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Write transactions sheet
        transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
    
    print(f"Template Excel file created at: {template_path}")
    
    # Also create a blank template without data
    blank_template_path = os.path.join(output_dir, 'BlankTemplate.xlsx')
    
    # Create blank transactions DataFrame with correct column structure
    blank_df = pd.DataFrame(columns=['Date', 'Amount', 'Description', 'Category', 'Who', 'Whom', 'Label'])
    
    # Create a new Excel writer for blank template
    with pd.ExcelWriter(blank_template_path, engine='openpyxl') as writer:
        # Write summary sheet with instructions
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Write blank transactions sheet
        blank_df.to_excel(writer, sheet_name='Transactions', index=False)
    
    print(f"Blank template Excel file created at: {blank_template_path}")
    
    return template_path, blank_template_path

if __name__ == "__main__":
    create_template_excel()