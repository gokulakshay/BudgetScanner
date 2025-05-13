"""
Card components for the budget dashboard
"""
import dash_bootstrap_components as dbc
from dash import html

from ..utils.helpers import format_inr

def create_summary_card(title, value, color_class, card_id=None):
    """
    Create a summary card for displaying financial information
    
    Args:
        title: The card title
        value: The value to display
        color_class: CSS class for the value color (e.g., 'text-success')
        card_id: Optional ID for the value element
    
    Returns:
        A dbc.Card component
    """
    # Create the H3 component with or without an ID based on whether card_id is provided
    if card_id:
        h3_component = html.H3(value, id=card_id, className=f"text-center {color_class}")
    else:
        h3_component = html.H3(value, className=f"text-center {color_class}")
        
    return dbc.Card([
        dbc.CardHeader(title, className="text-center"),
        dbc.CardBody([h3_component])
    ], className="mb-4")

def create_ytd_summary_cards(ytd_income, ytd_expenses, ytd_investments, ytd_surplus):
    """
    Create a row of summary cards for YTD financial information
    
    Args:
        ytd_income: Year-to-date income value
        ytd_expenses: Year-to-date expenses value
        ytd_investments: Year-to-date investments value
        ytd_surplus: Year-to-date surplus value
    
    Returns:
        A dbc.Row component containing cards
    """
    return dbc.Row([
        dbc.Col([
            create_summary_card(
                "Total Income (YTD)",
                format_inr(ytd_income),
                "text-success",
                "ytd-income-display"
            )
        ], width=3),
        
        dbc.Col([
            create_summary_card(
                "Total Expenses (YTD)",
                format_inr(ytd_expenses),
                "text-danger",
                "ytd-expenses-display"
            )
        ], width=3),
        
        dbc.Col([
            create_summary_card(
                "Total Investments (YTD)",
                format_inr(ytd_investments),
                "text-info",
                "ytd-investments-display"
            )
        ], width=3),
        
        dbc.Col([
            create_summary_card(
                "Total Surplus (YTD)",
                format_inr(ytd_surplus),
                "text-primary",
                "ytd-surplus-display"
            )
        ], width=3)
    ])

def create_monthly_averages_cards(avg_monthly_income, avg_monthly_expenses, 
                                 avg_monthly_investments, avg_monthly_surplus):
    """
    Create a row of summary cards for monthly average financial information
    
    Args:
        avg_monthly_income: Average monthly income value
        avg_monthly_expenses: Average monthly expenses value
        avg_monthly_investments: Average monthly investments value
        avg_monthly_surplus: Average monthly surplus value
    
    Returns:
        A dbc.Row component containing cards
    """
    return dbc.Row([
        dbc.Col([
            create_summary_card(
                "Avg. Monthly Income",
                format_inr(avg_monthly_income),
                "text-dark",
                "avg-monthly-income-value"
            )
        ], width=3),
        
        dbc.Col([
            create_summary_card(
                "Avg. Monthly Expenses",
                format_inr(avg_monthly_expenses),
                "text-dark",
                "avg-monthly-expenses-value"
            )
        ], width=3),
        
        dbc.Col([
            create_summary_card(
                "Avg. Monthly Investments",
                format_inr(avg_monthly_investments),
                "text-dark",
                "avg-monthly-investments-value"
            )
        ], width=3),
        
        dbc.Col([
            create_summary_card(
                "Avg. Monthly Surplus",
                format_inr(avg_monthly_surplus),
                "text-dark",
                "avg-monthly-surplus-value"
            )
        ], width=3)
    ])

def create_financial_planning_cards(avg_monthly_needs, emergency_fund_suggestion):
    """
    Create cards for financial planning information
    
    Args:
        avg_monthly_needs: Average monthly needs value
        emergency_fund_suggestion: Suggested emergency fund value
    
    Returns:
        A dbc.Row component containing cards
    """
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    "Suggested Monthly Needs",
                    html.Span(" ℹ️", id="monthly-needs-info", style={"cursor": "pointer"})
                ], className="text-center d-flex justify-content-center align-items-center"),
                dbc.CardBody([
                    html.H3(format_inr(avg_monthly_needs), id="monthly-needs-value", className="text-center", style={"color": "#00897B"})
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
                    html.H3(format_inr(emergency_fund_suggestion), id="emergency-fund-value", className="text-center", style={"color": "#E53935"})
                ]),
                dbc.Tooltip(
                    "Calculated as 6 months of your monthly needs. This is the recommended amount to keep as an emergency fund.",
                    target="emergency-fund-info"
                )
            ], className="mb-4")
        ], width=6)
    ])