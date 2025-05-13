"""
Main application file for the budget dashboard
"""
import dash
import dash_bootstrap_components as dbc
import flask
from dash import html, dcc, callback_context
import os

from .data.loader import load_data, get_data_dir, get_template_path, month_names
from .layouts.main_layout import create_layout
from .callbacks.dashboard_callbacks import register_callbacks

def create_app():
    """Create and configure the Dash application"""
    # Load the data
    summary_df, all_transactions_df, category_monthly_df = load_data()
    
    # Initialize the Dash app with callback exceptions suppressed
    app = dash.Dash(
        __name__, 
        external_stylesheets=[dbc.themes.BOOTSTRAP], 
        suppress_callback_exceptions=True
    )
    
    # Set app layout
    app.layout = create_layout(summary_df, all_transactions_df, category_monthly_df, month_names)
    
    # Register callbacks
    register_callbacks(app)
    
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
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=8050)