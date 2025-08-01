""" 
Data Import Page
Handles CSV file upload for GPS tracking data import
"""

import dash
from dash import dcc, html, Input, Output, State, callback, ctx, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Create data import layout focused on CSV upload
layout = html.Div([
    dcc.Store(id="store-movement-data"),
    # Page header
    html.Div([
        html.H2("Data Import & Filtering", className="page-title"),
        html.P("Upload GPS tracking data in CSV format", className="page-subtitle")
    ], className="page-header"),
    
    # Main content
    dbc.Row([
        # Left column: CSV upload
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("CSV File Upload"),
                dbc.CardBody([
                    html.P("Upload a CSV file with GPS tracking data:"),
                    dcc.Upload(
                        id="upload-movebank-csv",
                        children=html.Div([
                            html.I(className="fas fa-file-csv me-2"),
                            "Drag and Drop or ",
                            html.A("Select a CSV File")
                        ]),
                        style={
                            "width": "100%",
                            "height": "80px",
                            "lineHeight": "80px",
                            "borderWidth": "2px",
                            "borderStyle": "dashed",
                            "borderRadius": "5px",
                            "textAlign": "center",
                            "margin-bottom": "15px",
                        },
                        multiple=False
                    ),
                    html.Div(id="upload-status", className="mt-3"),
                    
                    html.Hr(),
                    html.H6("CSV Requirements:"),
                    html.Ul([
                        html.Li("File should be in CSV format"),
                        html.Li("Required columns: individual_id, timestamp, location_lat, location_long"),
                        html.Li("Optional: Additional sensor data (acceleration, activity, temperature)"),
                        html.Li("Timestamps should be in ISO format (YYYY-MM-DD HH:MM:SS)"),
                        html.Li("Maximum file size: 100MB")
                    ]),
                    
                    html.Hr(),
                    html.H6("Sample Format:"),
                    dbc.Table([
                        html.Thead([
                            html.Tr([
                                html.Th("individual_id"),
                                html.Th("timestamp"),
                                html.Th("location_long"),
                                html.Th("location_lat")
                            ])
                        ]),
                        html.Tbody([
                            html.Tr([
                                html.Td("Tiger_01"),
                                html.Td("2023-01-15 14:30:00"),
                                html.Td("78.9621"),
                                html.Td("20.7128")
                            ]),
                            html.Tr([
                                html.Td("Tiger_01"),
                                html.Td("2023-01-15 15:30:00"),
                                html.Td("78.9645"),
                                html.Td("20.7135")
                            ])
                        ])
                    ], bordered=True, hover=True, size="sm")
                ])
            ], className="mb-4")
        ], width=5),
        
        # Right column: Preview and options
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Data Preview and Settings"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H5("Imported Data Summary"),
                            html.Div(id="data-summary", className="mt-3")
                        ], width=12)
                    ], className="mb-3"),
                    
                    html.Hr(),
                    
                    html.H5("Filter Options"),
                    html.P("Date range filter:"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Start Date"),
                            dcc.DatePickerSingle(id="start-date-picker", className="w-100")
                        ], width=6),
                        dbc.Col([
                            dbc.Label("End Date"),
                            dcc.DatePickerSingle(id="end-date-picker", className="w-100")
                        ], width=6)
                    ], className="mb-3"),
                    
                    html.P("Individual selection:"),
                    dbc.Spinner(
                        children=[
                            dcc.Dropdown(
                                id="individuals-dropdown",
                                placeholder="Select individuals...",
                                multi=True,
                                className="mb-3"
                            )
                        ],
                        size="sm",
                        color="primary"
                    ),
                    
                    html.Hr(),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Apply Filters", id="apply-filters-btn", color="primary", className="me-2"),
                            dbc.Button("Reset", id="reset-data-btn", color="danger", outline=True),
                        ], width=12)
                    ])
                ])
            ], className="mb-4")
        ], width=7)
    ]),
    
    # Data preview section
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H5("Data Preview", className="mt-4"),
                dbc.Spinner(
                    children=[
                        dash_table.DataTable(
                            id="data-preview-table",
                            page_size=10,
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "whiteSpace": "normal",
                                "height": "auto",
                                "fontSize": "12px"
                            },
                            style_header={
                                "backgroundColor": "rgb(230, 230, 230)",
                                "fontWeight": "bold"
                            }
                        )
                    ],
                    size="lg",
                    color="primary"
                )
            ], id="data-preview-container", style={"display": "none"})
        ], width=12)
    ]),
    
    # Store components for sharing data between callbacks
    dcc.Store(id="store-movement-data"),
    dcc.Store(id="study-id-store"),
    dcc.Store(id="selected-individuals-store"),
    dcc.Store(id="imported-data-info-store")
])

# Callbacks will be defined in app.py to avoid circular imports
