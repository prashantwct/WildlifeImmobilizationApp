"""
Carnivore GPS Tracking Analysis Dashboard
Main application file
"""

import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import requests
import os
import base64
import io

# Create the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, 'https://use.fontawesome.com/releases/v5.15.4/css/all.css'],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True
)
server = app.server
app.title = "Carnivore GPS Tracking Dashboard"

# Import components and pages after app initialization
from components.analysis import (
    calculate_daily_distance, calculate_nsd, calculate_home_range,
    calculate_activity_patterns, calculate_speed_metrics, calculate_fix_success,
    calculate_core_peripheral_zones
)

# Create a navigation sidebar with the expanded sections
sidebar = html.Div(
    [
        html.Div(
            [
                html.Img(src="/assets/logo.png", className="sidebar-logo"),
                html.H3("Carnivore GPS Tracking", className="sidebar-title"),
            ],
            className="sidebar-header"
        ),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink([html.I(className="fas fa-home me-2"), "Dashboard"], href="/", active="exact"),
                dbc.NavLink([html.I(className="fas fa-database me-2"), "Data Import"], href="/data-import", active="exact"),
                dbc.NavLink([html.I(className="fas fa-map-marked-alt me-2"), "Map Visualization"], href="/map", active="exact"),
                dbc.NavLink([html.I(className="fas fa-route me-2"), "Movement Analysis"], href="/movement", active="exact"),
                dbc.NavLink([html.I(className="fas fa-chart-area me-2"), "Home Range"], href="/home-range", active="exact"),
                dbc.NavLink([html.I(className="fas fa-clock me-2"), "Behavioral Patterns"], href="/behavior", active="exact"),
                dbc.NavLink([html.I(className="fas fa-mountain me-2"), "Environmental Context"], href="/environment", active="exact"),
                dbc.NavLink([html.I(className="fas fa-check-circle me-2"), "Data Quality"], href="/quality", active="exact"),
                dbc.NavLink([html.I(className="fas fa-question-circle me-2"), "Help"], href="/help", active="exact"),
            ],
            vertical=True,
            pills=True,
            className="sidebar-nav"
        ),
        html.Hr(),
        html.Div(
            [
                html.P("Selected Animals:", className="mb-1 text-muted"),
                html.Div(id="selected-animals-display", className="selected-items"),
                html.P("Date Range:", className="mb-1 mt-3 text-muted"),
                html.Div(id="selected-dates-display", className="selected-items"),
            ],
            className="sidebar-footer"
        )
    ],
    className="sidebar",
)

# Create app layout with main content area
app.layout = html.Div(
    [
        # Data stores for sharing between components
        dcc.Store(id="store-movement-data"),
        dcc.Store(id="store-daily-distance"),
        dcc.Store(id="store-home-range"),
        dcc.Store(id="store-activity"),
        dcc.Store(id="store-speed"),
        dcc.Store(id="store-quality"),
        dcc.Store(id="store-filters"),
        dcc.Store(id="study-id-store"),  # Store for the current study ID
        
        # Date filter component that's used by several callbacks
        dcc.DatePickerRange(id="date-filter", start_date=None, end_date=None, style={"display": "none"}),
        
        # Hidden behavioral analysis components needed by callbacks
        dbc.Input(id="behavioral-activity-threshold", type="number", value=0.05, style={"display": "none"}),
        dbc.Input(id="behavioral-time-window", type="number", value=60, style={"display": "none"}),
        dcc.Dropdown(id="behavioral-individuals", multi=True, style={"display": "none"}),
        dcc.Dropdown(id="behavioral-timeline-individual", style={"display": "none"}),
        
        # Home range analysis hidden components needed by callbacks
        dbc.RadioItems(
            id="home-range-method",
            options=[
                {"label": "Kernel Density Estimation (KDE)", "value": "kde"},
                {"label": "Minimum Convex Polygon (MCP)", "value": "mcp"},
                {"label": "Time Local Convex Hull (T-LoCoH)", "value": "tlocoh"},
                {"label": "Brownian Bridge", "value": "brownian"}
            ],
            value="kde",
            style={"display": "none"}
        ),
        html.Div([
            dcc.Slider(id="home-range-percent", min=50, max=100, step=5, value=95),
            dcc.Slider(id="home-range-grid", min=50, max=200, step=25, value=100),
            dcc.Slider(id="home-range-smoothing", min=0.1, max=2.0, step=0.1, value=1.0)
        ], style={"display": "none"}),
        dcc.Dropdown(id="home-range-individuals", multi=True, style={"display": "none"}),
        
        # License alert modal for Movebank data
        dbc.Modal(
            [
                dbc.ModalHeader("License Agreement Required"),
                dbc.ModalBody([
                    html.Div(id="license-text"),
                    html.Div(
                        dbc.Button("Accept License Terms", id="accept-license-btn", color="success", className="mt-3"),
                        className="text-center"
                    ),
                ]),
            ],
            id="license-alert",
            is_open=False,
            backdrop="static",
            centered=True,
            size="lg",
        ),
        
        # License acceptance container
        html.Div(id="license-acceptance-container", style={"display": "none"}),
        
        # URL location
        dcc.Location(id="url", refresh=False),
        
        # Main layout with sidebar and content
        dbc.Row(
            [
                # Sidebar
                dbc.Col(sidebar, width=2, className="sidebar-col"),
                
                # Main content area
                dbc.Col(
                    html.Div(id="page-content", className="content"),
                    width=10, className="content-col"
                ),
            ],
            className="g-0",
        ),
        
        # Loading spinner for data operations
        dcc.Loading(
            id="loading-data",
            type="circle",
            children=html.Div(id="loading-output")
        ),
        
        # Interval component for periodic updates (can be enabled if needed)
        dcc.Interval(
            id="interval-component",
            interval=300000,  # 5 minutes in milliseconds
            n_intervals=0,
            disabled=True
        ),
    ]
)

# Import pages after app layout initialization
from pages.dashboard import layout as dashboard_layout
from pages.data_import import layout as data_import_layout
from pages.map_visualization import layout as map_layout
from pages.movement_analysis import layout as movement_layout
from pages.home_range_analysis import layout as home_range_layout
from pages.behavioral_patterns import layout as behavior_layout
from pages.environmental_context import layout as environment_layout
from pages.data_quality import layout as quality_layout
from pages.help import layout as help_layout

# Callback to update page content based on URL
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def render_page_content(pathname):
    if pathname == "/":
        return dashboard_layout
    elif pathname == "/data-import":
        return data_import_layout
    elif pathname == "/map":
        return map_layout
    elif pathname == "/movement":
        return movement_layout
    elif pathname == "/home-range":
        return home_range_layout
    elif pathname == "/behavior":
        return behavior_layout
    elif pathname == "/environment":
        return environment_layout
    elif pathname == "/quality":
        return quality_layout
    elif pathname == "/help":
        return help_layout
    else:
        # If the user tries to reach a different page, return a 404 message
        return html.Div(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognized..."),
                dbc.Button("Return to Dashboard", color="primary", href="/"),
            ],
            className="p-3 bg-light rounded-3",
        )

# Callback to update selected animals display
@app.callback(
    Output("selected-animals-display", "children"),
    Input("store-filters", "data")
)
def update_selected_animals(filters):
    if not filters:
        return "None selected"
    
    try:
        filters = json.loads(filters)
        if "individual_ids" in filters and filters["individual_ids"]:
            individual_ids = filters["individual_ids"]
            if len(individual_ids) > 3:
                return f"{len(individual_ids)} animals selected"
            elif len(individual_ids) > 0:
                return ", ".join(individual_ids)
        return "None selected"
    except:
        return "None selected"

# Callback to update selected date range display
@app.callback(
    Output("selected-dates-display", "children"),
    Input("store-filters", "data")
)
def update_selected_dates(filters):
    if not filters:
        return "No date range set"
    
    try:
        filters = json.loads(filters)
        if "start_date" in filters and "end_date" in filters:
            start = filters["start_date"]
            end = filters["end_date"]
            if start and end:
                return f"{start} to {end}"
        return "No date range set"
    except:
        return "No date range set"

# Callbacks for Movebank authentication
@callback(
    [
        Output("auth-status", "children"),
        Output("auth-status", "color"),
        Output("study-selection-container", "style"),
        Output("movebank-studies-store", "data"),
    ],
    [Input("authenticate-btn", "n_clicks")],
    [
        State("movebank-username", "value"),
        State("movebank-password", "value"),
    ],
    prevent_initial_call=True,
)
def authenticate_movebank(n_clicks, username, password):
    if n_clicks is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    if not username or not password:
        return "Please provide both username and password", "danger", {"display": "none"}, None
    
    try:
        # Create MoveBank instance and authenticate
        movebank = MoveBank()
        success = movebank.authenticate(username, password)
        
        if success:
            # Get available studies
            studies = movebank.get_studies()
            
            if studies:
                return (
                    f"Successfully authenticated as {username}",
                    "success",
                    {"display": "block"},
                    studies.to_dict("records"),
                )
            else:
                return "Authentication successful but no studies found", "warning", {"display": "none"}, None
        else:
            return "Authentication failed. Check your credentials.", "danger", {"display": "none"}, None
    except Exception as e:
        return f"Error: {str(e)}", "danger", {"display": "none"}, None

# Callback to update study dropdown based on authentication
@callback(
    Output("study-dropdown", "options"),
    Input("movebank-studies-store", "data"),
    prevent_initial_call=True,
)
def update_study_options(studies_data):
    if not studies_data:
        return []
    
    studies_df = pd.DataFrame(studies_data)
    options = [
        {"label": f"{row['name']} ({row['id']})", "value": row['id']} for _, row in studies_df.iterrows()
    ]
    return options

# Callback to get individuals from selected study
@callback(
    [
        Output("individuals-dropdown", "options"),
        Output("study-info", "children"),
        Output("license-alert", "is_open"),
        Output("license-text", "children"),
        Output("study-id-store", "data"),
    ],
    Input("study-dropdown", "value"),
    [State("movebank-username", "value"), State("movebank-password", "value")],
    prevent_initial_call=True,
)
def update_individuals(study_id, username, password):
    if not study_id:
        return [], "No study selected", False, "", None
    
    try:
        # Create MoveBank instance and authenticate
        movebank = MoveBank()
        success = movebank.authenticate(username, password)
        
        if success:
            # Get study details
            study_details = movebank.get_study_details(study_id)
            
            # Check if study requires license acceptance
            license_required = study_details.get('license_terms') is not None
            license_text = study_details.get('license_terms', "No license terms available")
            
            # Get individuals in study
            individuals = movebank.get_individuals(study_id)
            
            if individuals is not None and not individuals.empty:
                options = [
                    {"label": f"{row['individual_local_identifier']} ({row['individual_id']})", "value": row['individual_id']} 
                    for _, row in individuals.iterrows()
                ]
                
                study_info = [
                    html.H5(study_details.get('name', f"Study {study_id}")),
                    html.P(f"Taxa: {study_details.get('taxon_ids', 'Not specified')}"),
                    html.P(f"Number of individuals: {len(individuals)}"),
                    html.P(f"Principal investigator: {study_details.get('principal_investigator_name', 'Not specified')}"),
                ]
                
                return options, study_info, license_required, license_text, study_id
            else:
                return [], f"No individuals found in study {study_id}", False, "", study_id
        else:
            return [], "Authentication error", False, "", None
    except Exception as e:
        return [], f"Error: {str(e)}", False, "", None

