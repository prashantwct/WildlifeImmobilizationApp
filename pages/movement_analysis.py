"""
Movement Analysis Page
Provides detailed analysis of movement patterns, daily distances, and speeds
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

# Create movement analysis layout with charts, statistics, and comparison features
layout = html.Div([
    # Page header
    html.Div([
        html.H2("Movement Analysis", className="page-title"),
        html.P("Analyze movement patterns, distances, and speeds for selected carnivores", 
               className="page-subtitle")
    ], className="page-header"),
    
    # Main content
    dbc.Row([
        # Left column - Movement metrics and charts
        dbc.Col([
            # Daily Distance Chart Card
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("Daily Movement Distance"), width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("Day", id="daily-dist-day-btn", color="primary", size="sm", outline=True, className="me-1"),
                                dbc.Button("Week", id="daily-dist-week-btn", color="secondary", size="sm", outline=True, className="me-1"),
                                dbc.Button("Month", id="daily-dist-month-btn", color="secondary", size="sm", outline=True)
                            ])
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Graph(
                        id="daily-distance-chart-full",
                        config={'displayModeBar': True},
                        style={'height': '380px'}
                    )
                ])
            ], className="mb-4"),
            
            # Movement Speed Analysis Card
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("Movement Speed Analysis"), width="auto"),
                        dbc.Col([
                            dcc.Dropdown(
                                id="speed-analysis-dropdown",
                                options=[
                                    {"label": "Distribution", "value": "distribution"},
                                    {"label": "Temporal Trends", "value": "temporal"},
                                    {"label": "Box Plot", "value": "boxplot"}
                                ],
                                value="distribution",
                                clearable=False,
                                style={"width": "150px"}
                            )
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Graph(
                        id="speed-analysis-chart",
                        config={'displayModeBar': True},
                        style={'height': '380px'}
                    )
                ])
            ])
        ], width=6),
        
        # Right column - Stats and additional analysis
        dbc.Col([
            # Movement Stats Card
            dbc.Card([
                dbc.CardHeader("Movement Statistics"),
                dbc.CardBody([
                    dbc.Row([
                        # Total Distance Column
                        dbc.Col([
                            html.H6("Total Distance"),
                            html.Div([
                                html.H3(id="total-distance-stat", className="stat-value"),
                                html.P("kilometers", className="stat-label")
                            ], className="stat-container")
                        ], width=6),
                        
                        # Average Daily Distance Column
                        dbc.Col([
                            html.H6("Avg. Daily Distance"),
                            html.Div([
                                html.H3(id="avg-daily-distance-stat", className="stat-value"),
                                html.P("km/day", className="stat-label")
                            ], className="stat-container")
                        ], width=6)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        # Average Speed Column
                        dbc.Col([
                            html.H6("Average Speed"),
                            html.Div([
                                html.H3(id="avg-speed-stat", className="stat-value"),
                                html.P("km/h", className="stat-label")
                            ], className="stat-container")
                        ], width=6),
                        
                        # Maximum Speed Column
                        dbc.Col([
                            html.H6("Maximum Speed"),
                            html.Div([
                                html.H3(id="max-speed-stat", className="stat-value"),
                                html.P("km/h", className="stat-label")
                            ], className="stat-container")
                        ], width=6)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        # Time Active Column
                        dbc.Col([
                            html.H6("Time Active"),
                            html.Div([
                                html.H3(id="time-active-stat", className="stat-value"),
                                html.P("% of total time", className="stat-label")
                            ], className="stat-container")
                        ], width=6),
                        
                        # Monitoring Period Column
                        dbc.Col([
                            html.H6("Monitoring Period"),
                            html.Div([
                                html.H3(id="monitoring-period-stat", className="stat-value"),
                                html.P("days", className="stat-label")
                            ], className="stat-container")
                        ], width=6)
                    ])
                ])
            ], className="mb-4"),
            
            # Time & Activity Analysis Card
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("Activity Pattern Analysis"), width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("Hourly", id="activity-hourly-btn", color="primary", size="sm", outline=True, className="me-1"),
                                dbc.Button("Day/Night", id="activity-day-night-btn", color="secondary", size="sm", outline=True, className="me-1"),
                                dbc.Button("Weekly", id="activity-weekly-btn", color="secondary", size="sm", outline=True)
                            ])
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Graph(
                        id="activity-pattern-chart-full",
                        config={'displayModeBar': True},
                        style={'height': '380px'}
                    )
                ])
            ])
        ], width=6)
    ]),
    
    # Bottom row - Comparison features
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("Movement Comparison"), width="auto"),
                        dbc.Col([
                            dbc.Select(
                                id="comparison-metric-select",
                                options=[
                                    {"label": "Daily Distance", "value": "daily_distance"},
                                    {"label": "Speed", "value": "speed"},
                                    {"label": "Activity Pattern", "value": "activity"},
                                    {"label": "Net Displacement", "value": "displacement"}
                                ],
                                value="daily_distance",
                                style={"width": "200px"}
                            )
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Graph(
                        id="movement-comparison-chart",
                        config={'displayModeBar': True},
                        style={'height': '380px'}
                    )
                ])
            ])
        ], width=12)
    ], className="mt-4"),
    
    # Hidden components to store state
    dcc.Store(id="movement-data-store"),
    dcc.Store(id="activity-data-store"),
    dcc.Store(id="comparison-data-store")
])

# Callbacks will be defined in app.py to avoid circular imports
