"""
Main layout for the budget dashboard
"""
import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
from datetime import datetime
import pandas as pd

from ..data.loader import has_excel_files, get_excel_files, dashboard_errors
from ..components.cards import (
    create_ytd_summary_cards,
    create_monthly_averages_cards,
    create_financial_planning_cards
)
from ..utils.helpers import format_inr

def create_file_upload_section():
    """Create the file upload section of the dashboard"""
    return dbc.Row([
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
    ])

def create_error_container():
    """Create the error container for displaying data loading errors"""
    return dbc.Row([
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
    ])

def create_toast_container():
    """Create the toast container for notifications"""
    return html.Div(
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

def create_layout(summary_df, all_transactions_df, category_monthly_df, month_names=[]):
    """
    Create the main layout for the dashboard application
    
    Args:
        summary_df: DataFrame containing summary data
        all_transactions_df: DataFrame containing all transactions
        category_monthly_df: DataFrame containing category expenses by month
        month_names: List of month names
        
    Returns:
        A dbc.Container component containing the full dashboard layout
    """
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
    
    # Calculate YTD values
    ytd_income = summary_df['Total Income'].sum() if not summary_df.empty else 0
    ytd_expenses = summary_df['Total Expenses'].sum() if not summary_df.empty else 0
    ytd_investments = summary_df['Investments'].sum() if not summary_df.empty else 0
    ytd_surplus = summary_df['Surplus'].sum() if not summary_df.empty else 0
    
    # Calculate averages, preventing division by zero
    month_count = max(1, len(month_names))  # Ensure at least 1 to prevent division by zero
    avg_monthly_income = ytd_income / month_count
    avg_monthly_expenses = ytd_expenses / month_count
    avg_monthly_investments = ytd_investments / month_count
    avg_monthly_surplus = ytd_surplus / month_count
    
    # Calculate average monthly needs and emergency fund
    avg_monthly_needs = avg_monthly_expenses * 0.5  # Default: 50% of expenses
    emergency_fund_suggestion = avg_monthly_needs * 6  # Default: 6 months of needs
    
    # If we have labeled data, calculate based on actual "Needs" transactions
    if not all_transactions_df.empty and 'Label' in all_transactions_df.columns:
        # Get transactions labeled as 'Needs'
        needs_transactions = all_transactions_df[all_transactions_df['Label'] == 'Needs']
        if not needs_transactions.empty:
            # Calculate total needs expenses across all months
            total_needs = needs_transactions['Amount'].sum()
            # Calculate average monthly needs (total / number of months)
            avg_monthly_needs = total_needs / month_count
            # Calculate emergency fund suggestion (6 times monthly needs)
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
    
    # Create the app layout
    return dbc.Container([
        # Toast container for notifications
        create_toast_container(),
        
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("Personal Budget Dashboard - 2025", className="text-center mt-3 mb-4"),
            ], width=12)
        ]),
        
        # File Upload Section
        create_file_upload_section(),
        
        # Dashboard Content - only shown when files are available
        html.Div(id="dashboard-content", style={'display': 'block' if has_excel_files() else 'none'}, children=[
        
            # Error message row - only visible when there are errors
            create_error_container(),
            
            # YTD Summary Cards
            create_ytd_summary_cards(ytd_income, ytd_expenses, ytd_investments, ytd_surplus),
            
            # N/W/L Financial Planning Cards
            create_financial_planning_cards(avg_monthly_needs, emergency_fund_suggestion),
            
            # Monthly Average Cards
            create_monthly_averages_cards(avg_monthly_income, avg_monthly_expenses, 
                                         avg_monthly_investments, avg_monthly_surplus),
            
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
                            dcc.Graph(id='monthly-overview-chart')
                        ], width=12),
                    ]),
                    
                    dbc.Row([
                        dbc.Col([
                            html.H4("Surplus by Month", className="text-center mt-4 mb-2"),
                            dcc.Graph(id='monthly-surplus-chart')
                        ], width=6),
                        
                        dbc.Col([
                            html.H4("Investments by Month", className="text-center mt-4 mb-2"),
                            dcc.Graph(id='monthly-investments-chart')
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