# Callback to accept license and proceed
@callback(
    Output("license-acceptance-container", "style"),
    Input("accept-license-btn", "n_clicks"),
    [State("study-id-store", "data"), State("movebank-username", "value"), State("movebank-password", "value")],
    prevent_initial_call=True,
)
def accept_license(n_clicks, study_id, username, password):
    if n_clicks is None or not study_id:
        return {"display": "none"}
    
    try:
        movebank = MoveBank()
        success = movebank.authenticate(username, password)
        
        if success:
            movebank.accept_license_terms(study_id)
            return {"display": "none"}
        else:
            return {"display": "block"}
    except Exception:
        return {"display": "block"}


# Callback to display selected animals
@callback(
    Output("selected-animals-display", "children"),
    Input("individuals-dropdown", "value"),
    prevent_initial_call=True
)
def update_selected_animals(selected_individuals):
    if not selected_individuals:
        return "None selected"
    if isinstance(selected_individuals, list):
        if len(selected_individuals) == 0:
            return "None selected"
        if len(selected_individuals) > 3:
            return f"{len(selected_individuals)} animals selected"
        return ", ".join(str(ind) for ind in selected_individuals)
    return str(selected_individuals)

# Callback to display selected date range
@callback(
    Output("selected-dates-display", "children"),
    [Input("start-date-picker", "date"), Input("end-date-picker", "date")],
    prevent_initial_call=True
)
def update_selected_dates(start_date, end_date):
    if not start_date and not end_date:
        return "No date range set"
    if start_date and end_date:
        return f"{start_date} to {end_date}"
    if start_date:
        return f"From {start_date}"
    if end_date:
        return f"Up to {end_date}"
    return "No date range set"

# Callback to filter preview table based on filters
@callback(
    [
        Output("data-preview-table", "data"),
        Output("data-preview-table", "columns"),
        Output("data-summary", "children"),
    ],
    Input("apply-filters-btn", "n_clicks"),
    [
        State("store-movement-data", "data"),
        State("individuals-dropdown", "value"),
        State("start-date-picker", "date"),
        State("end-date-picker", "date"),
    ],
    prevent_initial_call=True
)
def apply_filters_to_preview(n_clicks, movement_data_json, selected_individuals, start_date, end_date):
    if not movement_data_json:
        return [], [], "No data imported."
    try:
        df = pd.read_json(movement_data_json, orient='split')
        # Filter individuals
        if selected_individuals:
            df = df[df["individual_id"].isin(selected_individuals)]
        # Filter date range
        if start_date:
            df = df[df["timestamp"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["timestamp"] <= pd.to_datetime(end_date)]
        # Prepare preview
        preview_df = df.head(10).copy()
        if 'timestamp' in preview_df.columns:
            preview_df['timestamp'] = preview_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        columns = [{'name': col, 'id': col} for col in preview_df.columns]
        data = preview_df.to_dict('records')
        # Summary
        if df.empty:
            summary = html.Div("No records match the selected filters.")
        else:
            num_individuals = df['individual_id'].nunique()
            date_range = f"{df['timestamp'].min().strftime('%Y-%m-%d')} to {df['timestamp'].max().strftime('%Y-%m-%d')}"
            summary = html.Div([
                html.Strong(f"{len(df):,} records after filtering. "),
                html.Span(f"{num_individuals} individuals, {date_range}")
            ])
        return data, columns, summary
    except Exception as e:
        return [], [], f"Error applying filters: {str(e)}"

# Callback to handle CSV file upload
@callback(
    [
        Output("store-movement-data", "data"),
        Output("upload-status", "children"),
        Output("data-preview-container", "style"),
        Output("data-preview-table", "columns"),
        Output("data-preview-table", "data"),
    ],
    Input("upload-movebank-csv", "contents"),
    [State("upload-movebank-csv", "filename"), State("upload-movebank-csv", "last_modified")],
    prevent_initial_call=True
)
def process_csv_upload(contents, filename, last_modified):
    print("DEBUG: process_csv_upload called", contents is not None, filename, last_modified, flush=True)
    if contents is None:
        return None, dash.no_update, {"display": "none"}, [], []
    
    if not filename.lower().endswith('.csv'):
        error_message = html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Please upload a CSV file."
        ], className="text-danger")
        return None, error_message, {"display": "none"}, [], []
    
    try:
        # Decode the contents
        content_type, content_string = contents.split(',', 1)
        decoded = base64.b64decode(content_string)
        
        # Try to parse the CSV file
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        
        # Check required columns - try alternative column names
        required_cols_mapping = {
            'individual_id': ['individual_id', 'individual-id', 'id', 'animal_id', 'animal-id', 'tag_id', 'tag-id'],
            'timestamp': ['timestamp', 'time', 'date', 'datetime', 'date_time', 'date-time'],
            'location_lat': ['location_lat', 'location-lat', 'latitude', 'lat', 'y'],
            'location_long': ['location_long', 'location-long', 'longitude', 'long', 'lon', 'x']
        }
        
        # Map actual column names to required column names
        col_mapping = {}
        missing_cols = []
        
        for req_col, alternatives in required_cols_mapping.items():
            found = False
            for alt in alternatives:
                if alt in df.columns:
                    col_mapping[alt] = req_col
                    found = True
                    break
            if not found:
                missing_cols.append(req_col)
        
        # Rename columns if needed
        if col_mapping and not missing_cols:
            df = df.rename(columns=col_mapping)
        
        # Check if any required columns are still missing
        if missing_cols:
            error_message = html.Div([
                html.I(className="fas fa-exclamation-triangle me-2"),
                html.Span(["Missing required columns: ", html.Strong(", ".join(missing_cols))]),
                html.Br(),
                html.Small("Required columns: individual_id, timestamp, location_lat, location_long")
            ], className="text-danger")
            return None, error_message, {"display": "none"}, [], []
        
        # Convert timestamp to datetime if it's not already
        try:
            if df['timestamp'].dtype == 'object':
                df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            print(f"Error converting timestamp: {str(e)}")
            error_message = html.Div([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Could not parse timestamp column. Please ensure it's in a standard format (e.g., 'YYYY-MM-DD HH:MM:SS')."
            ], className="text-danger")
            return None, error_message, {"display": "none"}, [], []
        
        # Sort data by individual_id and timestamp
        df = df.sort_values(['individual_id', 'timestamp'])
        
        # Create a preview of the data
        preview_df = df.head(10).copy()  # Create a copy to avoid SettingWithCopyWarning
        
        # Format timestamp for display
        if 'timestamp' in preview_df.columns:
            preview_df['timestamp'] = preview_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Format columns for display
        preview_columns = [{'name': col, 'id': col} for col in preview_df.columns]
        preview_data = preview_df.to_dict('records')
        
        # Create success message with stats
        num_individuals = df['individual_id'].nunique()
        date_range = f"{df['timestamp'].min().strftime('%Y-%m-%d')} to {df['timestamp'].max().strftime('%Y-%m-%d')}"
        
        success_message = html.Div([
            html.I(className="fas fa-check-circle me-2"),
            html.Div([
                html.Strong(f"Successfully loaded {len(df):,} records from {filename}"),
                html.Br(),
                html.Span(f"Found {num_individuals} individuals with data ranging from {date_range}")
            ])
        ], className="text-success p-2 bg-light border rounded")
        
        # Store the movement data as JSON
        movement_data_json = df.to_json(date_format='iso', orient='split')
        
        return movement_data_json, success_message, {"display": "block"}, preview_columns, preview_data
        
    except Exception as e:
        error_message = html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error processing CSV file: {str(e)}"
        ], className="text-danger")
        return None, error_message, {"display": "none"}, [], []

# CSV upload is the primary data import method now

# New callback for CSV file metadata extraction
@callback(
    [
        Output("individuals-dropdown", "options", allow_duplicate=True),
        Output("start-date-picker", "date"),
        Output("end-date-picker", "date"),
    ],
    Input("store-movement-data", "data"),
    prevent_initial_call=True,
)
def update_csv_metadata(movement_data_json):
    if not movement_data_json:
        return [], None, None
    
    try:
        # Parse the movement data
        movement_data = pd.read_json(movement_data_json, orient='split')
        
        if movement_data.empty:
            return [], None, None
        
        # Extract unique individuals
        unique_individuals = movement_data['individual_id'].unique()
        individual_options = [
            {"label": f"{ind}", "value": ind} 
            for ind in unique_individuals
        ]
        
        # Get time range
        try:
            # Ensure timestamp is datetime
            if movement_data['timestamp'].dtype == 'object':
                movement_data['timestamp'] = pd.to_datetime(movement_data['timestamp'])
                
            min_date = movement_data['timestamp'].min().strftime('%Y-%m-%d')
            max_date = movement_data['timestamp'].max().strftime('%Y-%m-%d')
        except Exception as e:
            min_date = None
            max_date = None
        
        # Create data summary
        summary = dbc.Card([
            dbc.CardBody([
                html.H5("CSV Data Summary"),
                html.P([
                    html.Strong("Records: "),
                    f"{len(movement_data):,} GPS points"
                ]),
                html.P([
                    html.Strong("Individuals: "),
                    f"{len(unique_individuals)} tracked animals"
                ]),
                html.P([
                    html.Strong("Time range: "),
                    f"{min_date or 'Unknown'} to {max_date or 'Unknown'}"
                ]) if min_date or max_date else None,
                html.P([
                    html.Strong("Columns available: "),
                    ", ".join(movement_data.columns.tolist())
                ])
            ])
        ])
        
        return individual_options, min_date, max_date, summary
    
    except Exception as e:
        print(f"Error processing CSV data: {str(e)}")
        return [], None, None, html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error processing CSV data: {str(e)}"
        ], className="text-danger")

# Callback to update filters store
@callback(
    Output("store-filters", "data"),
    [
        Input("study-id-store", "data"),
        Input("individuals-dropdown", "value"),
        Input("date-filter", "start_date"),
        Input("date-filter", "end_date"),
    ],
    prevent_initial_call=True,
)
def update_filters_store(study_id, selected_individuals, start_date, end_date):
    # Convert to list if it's a single value
    if selected_individuals and not isinstance(selected_individuals, list):
        selected_individuals = [selected_individuals]
    
    filters = {
        "study_id": study_id,
        "individuals": selected_individuals,
        "start_date": start_date,
        "end_date": end_date,
    }
    
    return filters

# Callback to calculate daily distance and update store
@callback(
    Output("store-daily-distance", "data"),
    Input("store-movement-data", "data"),
    prevent_initial_call=True,
)
def process_daily_distance(movement_data_json):
    if not movement_data_json:
        return None
    
    try:
        # Convert JSON to DataFrame
        movement_data = pd.read_json(movement_data_json, orient='split')
        
        # Calculate daily distance for each individual
        daily_distance = calculate_daily_distance(movement_data)
        
        # Store the results
        if daily_distance is not None and not daily_distance.empty:
            return daily_distance.to_json(date_format='iso', orient='split')
        else:
            return None
    except Exception:
        return None

# Callback to calculate home range and update store
@callback(
    Output("store-home-range", "data", allow_duplicate=True),
    Input("store-movement-data", "data"),
    prevent_initial_call=True,
)
def process_home_range(movement_data_json):
    if not movement_data_json:
        return None
    
    try:
        # Convert JSON to DataFrame
        movement_data = pd.read_json(movement_data_json, orient='split')
        
        # Calculate home range (MCP and KDE) for each individual
        home_range_data = calculate_home_range(movement_data)
        
        # Store the results as a dictionary with both MCP and KDE results
        if home_range_data:
            return json.dumps(home_range_data)
        else:
            return None
    except Exception:
        return None

