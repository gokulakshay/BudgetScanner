"""
Callbacks for the budget dashboard
"""
import pandas as pd
import plotly.express as px
from dash import html, dcc, dash_table, callback, Output, Input, State, no_update, dash
import dash_bootstrap_components as dbc
from datetime import datetime
import os

from ..data.loader import (
    get_excel_files, has_excel_files, load_data,
    process_upload, get_data_dir, months, month_names
)
from ..utils.helpers import format_inr

def register_callbacks(app):
    """Register all callbacks for the dashboard application"""
    
    # Global variables to store data
    global summary_df, all_transactions_df, category_monthly_df
    
    @app.callback(
        Output('category-pie-chart', 'figure'),
        Input('month-dropdown', 'value')
    )
    def update_pie_chart(selected_month):
        """Update the category pie chart based on selected month"""
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
        """Update the category trend chart based on selected category"""
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
        """Update the top categories chart"""
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
        """Update the transactions table based on filters"""
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
                        'options': [
                            {'label': 'Needs (N)', 'value': 'Needs'},
                            {'label': 'Wants (W)', 'value': 'Wants'},
                            {'label': 'Luxury (L)', 'value': 'Luxury'},
                            {'label': 'Savings (S)', 'value': 'Savings'},
                            {'label': 'Investment (I)', 'value': 'Investment'}
                        ]
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
        """Filter the label transactions table based on selected month"""
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
        """Apply bulk label to transactions"""
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
        """Update labels from the table to the store"""
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
        """Save labels to file and display status"""
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
        """Update spending by person chart"""
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
        """Update spending trends by person chart"""
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
        """Update daily spending pattern chart"""
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
        """Update the label pie chart"""
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
        """Update the label trend chart"""
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
        """Update the label category chart"""
        try:
            df = pd.DataFrame(transactions_data)
            
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
            
            # Ensure Amount is numeric - convert strings to float
            df['Amount'] = df['Amount'].astype(float)
            
            # Drop any rows with NaN Amount values
            df = df.dropna(subset=['Amount'])
            
            if df.empty:
                print("No valid transaction amounts")
                return px.bar(title="No valid transaction amounts")
            
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
        """Update the NWL pie chart"""
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
        """Update the NWL trend chart"""
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
    
    @app.callback(
        Output('nwl-category-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_nwl_category_chart(transactions_data):
        """Update the NWL category chart"""
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
    
    @app.callback(
        Output('monthly-overview-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_monthly_overview_chart(transactions_data):
        """Update the monthly overview chart"""
        # Use summary_df because it already has the aggregated data
        if summary_df.empty:
            return px.bar(title="No monthly data available")
        
        # Create bar chart
        fig = px.bar(
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
        return fig
    
    @app.callback(
        Output('monthly-surplus-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_monthly_surplus_chart(transactions_data):
        """Update the monthly surplus chart"""
        # Use summary_df because it already has the aggregated data
        if summary_df.empty:
            return px.line(title="No monthly data available")
        
        # Create line chart
        fig = px.line(
            summary_df, 
            x='Month', 
            y='Surplus',
            title="Monthly Surplus Trend",
            labels={'Surplus': 'Amount (₹)'},
            markers=True
        )
        return fig
    
    @app.callback(
        Output('monthly-investments-chart', 'figure'),
        Input('transactions-store', 'data')
    )
    def update_monthly_investments_chart(transactions_data):
        """Update the monthly investments chart"""
        # Use summary_df because it already has the aggregated data
        if summary_df.empty:
            return px.line(title="No monthly data available")
        
        # Create line chart
        fig = px.line(
            summary_df, 
            x='Month', 
            y='Investments',
            title="Monthly Investments Trend",
            labels={'Investments': 'Amount (₹)'},
            markers=True
        )
        return fig
    
    # Callbacks for refresh and file management
    @app.callback(
        Output('available-files', 'children'),
        [Input('refresh-button', 'n_clicks'),
         Input('upload-output', 'children')]  # Also trigger on new upload
    )
    def update_available_files(n_clicks, upload_output):
        """Update the list of available files"""
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
        """Refresh the dashboard and update all components"""
        if n_clicks:
            # Reload data completely - this is important for proper refresh
            try:
                print("Performing complete dashboard refresh...")
                
                # Reset all global data
                global summary_df, all_transactions_df, category_monthly_df
                
                # Force reload of all data
                summary_df, all_transactions_df, category_monthly_df = load_data()
                
                # Calculate YTD values freshly
                ytd_income = summary_df['Total Income'].sum() if not summary_df.empty else 0
                ytd_expenses = summary_df['Total Expenses'].sum() if not summary_df.empty else 0
                ytd_investments = summary_df['Investments'].sum() if not summary_df.empty else 0
                ytd_surplus = summary_df['Surplus'].sum() if not summary_df.empty else 0
                
                print(f"YTD Income after refresh: {ytd_income}")
                print(f"YTD Expenses after refresh: {ytd_expenses}")
                print(f"YTD Investments after refresh: {ytd_investments}")
                print(f"YTD Surplus after refresh: {ytd_surplus}")
                
                # Check if files exist after refresh
                has_files_now = has_excel_files()
                
                # Set visibility of dashboard and no-files message
                dashboard_style = {'display': 'block'} if has_files_now else {'display': 'none'}
                no_files_style = {'display': 'none'} if has_files_now else {'display': 'block', 'marginTop': '20px'}
                
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
        """Process uploaded files and update the dashboard"""
        if list_of_contents is None:
            # Get current state of files
            has_files_now = has_excel_files()
            dashboard_style = {'display': 'block'} if has_files_now else {'display': 'none'}
            no_files_style = {'display': 'none'} if has_files_now else {'display': 'block', 'marginTop': '20px'}
            return html.Div("Upload your Excel files to get started."), dashboard_style, no_files_style, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, dash.no_update, dash.no_update
        
        upload_results = []
        data_dir = get_data_dir()
        upload_success = False
        
        for content, filename, date in zip(list_of_contents, list_of_filenames, list_of_dates):
            # Process the upload
            success, message = process_upload(content, filename, date, data_dir)
            
            if success:
                upload_success = True
                upload_results.append(html.Div([
                    html.Span("✅ " + message, style={'color': 'green'})
                ]))
                print(f"Successfully uploaded file: {filename}")
            else:
                upload_results.append(html.Div(message, style={'color': 'red'}))
                print(f"Error uploading file {filename}: {message}")
        
        # If any upload was successful, reload data
        if upload_success:
            try:
                print("Upload was successful, performing complete data reload...")
                
                # Reset global data
                global summary_df, all_transactions_df, category_monthly_df
                
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
                
                # Check if we have files after upload
                has_files_now = has_excel_files()
                dashboard_style = {'display': 'block'} if has_files_now else {'display': 'none'}
                no_files_style = {'display': 'none'} if has_files_now else {'display': 'block', 'marginTop': '20px'}
                
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
                
                # Check if we have files after upload
                has_files_now = has_excel_files()
                dashboard_style = {'display': 'block'} if has_files_now else {'display': 'none'}
                no_files_style = {'display': 'none'} if has_files_now else {'display': 'block', 'marginTop': '20px'}
                
                # Keep YTD displays the same if there's an error
                return html.Div(upload_results), dashboard_style, no_files_style, transactions_data, dash.no_update, dash.no_update, dash.no_update, dash.no_update, True, "Upload Error", error_toast_content
        else:
            # Add message to use refresh button if no successful uploads
            upload_results.append(html.Div(
                "No files were successfully uploaded. Verify file format and try again.",
                style={'fontWeight': 'bold', 'marginTop': '10px', 'color': 'orange'}
            ))
            transactions_data = dash.no_update
            
            # Check if we have files after upload
            has_files_now = has_excel_files()
            dashboard_style = {'display': 'block'} if has_files_now else {'display': 'none'}
            no_files_style = {'display': 'none'} if has_files_now else {'display': 'block', 'marginTop': '20px'}
            
            # Keep YTD displays the same if there's no successful upload
            return html.Div(upload_results), dashboard_style, no_files_style, transactions_data, dash.no_update, dash.no_update, dash.no_update, dash.no_update, True, "Upload Warning", html.P("No files were successfully uploaded. Please check the file format and try again.")