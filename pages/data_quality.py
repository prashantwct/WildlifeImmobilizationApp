"""
Data Quality Page
Provides metrics and visualizations for assessing GPS tracking data quality
"""

import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Create data quality layout with fix success rates, gaps analysis, and error identification
layout = html.Div([
    # Page header
    html.Div([
        html.H2("Data Quality Assessment", className="page-title"),
        html.P("Monitor tracking data quality, identify gaps, and assess reliability", 
               className="page-subtitle")
    ], className="page-header"),
    
    # Main content
    dbc.Row([
        # Left column - Fix success rates and tracking metrics
        dbc.Col([
            # Fix Success Rate Card
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("GPS Fix Success Rate"), width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("Daily", id="fix-daily-btn", color="primary", size="sm", outline=True, className="me-1"),
                                dbc.Button("Weekly", id="fix-weekly-btn", color="secondary", size="sm", outline=True, className="me-1"),
                                dbc.Button("Monthly", id="fix-monthly-btn", color="secondary", size="sm", outline=True)
                            ])
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Graph(
                        id="fix-success-chart",
                        config={'displayModeBar': True},
                        style={'height': '380px'}
                    )
                ])
            ], className="mb-4"),
            
            # Data Completeness Card
            dbc.Card([
                dbc.CardHeader("Data Completeness"),
                dbc.CardBody([
                    dbc.Row([
                        # Individual completeness
                        dbc.Col([
                            html.Div([
                                html.H6("Completeness by Individual"),
                                dcc.Graph(
                                    id="individual-completeness-chart",
                                    config={'displayModeBar': False},
                                    style={'height': '300px'}
                                )
                            ])
                        ], width=12)
                    ])
                ])
            ])
        ], width=6),
        
        # Right column - Data gaps and error analysis
        dbc.Col([
            # Data Gaps Card
            dbc.Card([
                dbc.CardHeader("Data Gaps Analysis"),
                dbc.CardBody([
                    dbc.Row([
                        # Gap timeline
                        dbc.Col([
                            html.Div([
                                html.H6("Data Gap Timeline"),
                                dcc.Graph(
                                    id="data-gap-timeline",
                                    config={'displayModeBar': True},
                                    style={'height': '250px'}
                                )
                            ])
                        ], width=12)
                    ]),
                    
                    html.Hr(),
                    
                    dbc.Row([
                        dbc.Col([
                            html.H6("Major Data Gaps", className="mb-3"),
                            html.Div(id="major-gaps-table", className="stats-table")
                        ], width=12)
                    ])
                ])
            ], className="mb-4"),
            
            # Error Detection Card
            dbc.Card([
                dbc.CardHeader("Error Detection"),
                dbc.CardBody([
                    dbc.Row([
                        # Error detection tabs
                        dbc.Col([
                            dbc.Tabs([
                                dbc.Tab([
                                    html.Div([
                                        html.P("Outliers based on implausible movement speeds:", className="mt-3"),
                                        dcc.Graph(
                                            id="speed-outliers-chart",
                                            config={'displayModeBar': False},
                                            style={'height': '200px'}
                                        )
                                    ])
                                ], label="Speed Outliers"),
                                
                                dbc.Tab([
                                    html.Div([
                                        html.P("Positions outside expected spatial range:", className="mt-3"),
                                        dcc.Graph(
                                            id="spatial-outliers-chart",
                                            config={'displayModeBar': False},
                                            style={'height': '200px'}
                                        )
                                    ])
                                ], label="Spatial Outliers"),
                                
                                dbc.Tab([
                                    html.Div([
                                        html.P("GPS signal quality metrics:", className="mt-3"),
                                        dcc.Graph(
                                            id="signal-quality-chart",
                                            config={'displayModeBar': False},
                                            style={'height': '200px'}
                                        )
                                    ])
                                ], label="Signal Quality")
                            ])
                        ], width=12)
                    ])
                ])
            ])
        ], width=6)
    ]),
    
    # Bottom row - Data quality metrics and summary
    dbc.Row([
        # Summary stats
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Data Quality Summary"),
                dbc.CardBody([
                    dbc.Row([
                        # Fix success rate
                        dbc.Col([
                            html.H6("Overall Fix Success", className="stat-header"),
                            html.Div([
                                html.H4(id="overall-fix-success", className="stat-value"),
                                html.P("% of expected fixes", className="stat-label")
                            ], className="stat-container")
                        ], width=3),
                        
                        # Total gaps
                        dbc.Col([
                            html.H6("Total Data Gaps", className="stat-header"),
                            html.Div([
                                html.H4(id="total-gaps", className="stat-value"),
                                html.P("gaps over 3x fix interval", className="stat-label")
                            ], className="stat-container")
                        ], width=3),
                        
                        # Missing data time
                        dbc.Col([
                            html.H6("Missing Data Time", className="stat-header"),
                            html.Div([
                                html.H4(id="missing-data-time", className="stat-value"),
                                html.P("hours of missing data", className="stat-label")
                            ], className="stat-container")
                        ], width=3),
                        
                        # Overall quality score
                        dbc.Col([
                            html.H6("Quality Score", className="stat-header"),
                            html.Div([
                                html.H4(id="quality-score", className="stat-value"),
                                html.P("out of 100", className="stat-label")
                            ], className="stat-container")
                        ], width=3)
                    ])
                ])
            ])
        ], width=12)
    ], className="mt-4"),
    
    # Settings and actions row
    dbc.Row([
        # Quality settings
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Quality Analysis Settings"),
                dbc.CardBody([
                    dbc.Row([
                        # Expected fix interval
                        dbc.Col([
                            html.Label("Expected Fix Interval (minutes):"),
                            dbc.Input(
                                id="fix-interval-input",
                                type="number",
                                value=60,
                                min=1,
                                step=1,
                                className="mb-2"
                            )
                        ], width=6),
                        
                        # Speed threshold for outliers
                        dbc.Col([
                            html.Label("Speed Threshold for Outliers (km/h):"),
                            dbc.Input(
                                id="speed-threshold-input",
                                type="number",
                                value=20,
                                min=1,
                                step=1,
                                className="mb-2"
                            )
                        ], width=6)
                    ]),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "Update Quality Analysis",
                                id="update-quality-btn",
                                color="primary",
                                className="w-100"
                            )
                        ], width=12)
                    ])
                ])
            ])
        ], width=6),
        
        # Action buttons
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Data Quality Actions"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                html.Span([
                                    html.I(className="fas fa-file-export me-2"), 
                                    "Export Quality Report"
                                ]),
                                id="export-quality-report-btn",
                                color="success",
                                className="w-100 mb-2"
                            )
                        ], width=6),
                        
                        dbc.Col([
                            dbc.Button(
                                html.Span([
                                    html.I(className="fas fa-filter me-2"), 
                                    "Filter Outliers"
                                ]),
                                id="filter-outliers-btn",
                                color="warning",
                                className="w-100 mb-2"
                            )
                        ], width=6)
                    ]),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                html.Span([
                                    html.I(className="fas fa-chart-line me-2"), 
                                    "Analyze Fix Success Factors"
                                ]),
                                id="analyze-fix-success-btn",
                                color="info",
                                className="w-100"
                            )
                        ], width=12)
                    ])
                ])
            ])
        ], width=6)
    ], className="mt-4"),
    
    # Hidden components to store state
    dcc.Store(id="quality-data-store"),
    dcc.Store(id="gaps-data-store"),
    dcc.Store(id="outliers-data-store")
])

# Callbacks will be defined in app.py to avoid circular imports