# Callback to calculate activity patterns and update store
@callback(
    Output("store-activity", "data", allow_duplicate=True),
    Input("store-movement-data", "data"),
    prevent_initial_call=True,
)
def process_activity_patterns(movement_data_json):
    if not movement_data_json:
        return None
    
    try:
        # Convert JSON to DataFrame
        movement_data = pd.read_json(movement_data_json, orient='split')
        
        # Calculate activity patterns for each individual
        activity_data = calculate_activity_patterns(movement_data)
        
        # Store the results
        if activity_data is not None and not activity_data.empty:
            return activity_data.to_json(date_format='iso', orient='split')
        else:
            return None
    except Exception:
        return None

# Callback to calculate speed metrics and update store
@callback(
    Output("store-speed", "data"),
    Input("store-movement-data", "data"),
    prevent_initial_call=True,
)
def process_speed_metrics(movement_data_json):
    if not movement_data_json:
        return None
    
    try:
        # Convert JSON to DataFrame
        movement_data = pd.read_json(movement_data_json, orient='split')
        
        # Calculate speed metrics for each individual
        speed_data = calculate_speed_metrics(movement_data)
        
        # Store the results
        if speed_data is not None and not speed_data.empty:
            return speed_data.to_json(date_format='iso', orient='split')
        else:
            return None
    except Exception:
        return None

# Callback to calculate data quality metrics and update store
@callback(
    Output("store-quality", "data"),
    Input("store-movement-data", "data"),
    prevent_initial_call=True,
)
def process_data_quality(movement_data_json):
    if not movement_data_json:
        return None
    
    try:
        # Convert JSON to DataFrame
        movement_data = pd.read_json(movement_data_json, orient='split')
        
        # Calculate fix success rate and data gaps for each individual
        quality_data = calculate_fix_success(movement_data)
        
        # Store the results
        if quality_data is not None and not quality_data.empty:
            return quality_data.to_json(date_format='iso', orient='split')
        else:
            return None
    except Exception:
        return None

# Dashboard KPI Cards Callbacks
@callback(
    [
        Output("total-distance-kpi", "children"),
        Output("avg-daily-distance-kpi", "children"),
        Output("avg-speed-kpi", "children"),
        Output("time-active-kpi", "children"),
        Output("gps-fix-rate-kpi", "children"),
        Output("home-range-kpi", "children"),
    ],
    [
        Input("store-movement-data", "data"),
        Input("store-daily-distance", "data"),
        Input("store-speed", "data"),
        Input("store-activity", "data"),
        Input("store-quality", "data"),
        Input("store-home-range", "data"),
    ],
    prevent_initial_call=True,
)
def update_dashboard_kpis(movement_data_json, daily_distance_json, speed_json, activity_json, quality_json, home_range_json):
    # Default values
    total_distance = "--"
    avg_daily = "--"
    avg_speed = "--"
    time_active = "--"
    fix_rate = "--"
    home_range = "--"
    
    # Update metrics if data is available
    if daily_distance_json:
        try:
            daily_df = pd.read_json(daily_distance_json, orient='split')
            total_distance = f"{daily_df['distance'].sum():.1f} km"
            avg_daily = f"{daily_df['distance'].mean():.1f} km/day"
        except Exception:
            pass
    
    if speed_json:
        try:
            speed_df = pd.read_json(speed_json, orient='split')
            avg_speed = f"{speed_df['speed_kmh'].mean():.1f} km/h"
        except Exception:
            pass
    
    if activity_json:
        try:
            activity_df = pd.read_json(activity_json, orient='split')
            if 'activity_ratio' in activity_df.columns:
                time_active = f"{activity_df['activity_ratio'].mean() * 100:.1f}%"
        except Exception:
            pass
    
    if quality_json:
        try:
            quality_df = pd.read_json(quality_json, orient='split')
            if 'fix_success_rate' in quality_df.columns:
                fix_rate = f"{quality_df['fix_success_rate'].mean():.1f}%"
        except Exception:
            pass
    
    if home_range_json:
        try:
            home_range_data = json.loads(home_range_json)
            # Get MCP 95% area from first animal as an example
            if 'mcp' in home_range_data:
                area = home_range_data['mcp'].get('area_95', 0)
                home_range = f"{area:.1f} km²"
        except Exception:
            pass
    
    return total_distance, avg_daily, avg_speed, time_active, fix_rate, home_range

# Dashboard Main Chart Callback
@callback(
    Output("dashboard-main-chart", "figure"),
    [
        Input("store-daily-distance", "data"),
        Input("dashboard-chart-type", "value"),
    ],
    prevent_initial_call=True,
)
def update_dashboard_main_chart(daily_distance_json, chart_type):
    # Default empty figure
    fig = go.Figure()
    fig.update_layout(
        title="No data available",
        xaxis_title="Date",
        yaxis_title="Value",
        template="plotly_white",
        height=350,
    )
    
    if not daily_distance_json or not chart_type:
        return fig
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(daily_distance_json, orient='split')
        
        # Ensure timestamp is datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        elif 'date' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'])
        
        # Prepare data based on chart type
        if chart_type == "daily_distance":
            title = "Daily Distance Traveled"
            y_axis = "distance"
            y_title = "Distance (km)"
            color_sequence = px.colors.qualitative.Safe
            
            fig = px.line(
                df,
                x="timestamp",
                y=y_axis,
                color="individual_id" if "individual_id" in df.columns else None,
                title=title,
                labels={"timestamp": "Date", y_axis: y_title},
                template="plotly_white",
                color_discrete_sequence=color_sequence
            )
            
        elif chart_type == "cumulative_distance":
            # Calculate cumulative distance for each individual
            if "individual_id" in df.columns:
                df_cumulative = df.sort_values(["individual_id", "timestamp"])
                df_cumulative["cum_distance"] = df_cumulative.groupby("individual_id")["distance"].cumsum()
            else:
                df_cumulative = df.sort_values("timestamp")
                df_cumulative["cum_distance"] = df_cumulative["distance"].cumsum()
            
            title = "Cumulative Distance Traveled"
            y_title = "Cumulative Distance (km)"
            color_sequence = px.colors.qualitative.Bold
            
            fig = px.line(
                df_cumulative,
                x="timestamp",
                y="cum_distance",
                color="individual_id" if "individual_id" in df_cumulative.columns else None,
                title=title,
                labels={"timestamp": "Date", "cum_distance": y_title},
                template="plotly_white",
                color_discrete_sequence=color_sequence
            )
            
        elif chart_type == "speed_distribution":
            # Use the speed data if available
            if "speed_kmh" in df.columns:
                title = "Speed Distribution"
                y_axis = "speed_kmh"
                y_title = "Speed (km/h)"
                
                fig = px.box(
                    df,
                    x="individual_id" if "individual_id" in df.columns else None,
                    y=y_axis,
                    color="individual_id" if "individual_id" in df.columns else None,
                    title=title,
                    labels={"individual_id": "Individual", y_axis: y_title},
                    template="plotly_white",
                )
        
        # Update layout for better appearance
        fig.update_layout(
            height=350,
            margin={"l": 40, "r": 40, "t": 40, "b": 40},
            legend_title_text="Individual",
            hovermode="closest"
        )
        
        return fig
    except Exception as e:
        # Return default figure with error information
        fig.update_layout(title=f"Error loading data: {str(e)}")
        return fig

# Dashboard Map Preview Callback
@callback(
    Output("dashboard-map-preview", "figure"),
    Input("store-movement-data", "data"),
    prevent_initial_call=True,
)
def update_dashboard_map(movement_data_json):
    # Default empty figure
    fig = go.Figure()
    fig.update_layout(
        title="No GPS data available",
        template="plotly_white",
        height=350,
    )
    
    if not movement_data_json:
        return fig
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(movement_data_json, orient='split')
        
        # Check if required columns exist
        if 'location_lat' not in df.columns or 'location_long' not in df.columns:
            fig.update_layout(title="Missing GPS coordinates in data")
            return fig
        
        # Create map figure
        if 'individual_id' in df.columns:
            # Create a scatter mapbox with points colored by individual
            fig = px.scatter_mapbox(
                df, 
                lat='location_lat', 
                lon='location_long',
                color='individual_id',
                hover_name='individual_id',
                zoom=10,
                height=350,
                mapbox_style='carto-positron',
            )
        else:
            # Single individual
            fig = px.scatter_mapbox(
                df, 
                lat='location_lat', 
                lon='location_long',
                zoom=10,
                height=350,
                mapbox_style='carto-positron',
            )
        
        # Update layout
        fig.update_layout(
            margin={"l": 0, "r": 0, "t": 30, "b": 0},
            title="GPS Tracks Preview",
            mapbox={
                'center': {
                    'lat': df['location_lat'].mean(),
                    'lon': df['location_long'].mean()
                },
                'style': "carto-positron"
            }
        )
        
        return fig
    except Exception as e:
        # Return default figure with error information
        fig.update_layout(title=f"Error loading map data: {str(e)}")
        return fig

# Dashboard Activity Chart Callback
@callback(
    Output("dashboard-activity-chart", "figure"),
    Input("store-activity", "data"),
    prevent_initial_call=True,
)
def update_dashboard_activity(activity_json):
    # Default empty figure
    fig = go.Figure()
    fig.update_layout(
        title="No activity data available",
        template="plotly_white",
        height=250,
    )
    
    if not activity_json:
        return fig
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(activity_json, orient='split')
        
        # Check if the dataframe has required columns
        if 'hour_of_day' in df.columns and 'activity' in df.columns:
            # Create hourly activity pattern chart
            if 'individual_id' in df.columns:
                # Group by hour and individual, calculate mean activity
                hourly_activity = df.groupby(['hour_of_day', 'individual_id'])['activity'].mean().reset_index()
                
                fig = px.line(
                    hourly_activity,
                    x='hour_of_day',
                    y='activity',
                    color='individual_id',
                    title="Daily Activity Patterns",
                    labels={'hour_of_day': 'Hour of Day', 'activity': 'Activity Level'},
                    template="plotly_white",
                )
            else:
                # Group by hour, calculate mean activity
                hourly_activity = df.groupby('hour_of_day')['activity'].mean().reset_index()
                
                fig = px.line(
                    hourly_activity,
                    x='hour_of_day',
                    y='activity',
                    title="Daily Activity Patterns",
                    labels={'hour_of_day': 'Hour of Day', 'activity': 'Activity Level'},
                    template="plotly_white",
                )
                
            # Update layout
            fig.update_layout(
                height=250,
                margin={"l": 40, "r": 40, "t": 40, "b": 40},
                xaxis={
                    'tickmode': 'array',
                    'tickvals': list(range(0, 24, 3)),
                    'ticktext': ['12 AM', '3 AM', '6 AM', '9 AM', '12 PM', '3 PM', '6 PM', '9 PM']
                }
            )
        
        return fig
    except Exception as e:
        # Return default figure with error information
        fig.update_layout(title=f"Error loading activity data: {str(e)}")
        return fig

# Help page navigation callbacks
@callback(
    [Output("getting-started-section", "style"),
     Output("data-import-section", "style"),
     Output("map-visualizations-section", "style"),
     Output("movement-analysis-section", "style"),
     Output("home-range-section", "style"),
     Output("behavioral-section", "style"),
     Output("environmental-section", "style"),
     Output("data-quality-section", "style"),
     Output("faqs-section", "style"),
     Output("about-section", "style"),
     Output("getting-started-link", "active"),
     Output("data-import-link", "active"),
     Output("map-link", "active"),
     Output("movement-link", "active"),
     Output("home-range-link", "active"),
     Output("behavioral-link", "active"),
     Output("environmental-link", "active"),
     Output("quality-link", "active"),
     Output("faqs-link", "active"),
     Output("about-link", "active")],
    [Input("getting-started-link", "n_clicks"),
     Input("data-import-link", "n_clicks"),
     Input("map-link", "n_clicks"),
     Input("movement-link", "n_clicks"),
     Input("home-range-link", "n_clicks"),
     Input("behavioral-link", "n_clicks"),
     Input("environmental-link", "n_clicks"),
     Input("quality-link", "n_clicks"),
     Input("faqs-link", "n_clicks"),
     Input("about-link", "n_clicks")],
    prevent_initial_call=True
)
def display_help_section(n1, n2, n3, n4, n5, n6, n7, n8, n9, n10):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Default to getting started
        section_id = "getting-started-link"
    else:
        section_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Set all sections to hidden
    sections_style = [{"display": "none"} for _ in range(10)]
    active_states = [False for _ in range(10)]
    
    # Set the active section based on clicked link
    section_index = {
        "getting-started-link": 0,
        "data-import-link": 1,
        "map-link": 2,
        "movement-link": 3,
        "home-range-link": 4,
        "behavioral-link": 5,
        "environmental-link": 6,
        "quality-link": 7,
        "faqs-link": 8,
        "about-link": 9
    }.get(section_id, 0)
    
    sections_style[section_index] = {"display": "block"}
    active_states[section_index] = True
    
    return tuple(sections_style + active_states)

# Map Visualization Callbacks
@callback(
    Output("map-visualization", "figure"),
    [
        Input("store-movement-data", "data"),
        Input("map-visualization-type", "value"),
        Input("map-style", "value"),
        Input("map-time-slider", "value"),
        Input("map-filter-individuals", "value"),
        Input("map-show-trajectory", "value"),
    ],
    prevent_initial_call=True,
)
def update_map_visualization(
    movement_data_json, map_type, map_style, time_range, selected_individuals, show_trajectory
):
    # Default empty figure
    fig = go.Figure()
    fig.update_layout(
        title="No GPS data available",
        template="plotly_white",
        height=700,
    )
    
    if not movement_data_json:
        return fig
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(movement_data_json, orient='split')
        
        # Check if required columns exist
        if 'location_lat' not in df.columns or 'location_long' not in df.columns:
            fig.update_layout(title="Missing GPS coordinates in data")
            return fig
            
        # Ensure timestamp is datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Apply time range filter if provided
        if time_range and len(time_range) == 2 and 'timestamp' in df.columns:
            # Convert time range from slider value (days) to timestamps
            start_date = df['timestamp'].min() + pd.Timedelta(days=time_range[0])
            end_date = df['timestamp'].min() + pd.Timedelta(days=time_range[1])
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
        
        # Apply individual filter if provided
        if selected_individuals and 'individual_id' in df.columns:
            df = df[df['individual_id'].isin(selected_individuals)]
        
        if len(df) == 0:
            fig.update_layout(title="No data available for the selected filters")
            return fig
        
        # Set map style
        mapbox_style = "carto-positron"  # default
        if map_style == "satellite":
            mapbox_style = "satellite"
        elif map_style == "terrain":
            mapbox_style = "stamen-terrain"
        elif map_style == "dark":
            mapbox_style = "carto-darkmatter"
        
        # Create appropriate map based on the map_type
        if map_type == "points":
            # Create scatter mapbox with individual points
            if 'individual_id' in df.columns:
                fig = px.scatter_mapbox(
                    df, 
                    lat='location_lat', 
                    lon='location_long',
                    color='individual_id',
                    hover_name='individual_id',
                    hover_data=['timestamp', 'location_lat', 'location_long'],
                    zoom=9,
                    height=700,
                    opacity=0.7,
                    size_max=10,
                )
            else:
                fig = px.scatter_mapbox(
                    df, 
                    lat='location_lat', 
                    lon='location_long',
                    hover_data=['timestamp', 'location_lat', 'location_long'],
                    zoom=9,
                    height=700,
                    opacity=0.7,
                )
                
        elif map_type == "heatmap":
            # Create density heatmap
            fig = px.density_mapbox(
                df,
                lat='location_lat',
                lon='location_long',
                z='location_lat',  # Just needed for the density calculation
                radius=10,
                zoom=9,
                height=700,
                opacity=0.7,
                color_continuous_scale='Viridis',
            )
            
            # Customize heatmap
            fig.update_layout(
                coloraxis_showscale=False  # Hide the color scale
            )
        
        # Add trajectory lines if requested
        if show_trajectory and len(show_trajectory) > 0 and 'individual_id' in df.columns:
            if 'trajectory' in show_trajectory:
                # Sort by timestamp to ensure correct line connection
                if 'individual_id' in df.columns:
                    for individual in df['individual_id'].unique():
                        individual_df = df[df['individual_id'] == individual].sort_values('timestamp')
                        fig.add_trace(
                            go.Scattermapbox(
                                lat=individual_df['location_lat'],
                                lon=individual_df['location_long'],
                                mode='lines',
                                line=dict(width=2),
                                opacity=0.6,
                                name=f"{individual} Path",
                                showlegend=True
                            )
                        )
                else:
                    # Single individual case
                    df_sorted = df.sort_values('timestamp')
                    fig.add_trace(
                        go.Scattermapbox(
                            lat=df_sorted['location_lat'],
                            lon=df_sorted['location_long'],
                            mode='lines',
                            line=dict(width=2),
                            opacity=0.6,
                            name="Path",
                            showlegend=True
                        )
                    )
        
        # Update layout
        fig.update_layout(
            margin={"l": 0, "r": 0, "t": 30, "b": 0},
            title="GPS Tracking Map",
            mapbox={
                'style': mapbox_style,
                'center': {
                    'lat': df['location_lat'].mean(),
                    'lon': df['location_long'].mean()
                },
                'zoom': 9
            },
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)"
            )
        )
        
        return fig
    except Exception as e:
        # Return default figure with error information
        fig.update_layout(title=f"Error loading map data: {str(e)}")
        return fig

# Callback for map statistics panel
@callback(
    [
        Output("map-stats-total-points", "children"),
        Output("map-stats-individuals", "children"),
        Output("map-stats-time-period", "children"),
        Output("map-stats-bounds", "children"),
    ],
    [
        Input("store-movement-data", "data"),
        Input("map-time-slider", "value"),
        Input("map-filter-individuals", "value"),
    ],
    prevent_initial_call=True,
)
def update_map_stats(movement_data_json, time_range, selected_individuals):
    # Default values
    total_points = "--"
    individuals = "--"
    time_period = "--"
    bounds = "--"
    
    if not movement_data_json:
        return total_points, individuals, time_period, bounds
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(movement_data_json, orient='split')
        
        # Apply filters if needed
        if time_range and len(time_range) == 2 and 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start_date = df['timestamp'].min() + pd.Timedelta(days=time_range[0])
            end_date = df['timestamp'].min() + pd.Timedelta(days=time_range[1])
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
        
        if selected_individuals and 'individual_id' in df.columns:
            df = df[df['individual_id'].isin(selected_individuals)]
        
        # Calculate stats
        total_points = f"{len(df):,}"
        
        if 'individual_id' in df.columns:
            individuals = f"{df['individual_id'].nunique()}"
        
        if 'timestamp' in df.columns:
            min_date = df['timestamp'].min().strftime('%Y-%m-%d')
            max_date = df['timestamp'].max().strftime('%Y-%m-%d')
            time_period = f"{min_date} to {max_date}"
        
        if 'location_lat' in df.columns and 'location_long' in df.columns:
            lat_min = df['location_lat'].min()
            lat_max = df['location_lat'].max()
            lon_min = df['location_long'].min()
            lon_max = df['location_long'].max()
            bounds = f"Lat: {lat_min:.4f} to {lat_max:.4f}, Lon: {lon_min:.4f} to {lon_max:.4f}"
        
        return total_points, individuals, time_period, bounds
    except Exception:
        return total_points, individuals, time_period, bounds

# Generate map time slider marks
@callback(
    [
        Output("map-time-slider", "marks"),
        Output("map-time-slider", "min"),
        Output("map-time-slider", "max"),
        Output("map-time-slider", "value"),
    ],
    Input("store-movement-data", "data"),
    prevent_initial_call=True,
)
def update_time_slider(movement_data_json):
    if not movement_data_json:
        return {}, 0, 1, [0, 1]
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(movement_data_json, orient='split')
        
        if 'timestamp' not in df.columns:
            return {}, 0, 1, [0, 1]
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate days from the first date
        start_date = df['timestamp'].min()
        df['days_from_start'] = (df['timestamp'] - start_date).dt.days
        
        max_days = df['days_from_start'].max()
        
        # Create slider marks at reasonable intervals
        if max_days <= 0:
            return {}, 0, 1, [0, 1]  # Default if all data is on the same day
            
        step = max(1, max_days // 10)  # Create about 10 marks
        marks = {}
        
        for day in range(0, max_days + 1, step):
            date_str = (start_date + pd.Timedelta(days=day)).strftime('%Y-%m-%d')
            marks[day] = {'label': date_str, 'style': {'writing-mode': 'vertical-lr'}}
        
        # Add last day if not included
        if max_days % step != 0:
            date_str = (start_date + pd.Timedelta(days=max_days)).strftime('%Y-%m-%d')
            marks[max_days] = {'label': date_str, 'style': {'writing-mode': 'vertical-lr'}}
        
        return marks, 0, max_days, [0, max_days]
    except Exception:
        return {}, 0, 1, [0, 1]

# Populate map filter dropdown with available individuals
@callback(
    [
        Output("map-filter-individuals", "options"),
        Output("map-filter-individuals", "value"),
    ],
    Input("store-movement-data", "data"),
    prevent_initial_call=True,
)
def update_map_filter_options(movement_data_json):
    if not movement_data_json:
        return [], []
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(movement_data_json, orient='split')
        
        if 'individual_id' not in df.columns:
            return [], []
        
        # Get unique individuals
        individuals = df['individual_id'].unique().tolist()
        options = [{'label': ind, 'value': ind} for ind in individuals]
        
        return options, individuals  # Select all individuals by default
    except Exception:
        return [], []

# Home Range Analysis Callbacks
@callback(
    Output("store-home-range", "data"),
    [
        Input("store-movement-data", "data"),
        Input("home-range-method", "value"),
        Input("home-range-percent", "value"),
        Input("home-range-grid", "value"),
        Input("home-range-smoothing", "value"),
        Input("home-range-individuals", "value"),
    ],
    prevent_initial_call=True,
)
def calculate_home_range(movement_data_json, method, percent_levels, grid_size, smoothing_factor, selected_individuals):
    if not movement_data_json:
        return json.dumps({})
    
    # Default values if not provided
    if not method:
        method = "mcp"  # Minimum Convex Polygon as default
    if not percent_levels:
        percent_levels = [50, 95]  # Default contour levels
    if not grid_size:
        grid_size = 100  # Default grid size
    if not smoothing_factor:
        smoothing_factor = 1.0  # Default smoothing
        
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(movement_data_json, orient='split')
        
        # Check if required columns exist
        if 'location_lat' not in df.columns or 'location_long' not in df.columns:
            return json.dumps({})
        
        # Apply individual filter if provided
        if selected_individuals and 'individual_id' in df.columns:
            df = df[df['individual_id'].isin(selected_individuals)]
        
        # Initialize result dictionary
        result = {}
        
        # Calculate home range based on method
        if method == "mcp":
            result["mcp"] = calculate_mcp_home_range(df, percent_levels)
        elif method == "kde":
            result["kde"] = calculate_kde_home_range(df, percent_levels, grid_size, smoothing_factor)
        elif method == "bbmm":
            result["bbmm"] = calculate_bbmm_home_range(df, percent_levels, grid_size)
        elif method == "locoht":
            result["locoht"] = calculate_locoht_home_range(df, percent_levels)
        
        return json.dumps(result)
    except Exception as e:
        print(f"Error calculating home range: {str(e)}")
        return json.dumps({"error": str(e)})

# MCP Home Range Calculation
def calculate_mcp_home_range(df, percent_levels):
    result = {}
    
    # Check if we have multiple individuals
    if 'individual_id' in df.columns:
        # Calculate for each individual
        for individual in df['individual_id'].unique():
            ind_df = df[df['individual_id'] == individual]
            ind_result = calculate_single_mcp(ind_df, percent_levels)
            result[individual] = ind_result
    else:
        # Calculate for the single dataset
        result = calculate_single_mcp(df, percent_levels)
    
    return result

def calculate_single_mcp(df, percent_levels):
    result = {}
    
    # Create a list of points for shapely
    points = [Point(lon, lat) for lon, lat in zip(df['location_long'], df['location_lat'])]
    
    # Calculate MultiPoint and convex hull
    multi_point = MultiPoint(points)
    
    # Calculate full MCP (100%)
    hull = multi_point.convex_hull
    
    # Calculate area in square kilometers (approximate)
    # This is an approximation assuming a flat surface
    area_100 = calculate_area_km2(hull, df['location_lat'].mean())
    result["area_100"] = area_100
    result["hull_100"] = hull_to_geojson(hull)
    
    # Calculate MCPs for specified percent levels
    for percent in percent_levels:
        if percent == 100:
            continue  # Already calculated
            
        # Randomly sample points
        n_points = len(points)
        sample_size = int(n_points * (percent / 100))
        
        if sample_size >= 3:  # Need at least 3 points for a polygon
            # Sample points
            random_indices = np.random.choice(range(n_points), sample_size, replace=False)
            sampled_points = [points[i] for i in random_indices]
            sampled_multi_point = MultiPoint(sampled_points)
            sampled_hull = sampled_multi_point.convex_hull
            
            # Calculate area
            area = calculate_area_km2(sampled_hull, df['location_lat'].mean())
            result[f"area_{percent}"] = area
            result[f"hull_{percent}"] = hull_to_geojson(sampled_hull)
    
    return result

# KDE Home Range Calculation
def calculate_kde_home_range(df, percent_levels, grid_size, smoothing_factor):
    result = {}
    
    # Check if we have multiple individuals
    if 'individual_id' in df.columns:
        # Calculate for each individual
        for individual in df['individual_id'].unique():
            ind_df = df[df['individual_id'] == individual]
            ind_result = calculate_single_kde(ind_df, percent_levels, grid_size, smoothing_factor)
            result[individual] = ind_result
    else:
        # Calculate for the single dataset
        result = calculate_single_kde(df, percent_levels, grid_size, smoothing_factor)
    
    return result

def calculate_single_kde(df, percent_levels, grid_size, smoothing_factor):
    result = {}
    
    try:
        # Extract coordinates
        x = df['location_long'].to_numpy()
        y = df['location_lat'].to_numpy()
        
        # Create grid for KDE calculation
        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()
        
        # Add buffer around min/max
        buffer_x = (x_max - x_min) * 0.1
        buffer_y = (y_max - y_min) * 0.1
        
        x_min -= buffer_x
        x_max += buffer_x
        y_min -= buffer_y
        y_max += buffer_y
        
        # Create grid
        x_grid = np.linspace(x_min, x_max, grid_size)
        y_grid = np.linspace(y_min, y_max, grid_size)
        xx, yy = np.meshgrid(x_grid, y_grid)
        
        # Stack coordinates for KDE input
        positions = np.vstack([xx.ravel(), yy.ravel()])
        values = np.vstack([x, y])
        
        # Calculate KDE
        kernel = stats.gaussian_kde(values, bw_method=smoothing_factor)
        kde = np.reshape(kernel(positions).T, xx.shape)
        
        # Find contour levels
        kde_sorted = np.sort(kde.flatten())[::-1]  # Sort in descending order
        cumsum = np.cumsum(kde_sorted)
        cumsum = cumsum / cumsum[-1]  # Normalize
        
        # Store raw KDE data
        result["kde_grid"] = kde.tolist()
        result["x_grid"] = x_grid.tolist()
        result["y_grid"] = y_grid.tolist()
        
        # Calculate contours for each percent level
        for percent in percent_levels:
            # Find the kde value that gives the specified percent level
            idx = np.argmin(np.abs(cumsum - (percent / 100)))
            contour_level = kde_sorted[idx]
            
            # Generate contour
            contours = measure.find_contours(kde, contour_level)
            
            # Convert contours to geographic coordinates
            geo_contours = []
            for contour in contours:
                # Map from grid indices to geographic coordinates
                contour_y = np.interp(contour[:, 0], np.arange(grid_size), y_grid)
                contour_x = np.interp(contour[:, 1], np.arange(grid_size), x_grid)
                geo_contours.append(list(zip(contour_x, contour_y)))
            
            # Convert to polygons and calculate area
            polygons = [Polygon(contour) for contour in geo_contours if len(contour) >= 3]
            if polygons:
                multi_polygon = MultiPolygon(polygons)
                area = calculate_area_km2(multi_polygon, df['location_lat'].mean())
                result[f"area_{percent}"] = area
                result[f"contour_{percent}"] = contour_to_geojson(multi_polygon)
                
    except Exception as e:
        result["error"] = str(e)
    
    return result

# Brownian Bridge Movement Model (BBMM) - Simplified implementation
def calculate_bbmm_home_range(df, percent_levels, grid_size):
    # In a real implementation, this would use a proper BBMM package
    # For this demo, we'll use a simplified approach similar to KDE but with time weighting
    result = {}
    
    # Check if we have multiple individuals
    if 'individual_id' in df.columns:
        # Calculate for each individual
        for individual in df['individual_id'].unique():
            ind_df = df[df['individual_id'] == individual]
            if 'timestamp' in ind_df.columns:
                ind_result = calculate_single_bbmm(ind_df, percent_levels, grid_size)
                result[individual] = ind_result
    else:
        # Calculate for the single dataset
        if 'timestamp' in df.columns:
            result = calculate_single_bbmm(df, percent_levels, grid_size)
    
    return result

def calculate_single_bbmm(df, percent_levels, grid_size):
    # This is a simplified implementation
    result = {}
    
    try:
        # Sort by timestamp
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp')
            
            # Calculate time differences
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / 3600  # In hours
            
            # Replace NaN in first row and cap large gaps
            df['time_diff'].iloc[0] = 0
            df['time_diff'] = df['time_diff'].clip(upper=24)  # Cap at 24 hours
            
            # Use time differences as weights
            weights = 1.0 / (df['time_diff'] + 0.1)  # Add small constant to avoid division by zero
            weights = weights / weights.sum()  # Normalize
            
            # Extract coordinates
            x = df['location_long'].to_numpy()
            y = df['location_lat'].to_numpy()
            
            # Create grid
            x_min, x_max = x.min(), x.max()
            y_min, y_max = y.min(), y.max()
            
            # Add buffer
            buffer_x = (x_max - x_min) * 0.1
            buffer_y = (y_max - y_min) * 0.1
            
            x_min -= buffer_x
            x_max += buffer_x
            y_min -= buffer_y
            y_max += buffer_y
            
            x_grid = np.linspace(x_min, x_max, grid_size)
            y_grid = np.linspace(y_min, y_max, grid_size)
            xx, yy = np.meshgrid(x_grid, y_grid)
            
            # Calculate weighted KDE as a simplified BBMM
            grid_values = np.zeros_like(xx)
            
            for i in range(len(x) - 1):
                # Calculate segment contribution based on time
                weight = weights[i+1]
                
                # Create a density between consecutive points
                segment_density = np.zeros_like(xx)
                
                for j in range(grid_size):
                    for k in range(grid_size):
                        # Distance from grid point to line segment
                        dist = point_to_segment_distance(
                            xx[j, k], yy[j, k],
                            x[i], y[i],
                            x[i+1], y[i+1]
                        )
                        # Apply Gaussian kernel
                        segment_density[j, k] = np.exp(-dist * dist / 0.001) * weight
                
                grid_values += segment_density
            
            # Normalize grid values
            grid_values = grid_values / grid_values.sum()
            
            # Store grid data
            result["bbmm_grid"] = grid_values.tolist()
            result["x_grid"] = x_grid.tolist()
            result["y_grid"] = y_grid.tolist()
            
            # Calculate contours for each percent level
            grid_sorted = np.sort(grid_values.flatten())[::-1]
            cumsum = np.cumsum(grid_sorted)
            cumsum = cumsum / cumsum[-1]  # Normalize
            
            for percent in percent_levels:
                # Find contour level
                idx = np.argmin(np.abs(cumsum - (percent / 100)))
                contour_level = grid_sorted[idx]
                
                # Generate contour
                contours = measure.find_contours(grid_values, contour_level)
                
                # Convert to geographic coordinates
                geo_contours = []
                for contour in contours:
                    contour_y = np.interp(contour[:, 0], np.arange(grid_size), y_grid)
                    contour_x = np.interp(contour[:, 1], np.arange(grid_size), x_grid)
                    geo_contours.append(list(zip(contour_x, contour_y)))
                
                # Convert to polygons and calculate area
                polygons = [Polygon(contour) for contour in geo_contours if len(contour) >= 3]
                if polygons:
                    multi_polygon = MultiPolygon(polygons)
                    area = calculate_area_km2(multi_polygon, df['location_lat'].mean())
                    result[f"area_{percent}"] = area
                    result[f"contour_{percent}"] = contour_to_geojson(multi_polygon)
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

# Calculate T-LoCoH Home Range (simplified implementation)
def calculate_locoht_home_range(df, percent_levels):
    result = {}
    
    # Check if we have multiple individuals
    if 'individual_id' in df.columns:
        # Calculate for each individual
        for individual in df['individual_id'].unique():
            ind_df = df[df['individual_id'] == individual]
            ind_result = calculate_single_locoht(ind_df, percent_levels)
            result[individual] = ind_result
    else:
        # Calculate for the single dataset
        result = calculate_single_locoht(df, percent_levels)
    
    return result

def calculate_single_locoht(df, percent_levels):
    # This is a simplified implementation of T-LoCoH
    result = {}
    
    try:
        # Extract coordinates
        coords = np.column_stack((df['location_long'].values, df['location_lat'].values))
        n_points = len(coords)
        
        if n_points < 5:
            result["error"] = "Not enough points for T-LoCoH analysis"
            return result
        
        # Calculate pairwise distances
        dist_matrix = spatial.distance.cdist(coords, coords, 'euclidean')
        
        # Incorporate time if available
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            times = df['timestamp'].values.astype(np.int64) // 10**9  # Convert to Unix time
            time_matrix = spatial.distance.cdist(times.reshape(-1, 1), times.reshape(-1, 1), 'euclidean')
            # Normalize time matrix
            time_matrix = time_matrix / time_matrix.max() if time_matrix.max() > 0 else time_matrix
            
            # Combine space and time with s parameter = 0.5 (equal weight)
            combined_matrix = dist_matrix + 0.5 * time_matrix
        else:
            combined_matrix = dist_matrix
        
        # Set diagonal to infinity to avoid self-neighbors
        np.fill_diagonal(combined_matrix, np.inf)
        
        # Create local hulls
        k = min(15, n_points - 1)  # Number of nearest neighbors
        hulls = []
        hull_areas = []
        
        for i in range(n_points):
            # Find k nearest neighbors
            neighbors_idx = np.argsort(combined_matrix[i])[:k+1]  # +1 to include self
            neighbor_coords = coords[neighbors_idx]
            
            # Create convex hull
            if len(neighbor_coords) >= 3:
                hull = ConvexHull(neighbor_coords)
                hull_points = neighbor_coords[hull.vertices]
                
                # Calculate hull area (simplified, should be geodesic in full implementation)
                hull_poly = Polygon(hull_points)
                area = calculate_area_km2(hull_poly, df['location_lat'].mean())
                
                hulls.append(hull_poly)
                hull_areas.append(area)
        
        # Sort hulls by area
        sorted_indices = np.argsort(hull_areas)
        sorted_hulls = [hulls[i] for i in sorted_indices]
        
        # Calculate isopleth hulls for different percent levels
        total_area = sum(hull_areas)
        
        for percent in percent_levels:
            # Calculate how many hulls to include
            target_area = total_area * (percent / 100)
            current_area = 0
            included_hulls = []
            
            for i, hull in enumerate(sorted_hulls):
                current_area += hull_areas[sorted_indices[i]]
                included_hulls.append(hull)
                
                if current_area >= target_area:
                    break
            
            # Union of included hulls
            if included_hulls:
                union_poly = unary_union(included_hulls)
                area = calculate_area_km2(union_poly, df['location_lat'].mean())
                result[f"area_{percent}"] = area
                result[f"contour_{percent}"] = contour_to_geojson(union_poly)
    
    except Exception as e:
        result["error"] = str(e)
    
    return result

# Helper function to calculate area in km²
def calculate_area_km2(polygon, mean_latitude):
    # Convert area in degrees to km² (approximate)
    # At the equator, 1° longitude = 111.32 km
    # At latitude L, 1° longitude = 111.32 * cos(L) km
    lat_correction = np.cos(np.radians(mean_latitude))
    area_degrees = polygon.area
    area_km2 = area_degrees * (111.32**2) * lat_correction
    return area_km2

# Helper function to convert shapely polygon to GeoJSON format
def hull_to_geojson(hull):
    if hull.geom_type == 'Polygon':
        exterior_coords = list(hull.exterior.coords)
        return {
            "type": "Polygon",
            "coordinates": [exterior_coords]
        }
    return None

# Helper function to convert contour to GeoJSON
def contour_to_geojson(contour):
    if contour.geom_type == 'Polygon':
        exterior_coords = list(contour.exterior.coords)
        interior_coords = [list(interior.coords) for interior in contour.interiors]
        return {
            "type": "Polygon",
            "coordinates": [exterior_coords] + interior_coords
        }
    elif contour.geom_type == 'MultiPolygon':
        multi_coords = []
        for polygon in contour.geoms:
            exterior_coords = list(polygon.exterior.coords)
            interior_coords = [list(interior.coords) for interior in polygon.interiors]
            multi_coords.append([exterior_coords] + interior_coords)
        return {
            "type": "MultiPolygon",
            "coordinates": multi_coords
        }
    return None

# Helper function for BBMM calculation
def point_to_segment_distance(px, py, x1, y1, x2, y2):
    # Calculate the distance from point (px, py) to line segment (x1,y1)-(x2,y2)
    line_length_sq = (x2 - x1)**2 + (y2 - y1)**2
    
    if line_length_sq == 0:
        # Points are the same
        return np.sqrt((px - x1)**2 + (py - y1)**2)
    
    # Calculate projection
    t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq
    
    if t < 0:
        # Beyond point 1
        return np.sqrt((px - x1)**2 + (py - y1)**2)
    elif t > 1:
        # Beyond point 2
        return np.sqrt((px - x2)**2 + (py - y2)**2)
    else:
        # On the segment
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        return np.sqrt((px - proj_x)**2 + (py - proj_y)**2)

# Behavioral Patterns Analysis Callbacks
@callback(
    Output("store-activity", "data"),
    [
        Input("store-movement-data", "data"),
        Input("behavioral-activity-threshold", "value"),
        Input("behavioral-time-window", "value"),
        Input("behavioral-individuals", "value"),
    ],
    prevent_initial_call=True,
)
def calculate_activity_patterns(movement_data_json, activity_threshold, time_window, selected_individuals):
    if not movement_data_json:
        return json.dumps({})
    
    # Default values if not provided
    if not activity_threshold:
        activity_threshold = 0.05  # Default distance threshold in km
    if not time_window:
        time_window = 60  # Default time window in minutes
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(movement_data_json, orient='split')
        
        # Check if required columns exist
        if 'location_lat' not in df.columns or 'location_long' not in df.columns or 'timestamp' not in df.columns:
            return json.dumps({})
        
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Apply individual filter if provided
        if selected_individuals and 'individual_id' in df.columns:
            df = df[df['individual_id'].isin(selected_individuals)]
        
        # Calculate activity patterns
        result_df = calculate_activity_metrics(df, activity_threshold, time_window)
        
        # Return as JSON
        return result_df.to_json(orient='split', date_format='iso')
    
    except Exception as e:
        print(f"Error calculating activity patterns: {str(e)}")
        return json.dumps({})

# Calculate activity metrics
def calculate_activity_metrics(df, activity_threshold, time_window):
    # Sort by individual (if present) and timestamp
    if 'individual_id' in df.columns:
        df = df.sort_values(['individual_id', 'timestamp'])
    else:
        df = df.sort_values('timestamp')
    
    # Initialize result DataFrame
    result_df = pd.DataFrame()
    
    # Process each individual separately if individual_id exists
    if 'individual_id' in df.columns:
        for individual in df['individual_id'].unique():
            ind_df = df[df['individual_id'] == individual]
            ind_result = calculate_single_activity(ind_df, activity_threshold, time_window)
            ind_result['individual_id'] = individual
            result_df = pd.concat([result_df, ind_result])
    else:
        result_df = calculate_single_activity(df, activity_threshold, time_window)
    
    return result_df

def calculate_single_activity(df, activity_threshold, time_window):
    # Calculate step distances
    df['next_lat'] = df['location_lat'].shift(-1)
    df['next_long'] = df['location_long'].shift(-1)
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / 60  # in minutes
    
    # Calculate haversine distance
    df['distance'] = np.nan
    for i in range(len(df) - 1):
        df.loc[df.index[i], 'distance'] = haversine_distance(
            df.loc[df.index[i], 'location_lat'],
            df.loc[df.index[i], 'location_long'],
            df.loc[df.index[i+1], 'location_lat'],
            df.loc[df.index[i+1], 'location_long']
        )
    
    # Calculate speed in km/h
    df['speed_kmh'] = df['distance'] / (df['time_diff'] / 60)
    
    # Set NaN or inf values to 0
    df['speed_kmh'] = df['speed_kmh'].replace([np.nan, np.inf, -np.inf], 0)
    
    # Determine if active based on distance threshold and time window
    df['is_active'] = (df['distance'] > activity_threshold) & (df['time_diff'] <= time_window)
    
    # Extract hour of day and add day/night flag
    df['hour_of_day'] = df['timestamp'].dt.hour
    df['is_daytime'] = ((df['hour_of_day'] >= 6) & (df['hour_of_day'] < 18))
    
    # Aggregate by hour of day
    hourly_activity = df.groupby('hour_of_day').agg(
        activity_count=('is_active', 'sum'),
        total_count=('is_active', 'count'),
        avg_speed=('speed_kmh', 'mean')
    ).reset_index()
    
    hourly_activity['activity_ratio'] = hourly_activity['activity_count'] / hourly_activity['total_count']
    hourly_activity['activity'] = hourly_activity['activity_ratio'] * 100  # as percentage
    
    # Add day/night flag
    hourly_activity['is_daytime'] = ((hourly_activity['hour_of_day'] >= 6) & (hourly_activity['hour_of_day'] < 18))
    
    return hourly_activity

# Haversine distance calculation (in km)
def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of Earth in km
    
    return c * r

# Callback for daily activity rhythm chart
@callback(
    Output("behavioral-daily-rhythm-chart", "figure"),
    [
        Input("store-activity", "data"),
        Input("behavioral-rhythm-chart-type", "value"),
    ],
    prevent_initial_call=True,
)
def update_daily_rhythm_chart(activity_json, chart_type):
    # Default empty figure
    fig = go.Figure()
    fig.update_layout(
        title="No activity data available",
        template="plotly_white",
        height=400,
    )
    
    if not activity_json or not chart_type:
        return fig
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(activity_json, orient='split')
        
        # Create appropriate chart based on type
        if chart_type == "activity_line":
            # Activity line chart
            if 'individual_id' in df.columns:
                fig = px.line(
                    df,
                    x="hour_of_day",
                    y="activity",
                    color="individual_id",
                    title="Daily Activity Rhythm",
                    labels={"hour_of_day": "Hour of Day", "activity": "Activity (%)"}
                )
            else:
                fig = px.line(
                    df,
                    x="hour_of_day",
                    y="activity",
                    title="Daily Activity Rhythm",
                    labels={"hour_of_day": "Hour of Day", "activity": "Activity (%)"}
                )
                
        elif chart_type == "speed_line":
            # Speed line chart
            if 'individual_id' in df.columns:
                fig = px.line(
                    df,
                    x="hour_of_day",
                    y="avg_speed",
                    color="individual_id",
                    title="Hourly Average Speed",
                    labels={"hour_of_day": "Hour of Day", "avg_speed": "Speed (km/h)"}
                )
            else:
                fig = px.line(
                    df,
                    x="hour_of_day",
                    y="avg_speed",
                    title="Hourly Average Speed",
                    labels={"hour_of_day": "Hour of Day", "avg_speed": "Speed (km/h)"}
                )
                
        elif chart_type == "day_night_comparison":
            # Day/Night activity comparison
            day_night_df = df.groupby('is_daytime').agg(
                activity=('activity', 'mean'),
                speed=('avg_speed', 'mean')
            ).reset_index()
            
            day_night_df['period'] = day_night_df['is_daytime'].map({True: 'Day (6am-6pm)', False: 'Night (6pm-6am)'})
            
            fig = px.bar(
                day_night_df,
                x="period",
                y="activity",
                color="period",
                title="Day vs Night Activity",
                labels={"period": "Time Period", "activity": "Activity (%)"}
            )
        
        # Update layout for all chart types
        fig.update_layout(
            height=400,
            template="plotly_white",
            margin={"l": 40, "r": 40, "t": 40, "b": 40}
        )
        
        # For line charts, update x-axis
        if chart_type in ["activity_line", "speed_line"]:
            fig.update_xaxes(
                tickmode='array',
                tickvals=list(range(0, 24, 3)),
                ticktext=['12 AM', '3 AM', '6 AM', '9 AM', '12 PM', '3 PM', '6 PM', '9 PM']
            )
        
        return fig
    
    except Exception as e:
        # Return default figure with error information
        fig.update_layout(title=f"Error loading activity data: {str(e)}")
        return fig

# Callback for active/resting time donut chart
@callback(
    Output("behavioral-active-resting-chart", "figure"),
    Input("store-activity", "data"),
    prevent_initial_call=True,
)
def update_active_resting_chart(activity_json):
    # Default empty figure
    fig = go.Figure()
    fig.update_layout(
        title="No activity data available",
        template="plotly_white",
        height=350,
    )
    
    if not activity_json:
        return fig
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(activity_json, orient='split')
        
        # Calculate overall activity ratio
        if 'individual_id' in df.columns:
            # Group by individual
            summary_df = df.groupby('individual_id').agg(
                avg_activity=('activity_ratio', 'mean')
            ).reset_index()
            
            # Calculate active and resting percentages
            summary_df['active_percent'] = summary_df['avg_activity'] * 100
            summary_df['resting_percent'] = 100 - summary_df['active_percent']
            
            # Create a long-format dataframe for the donut chart
            result = []
            for _, row in summary_df.iterrows():
                result.append({
                    'individual_id': row['individual_id'],
                    'status': 'Active',
                    'percent': row['active_percent']
                })
                result.append({
                    'individual_id': row['individual_id'],
                    'status': 'Resting',
                    'percent': row['resting_percent']
                })
            
            long_df = pd.DataFrame(result)
            
            # Create donut chart
            fig = px.pie(
                long_df,
                values='percent',
                names='status',
                color='status',
                facet_col='individual_id',
                hole=0.4,
                color_discrete_map={'Active': '#3498db', 'Resting': '#95a5a6'}
            )
            
            # Update layout
            fig.update_layout(
                title="Active vs Resting Time",
                height=350,
                margin={"l": 40, "r": 40, "t": 40, "b": 40}
            )
            
            # Update annotations for each facet
            for i, ind in enumerate(summary_df['individual_id']):
                fig.update_traces(
                    textinfo='percent+label',
                    textposition='inside',
                    selector=dict(type='pie'),
                    col=i+1
                )
                
        else:
            # Single individual
            avg_activity = df['activity_ratio'].mean()
            active_percent = avg_activity * 100
            resting_percent = 100 - active_percent
            
            # Create donut chart
            fig = go.Figure(data=[go.Pie(
                labels=['Active', 'Resting'],
                values=[active_percent, resting_percent],
                hole=0.4,
                textinfo='percent+label',
                textposition='inside',
                marker=dict(colors=['#3498db', '#95a5a6'])
            )])
            
            # Update layout
            fig.update_layout(
                title="Active vs Resting Time",
                height=350,
                margin={"l": 40, "r": 40, "t": 40, "b": 40}
            )
        
        return fig
        
    except Exception as e:
        # Return default figure with error information
        fig.update_layout(title=f"Error loading activity data: {str(e)}")
        return fig

# Callback for seasonal patterns chart
@callback(
    Output("behavioral-seasonal-chart", "figure"),
    Input("store-movement-data", "data"),
    prevent_initial_call=True,
)
def update_seasonal_chart(movement_data_json):
    # Default empty figure
    fig = go.Figure()
    fig.update_layout(
        title="No data available or insufficient time period for seasonal analysis",
        template="plotly_white",
        height=350,
    )
    
    if not movement_data_json:
        return fig
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(movement_data_json, orient='split')
        
        # Check if required columns exist
        if 'location_lat' not in df.columns or 'location_long' not in df.columns or 'timestamp' not in df.columns:
            return fig
            
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate study duration in days
        duration_days = (df['timestamp'].max() - df['timestamp'].min()).days
        
        # Only proceed if we have at least 30 days of data
        if duration_days < 30:
            fig.update_layout(title="Insufficient data period for seasonal analysis (need >30 days)")
            return fig
        
        # Calculate monthly aggregates
        df['month'] = df['timestamp'].dt.month
        df['month_name'] = df['timestamp'].dt.strftime('%B')
        
        # Calculate distance between consecutive points
        if 'individual_id' in df.columns:
            df = df.sort_values(['individual_id', 'timestamp'])
            df['next_lat'] = df.groupby('individual_id')['location_lat'].shift(-1)
            df['next_long'] = df.groupby('individual_id')['location_long'].shift(-1)
        else:
            df = df.sort_values('timestamp')
            df['next_lat'] = df['location_lat'].shift(-1)
            df['next_long'] = df['location_long'].shift(-1)
        
        # Calculate distance in km
        df['distance'] = np.nan
        for i in range(len(df) - 1):
            # Skip if next point is from a different individual
            if 'individual_id' in df.columns:
                if df.iloc[i]['individual_id'] != df.iloc[i+1]['individual_id']:
                    continue
                    
            df.loc[df.index[i], 'distance'] = haversine_distance(
                df.loc[df.index[i], 'location_lat'],
                df.loc[df.index[i], 'location_long'],
                df.loc[df.index[i], 'next_lat'],
                df.loc[df.index[i], 'next_long']
            )
        
        # Aggregate by month
        if 'individual_id' in df.columns:
            monthly_df = df.groupby(['individual_id', 'month', 'month_name']).agg(
                total_distance=('distance', 'sum'),
                avg_distance=('distance', 'mean'),
                point_count=('timestamp', 'count')
            ).reset_index()
        else:
            monthly_df = df.groupby(['month', 'month_name']).agg(
                total_distance=('distance', 'sum'),
                avg_distance=('distance', 'mean'),
                point_count=('timestamp', 'count')
            ).reset_index()
        
        # Sort by month
        monthly_df['month_order'] = monthly_df['month']
        monthly_df = monthly_df.sort_values('month_order')
        
        # Create seasonal patterns chart
        if 'individual_id' in monthly_df.columns:
            fig = px.line(
                monthly_df, 
                x="month_name", 
                y="total_distance", 
                color="individual_id",
                title="Seasonal Movement Patterns",
                labels={"month_name": "Month", "total_distance": "Total Distance (km)"},
                markers=True
            )
        else:
            fig = px.line(
                monthly_df, 
                x="month_name", 
                y="total_distance", 
                title="Seasonal Movement Patterns",
                labels={"month_name": "Month", "total_distance": "Total Distance (km)"},
                markers=True
            )
        
        # Update layout
        fig.update_layout(
            height=350,
            template="plotly_white",
            margin={"l": 40, "r": 40, "t": 40, "b": 40},
            xaxis={
                'categoryorder': 'array',
                'categoryarray': ['January', 'February', 'March', 'April', 'May', 'June', 
                                 'July', 'August', 'September', 'October', 'November', 'December']
            }
        )
        
        return fig
        
    except Exception as e:
        # Return default figure with error information
        fig.update_layout(title=f"Error in seasonal analysis: {str(e)}")
        return fig

# Callback for behavioral timeline
@callback(
    Output("behavioral-timeline-chart", "figure"),
    [
        Input("store-movement-data", "data"),
        Input("store-activity", "data"),
        Input("behavioral-timeline-individual", "value"),
    ],
    prevent_initial_call=True,
)
def update_behavioral_timeline(movement_data_json, activity_json, selected_individual):
    # Default empty figure
    fig = go.Figure()
    fig.update_layout(
        title="No data available for behavioral timeline",
        template="plotly_white",
        height=400,
    )
    
    if not movement_data_json or not activity_json:
        return fig
    
    try:
        # Convert JSONs to DataFrames
        move_df = pd.read_json(movement_data_json, orient='split')
        activity_df = pd.read_json(activity_json, orient='split')
        
        # Check if required columns exist
        if 'timestamp' not in move_df.columns:
            return fig
            
        # Ensure timestamp is datetime
        move_df['timestamp'] = pd.to_datetime(move_df['timestamp'])
        
        # Filter by individual if specified and available
        if selected_individual and 'individual_id' in move_df.columns:
            move_df = move_df[move_df['individual_id'] == selected_individual]
        
        if len(move_df) == 0:
            fig.update_layout(title="No data available for selected individual")
            return fig
        
        # Calculate daily activity stats
        move_df['date'] = move_df['timestamp'].dt.date
        move_df['hour'] = move_df['timestamp'].dt.hour
        
        # Create daily activity grid
        # First get the activity pattern by hour
        hourly_activity = {}
        for _, row in activity_df.iterrows():
            if 'individual_id' in activity_df.columns:
                if selected_individual and row['individual_id'] != selected_individual:
                    continue
                hourly_activity[row['hour_of_day']] = row['activity']
            else:
                hourly_activity[row['hour_of_day']] = row['activity']
        
        # Then create a timeline
        dates = sorted(move_df['date'].unique())
        hours = list(range(24))
        
        timeline_data = []
        
        for date in dates:
            date_points = move_df[move_df['date'] == date]
            for hour in hours:
                hour_points = date_points[date_points['hour'] == hour]
                activity_level = hourly_activity.get(hour, 0) if hourly_activity else 0
                
                # Determine if we have data for this hour
                has_data = len(hour_points) > 0
                
                timeline_data.append({
                    'date': date,
                    'hour': hour,
                    'activity': activity_level if has_data else 0,
                    'has_data': has_data
                })
        
        timeline_df = pd.DataFrame(timeline_data)
        
        # Convert to matrix format for heatmap
        matrix_df = timeline_df.pivot(index='date', columns='hour', values='activity')
        
        # Create heatmap
        fig = px.imshow(
            matrix_df,
            labels=dict(x="Hour of Day", y="Date", color="Activity"),
            x=hours,
            y=[str(date) for date in matrix_df.index],
            color_continuous_scale='Viridis',
            title="Behavioral Timeline" + (f" for {selected_individual}" if selected_individual else "")
        )
        
        # Update layout
        fig.update_layout(
            height=400,
            template="plotly_white",
            margin={"l": 40, "r": 40, "t": 40, "b": 40},
            xaxis={
                'tickmode': 'array',
                'tickvals': list(range(0, 24, 3)),
                'ticktext': ['12 AM', '3 AM', '6 AM', '9 AM', '12 PM', '3 PM', '6 PM', '9 PM']
            }
        )
        
        return fig
        
    except Exception as e:
        # Return default figure with error information
        fig.update_layout(title=f"Error creating behavioral timeline: {str(e)}")
        return fig

# Populate behavioral pattern dropdown with available individuals
@callback(
    [
        Output("behavioral-individuals", "options"),
        Output("behavioral-individuals", "value"),
        Output("behavioral-timeline-individual", "options"),
        Output("behavioral-timeline-individual", "value"),
    ],
    Input("store-movement-data", "data"),
    prevent_initial_call=True,
)
def update_behavioral_filter_options(movement_data_json):
    if not movement_data_json:
        return [], [], [], None
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(movement_data_json, orient='split')
        
        if 'individual_id' not in df.columns:
            return [], [], [], None
        
        # Get unique individuals
        individuals = df['individual_id'].unique().tolist()
        options = [{'label': ind, 'value': ind} for ind in individuals]
        
        # Use "all" string instead of None for the All Individuals option
        timeline_options = [{'label': 'All Individuals', 'value': 'all'}] + options
        
        return options, individuals, timeline_options, 'all'  # Select 'All Individuals' by default
    except Exception:
        return [], [], [], None

# Data Quality Analysis Callbacks
@callback(
    Output("store-data-quality", "data"),
    [
        Input("store-movement-data", "data"),
        Input("quality-sampling-rate", "value"),
        Input("quality-individual", "value"),
    ],
    prevent_initial_call=True,
)
def calculate_data_quality(movement_data_json, expected_sampling_rate, selected_individual):
    if not movement_data_json:
        return json.dumps({})
    
    # Default values if not provided
    if not expected_sampling_rate or expected_sampling_rate <= 0:
        expected_sampling_rate = 60  # Default: 1 fix per hour (60 minutes)
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(movement_data_json, orient='split')
        
        # Check if required columns exist
        if 'timestamp' not in df.columns:
            return json.dumps({})
        
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Apply individual filter if provided
        if selected_individual and 'individual_id' in df.columns:
            df = df[df['individual_id'] == selected_individual]
            
        # Calculate data quality metrics
        quality_metrics = calculate_quality_metrics(df, expected_sampling_rate)
        
        # Return as JSON
        return json.dumps(quality_metrics)
    
    except Exception as e:
        print(f"Error calculating data quality metrics: {str(e)}")
        return json.dumps({})

# Calculate data quality metrics
def calculate_quality_metrics(df, expected_sampling_rate):
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    # Calculate date range
    start_date = df['timestamp'].min()
    end_date = df['timestamp'].max()
    date_range = (end_date - start_date).total_seconds() / 60  # in minutes
    
    # Expected fixes based on sampling rate
    expected_fixes = int(date_range / expected_sampling_rate)
    actual_fixes = len(df)
    
    # Fix success rate
    fix_success_rate = min(100, (actual_fixes / expected_fixes * 100)) if expected_fixes > 0 else 0
    
    # Time gaps between consecutive fixes
    df['next_timestamp'] = df['timestamp'].shift(-1)
    df['time_gap'] = (df['next_timestamp'] - df['timestamp']).dt.total_seconds() / 60  # in minutes
    
    # Identify outages (gaps larger than 2x expected sampling rate)
    outage_threshold = expected_sampling_rate * 2
    df['is_outage'] = df['time_gap'] > outage_threshold
    outages = df[df['is_outage']]
    
    # Calculate outage statistics
    total_outages = len(outages)
    total_outage_time = outages['time_gap'].sum() if not outages.empty else 0
    avg_outage_duration = outages['time_gap'].mean() if not outages.empty else 0
    max_outage_duration = outages['time_gap'].max() if not outages.empty else 0
    
    # Calculate daily completeness
    df['date'] = df['timestamp'].dt.date
    daily_counts = df.groupby('date').size()
    daily_expected = 24 * 60 / expected_sampling_rate  # expected fixes per day
    daily_completeness = daily_counts / daily_expected * 100
    daily_completeness = daily_completeness.clip(upper=100)  # Cap at 100%
    
    # Prepare daily completeness for chart
    daily_comp_data = [
        {
            'date': str(date),
            'completeness': completeness
        } for date, completeness in zip(daily_completeness.index, daily_completeness)
    ]
    
    # Prepare outage data for timeline
    outage_data = []
    if not outages.empty:
        for _, row in outages.iterrows():
            outage_data.append({
                'start_time': row['timestamp'].isoformat(),
                'end_time': row['next_timestamp'].isoformat(),
                'duration': row['time_gap']
            })
    
    # Calculate weekly or monthly patterns if enough data
    temporal_patterns = {}
    if (end_date - start_date).days >= 7:  # At least a week of data
        df['day_of_week'] = df['timestamp'].dt.day_name()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekly_counts = df.groupby('day_of_week').size().reindex(day_order).fillna(0).to_dict()
        temporal_patterns['weekly'] = weekly_counts
    
    if (end_date - start_date).days >= 30:  # At least a month of data
        df['hour_of_day'] = df['timestamp'].dt.hour
        hourly_counts = df.groupby('hour_of_day').size().to_dict()
        temporal_patterns['hourly'] = hourly_counts
    
    # Return all metrics
    return {
        'summary': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_points': actual_fixes,
            'expected_points': expected_fixes,
            'fix_success_rate': fix_success_rate,
            'total_outages': total_outages,
            'total_outage_time': total_outage_time,  # in minutes
            'avg_outage_duration': avg_outage_duration,  # in minutes
            'max_outage_duration': max_outage_duration,  # in minutes
        },
        'daily_completeness': daily_comp_data,
        'outages': outage_data,
        'temporal_patterns': temporal_patterns
    }

# Callback to update data quality KPI cards
@callback(
    [
        Output("quality-fix-success-rate", "children"),
        Output("quality-total-outages", "children"),
        Output("quality-outage-duration", "children"),
        Output("quality-data-completeness", "children"),
    ],
    Input("store-data-quality", "data"),
    prevent_initial_call=True,
)
def update_quality_kpi_cards(quality_json):
    if not quality_json:
        return "N/A", "N/A", "N/A", "N/A"
    
    try:
        # Parse JSON
        quality_data = json.loads(quality_json)
        summary = quality_data.get('summary', {})
        
        # Extract metrics
        fix_success_rate = summary.get('fix_success_rate', 0)
        total_outages = summary.get('total_outages', 0)
        avg_outage_duration = summary.get('avg_outage_duration', 0)
        
        # Calculate overall data completeness
        total_points = summary.get('total_points', 0)
        expected_points = summary.get('expected_points', 0)
        data_completeness = (total_points / expected_points * 100) if expected_points > 0 else 0
        data_completeness = min(100, data_completeness)  # Cap at 100%
        
        # Format for display
        fix_success_display = f"{fix_success_rate:.1f}%"
        outages_display = f"{total_outages}"
        outage_duration_display = f"{avg_outage_duration:.1f} min" if total_outages > 0 else "N/A"
        completeness_display = f"{data_completeness:.1f}%"
        
        return fix_success_display, outages_display, outage_duration_display, completeness_display
    
    except Exception as e:
        print(f"Error updating quality KPI cards: {str(e)}")
        return "Error", "Error", "Error", "Error"

# Callback to update daily completeness chart
@callback(
    Output("quality-completeness-chart", "figure"),
    Input("store-data-quality", "data"),
    prevent_initial_call=True,
)
def update_completeness_chart(quality_json):
    # Default empty figure
    fig = go.Figure()
    fig.update_layout(
        title="No data available",
        template="plotly_white",
        height=300,
    )
    
    if not quality_json:
        return fig
    
    try:
        # Parse JSON
        quality_data = json.loads(quality_json)
        daily_completeness = quality_data.get('daily_completeness', [])
        
        if not daily_completeness:
            return fig
        
        # Convert to DataFrame
        df = pd.DataFrame(daily_completeness)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Create bar chart
        fig = px.bar(
            df,
            x='date',
            y='completeness',
            title="Daily Data Completeness",
            labels={'date': 'Date', 'completeness': 'Completeness (%)'},
            color='completeness',
            color_continuous_scale=[[0, 'red'], [0.5, 'yellow'], [0.8, 'green'], [1, 'green']]
        )
        
        # Add threshold line at 80%
        fig.add_shape(
            type="line",
            x0=df['date'].min(),
            x1=df['date'].max(),
            y0=80,
            y1=80,
            line=dict(color="black", width=2, dash="dash"),
        )
        
        # Update layout
        fig.update_layout(
            height=300,
            template="plotly_white",
            margin={"l": 40, "r": 40, "t": 40, "b": 40},
            coloraxis_showscale=False
        )
        
        return fig
        
    except Exception as e:
        # Return default figure with error information
        fig.update_layout(title=f"Error loading completeness data: {str(e)}")
        return fig

# Callback to update outage timeline
@callback(
    Output("quality-outage-timeline", "figure"),
    Input("store-data-quality", "data"),
    prevent_initial_call=True,
)
def update_outage_timeline(quality_json):
    # Default empty figure
    fig = go.Figure()
    fig.update_layout(
        title="No outage data available",
        template="plotly_white",
        height=300,
    )
    
    if not quality_json:
        return fig
    
    try:
        # Parse JSON
        quality_data = json.loads(quality_json)
        outages = quality_data.get('outages', [])
        summary = quality_data.get('summary', {})
        
        if not outages:
            fig.update_layout(title="No outages detected")
            return fig
        
        # Convert to DataFrame
        df = pd.DataFrame(outages)
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['end_time'] = pd.to_datetime(df['end_time'])
        df = df.sort_values('start_time')
        
        # Get date range for x-axis
        start_date = pd.to_datetime(summary.get('start_date'))
        end_date = pd.to_datetime(summary.get('end_date'))
        
        # Create outage timeline
        fig = go.Figure()
        
        # Add rectangle for each outage
        for i, row in df.iterrows():
            fig.add_trace(go.Scatter(
                x=[row['start_time'], row['end_time'], row['end_time'], row['start_time'], row['start_time']],
                y=[i, i, i+0.8, i+0.8, i],
                fill="toself",
                fillcolor="rgba(255, 0, 0, 0.5)",
                line=dict(color="red"),
                mode="lines",
                name=f"Outage: {row['duration']:.1f} min",
                hoverinfo="text",
                text=f"Start: {row['start_time']}<br>End: {row['end_time']}<br>Duration: {row['duration']:.1f} min"
            ))
        
        # Update layout
        fig.update_layout(
            title="GPS Outage Timeline",
            height=300,
            template="plotly_white",
            margin={"l": 40, "r": 40, "t": 40, "b": 40},
            showlegend=False,
            xaxis=dict(title="Time", range=[start_date, end_date]),
            yaxis=dict(title="Outages", showticklabels=False)
        )
        
        return fig
        
    except Exception as e:
        # Return default figure with error information
        fig.update_layout(title=f"Error loading outage data: {str(e)}")
        return fig

# Callback to update temporal pattern chart
@callback(
    Output("quality-temporal-pattern", "figure"),
    [
        Input("store-data-quality", "data"),
        Input("quality-pattern-type", "value"),
    ],
    prevent_initial_call=True,
)
def update_temporal_pattern(quality_json, pattern_type):
    # Default empty figure
    fig = go.Figure()
    fig.update_layout(
        title="No temporal pattern data available",
        template="plotly_white",
        height=300,
    )
    
    if not quality_json or not pattern_type:
        return fig
    
    try:
        # Parse JSON
        quality_data = json.loads(quality_json)
        temporal_patterns = quality_data.get('temporal_patterns', {})
        
        if not temporal_patterns or pattern_type not in temporal_patterns:
            fig.update_layout(title=f"No {pattern_type} pattern data available")
            return fig
        
        # Get selected pattern
        pattern_data = temporal_patterns[pattern_type]
        
        # Convert to DataFrame
        df = pd.DataFrame(list(pattern_data.items()), columns=['period', 'count'])
        
        if pattern_type == 'weekly':
            # Ensure correct day order
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            df['period'] = pd.Categorical(df['period'], categories=day_order, ordered=True)
            df = df.sort_values('period')
            x_title = "Day of Week"
        else:  # hourly
            df['period'] = pd.to_numeric(df['period'])
            df = df.sort_values('period')
            x_title = "Hour of Day"
        
        # Create bar chart
        fig = px.bar(
            df,
            x='period',
            y='count',
            title=f"GPS Fix Distribution by {x_title}",
            labels={'period': x_title, 'count': 'Number of Fixes'}
        )
        
        # Update layout
        fig.update_layout(
            height=300,
            template="plotly_white",
            margin={"l": 40, "r": 40, "t": 40, "b": 40}
        )
        
        # Format x-axis for hourly pattern
        if pattern_type == 'hourly':
            fig.update_xaxes(
                tickmode='array',
                tickvals=list(range(0, 24, 3)),
                ticktext=['12 AM', '3 AM', '6 AM', '9 AM', '12 PM', '3 PM', '6 PM', '9 PM']
            )
        
        return fig
        
    except Exception as e:
        # Return default figure with error information
        fig.update_layout(title=f"Error loading temporal pattern data: {str(e)}")
        return fig

# Populate data quality filter dropdown with available individuals
@callback(
    [
        Output("quality-individual", "options"),
        Output("quality-individual", "value"),
    ],
    Input("store-movement-data", "data"),
    prevent_initial_call=True,
)
def update_quality_individual_filter(movement_data_json):
    if not movement_data_json:
        return [], None
    
    try:
        # Convert JSON to DataFrame
        df = pd.read_json(movement_data_json, orient='split')
        
        if 'individual_id' not in df.columns:
            return [], None
        
        # Get unique individuals
        individuals = df['individual_id'].unique().tolist()
        options = [{'label': 'All Individuals', 'value': None}] + [{'label': ind, 'value': ind} for ind in individuals]
        
        return options, None  # Select all individuals by default
    except Exception:
        return [], None

if __name__ == "__main__":
    app.run(debug=True)
