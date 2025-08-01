"""
Behavioral Patterns Page
Analyzes and visualizes carnivore activity patterns, resting behaviors, and temporal rhythms
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

# Create behavioral patterns layout with activity analysis, resting patterns, and seasonal changes
layout = html.Div([
    # Page header
    html.Div([
        html.H2("Behavioral Patterns", className="page-title"),
        html.P("Analyze activity rhythms, resting behaviors, and temporal patterns", 
               className="page-subtitle")
    ], className="page-header"),
    
    # Main content
    dbc.Row([
        # Left column - Activity patterns
        dbc.Col([
            # Daily Activity Rhythm Card
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("Daily Activity Rhythm"), width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("Linear", id="activity-linear-btn", color="primary", size="sm", outline=True, className="me-1"),
                                dbc.Button("Circular", id="activity-circular-btn", color="secondary", size="sm", outline=True)
                            ])
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Graph(
                        id="daily-activity-rhythm-chart",
                        config={'displayModeBar': True},
                        style={'height': '380px'}
                    )
                ])
            ], className="mb-4"),
            
            # Day vs Night Activity Card
            dbc.Card([
                dbc.CardHeader("Diurnal vs. Nocturnal Activity"),
                dbc.CardBody([
                    dbc.Row([
                        # Day/Night Ratio Gauge
                        dbc.Col([
                            dcc.Graph(
                                id="day-night-ratio-gauge",
                                config={'displayModeBar': False},
                                style={'height': '250px'}
                            )
                        ], width=6),
                        
                        # Day/Night Stats
                        dbc.Col([
                            html.Div([
                                html.H5("Activity Analysis"),
                                
                                html.Div([
                                    html.P("Day Activity (6 AM - 6 PM):", className="mb-1"),
                                    dbc.Progress(id="day-activity-bar", value=65, color="warning", className="mb-3", 
                                               style={"height": "20px"})
                                ]),
                                
                                html.Div([
                                    html.P("Night Activity (6 PM - 6 AM):", className="mb-1"),
                                    dbc.Progress(id="night-activity-bar", value=35, color="primary", className="mb-3",
                                               style={"height": "20px"})
                                ]),
                                
                                html.Div([
                                    html.P(id="activity-classification-text", className="mt-3 fw-bold text-center")
                                ])
                            ])
                        ], width=6)
                    ])
                ])
            ])
        ], width=6),
        
        # Right column - Resting and seasonal patterns
        dbc.Col([
            # Active vs Resting Time Card
            dbc.Card([
                dbc.CardHeader("Active vs. Resting Time"),
                dbc.CardBody([
                    dbc.Row([
                        # Active/Rest Ratio Chart
                        dbc.Col([
                            dcc.Graph(
                                id="active-rest-chart",
                                config={'displayModeBar': False},
                                style={'height': '250px'}
                            )
                        ], width=6),
                        
                        # Active/Rest Stats
                        dbc.Col([
                            html.Div([
                                html.H5("Activity Breakdown"),
                                
                                html.Div([
                                    html.P("Active Time:", className="mb-1"),
                                    dbc.Progress(id="active-time-bar", value=70, color="success", className="mb-3",
                                               style={"height": "20px"})
                                ]),
                                
                                html.Div([
                                    html.P("Resting Time:", className="mb-1"),
                                    dbc.Progress(id="rest-time-bar", value=30, color="info", className="mb-3",
                                               style={"height": "20px"})
                                ]),
                                
                                html.Div([
                                    html.P([
                                        "Speed Threshold for Activity Classification: ",
                                        html.Span(id="speed-threshold-value", className="fw-bold")
                                    ], className="mt-3")
                                ])
                            ])
                        ], width=6)
                    ])
                ])
            ], className="mb-4"),
            
            # Seasonal Patterns Card
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("Seasonal Activity Patterns"), width="auto"),
                        dbc.Col([
                            dcc.Dropdown(
                                id="seasonal-pattern-metric",
                                options=[
                                    {"label": "Activity Level", "value": "activity"},
                                    {"label": "Movement Distance", "value": "distance"},
                                    {"label": "Average Speed", "value": "speed"},
                                    {"label": "Home Range Size", "value": "range"}
                                ],
                                value="activity",
                                clearable=False,
                                style={"width": "150px"}
                            )
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Graph(
                        id="seasonal-pattern-chart",
                        config={'displayModeBar': True},
                        style={'height': '250px'}
                    )
                ])
            ])
        ], width=6)
    ]),
    
    # Bottom row - Behavioral timeline
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("Behavioral Timeline"), width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("1 Week", id="timeline-1week-btn", color="secondary", size="sm", outline=True, className="me-1"),
                                dbc.Button("1 Month", id="timeline-1month-btn", color="primary", size="sm", outline=True, className="me-1"),
                                dbc.Button("3 Months", id="timeline-3month-btn", color="secondary", size="sm", outline=True, className="me-1"),
                                dbc.Button("All Data", id="timeline-all-btn", color="secondary", size="sm", outline=True)
                            ])
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Graph(
                        id="behavioral-timeline-chart",
                        config={'displayModeBar': True},
                        style={'height': '300px'}
                    )
                ])
            ])
        ], width=12)
    ], className="mt-4"),
    
    # Analysis settings row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Analysis Settings"),
                dbc.CardBody([
                    dbc.Row([
                        # Speed threshold slider
                        dbc.Col([
                            html.Label("Speed Threshold for Active/Rest (m/s):"),
                            dcc.Slider(
                                id="activity-speed-threshold",
                                min=0.05,
                                max=1.0,
                                step=0.05,
                                value=0.2,
                                marks={i/100: str(i/100) for i in range(5, 101, 15)},
                                className="mb-3"
                            )
                        ], width=6),
                        
                        # Day hours range slider
                        dbc.Col([
                            html.Label("Day Hours Definition:"),
                            dcc.RangeSlider(
                                id="day-hours-range",
                                min=0,
                                max=24,
                                step=1,
                                value=[6, 18],
                                marks={i: f"{i}:00" for i in range(0, 25, 3)},
                                className="mb-3"
                            )
                        ], width=6)
                    ]),
                    
                    dbc.Row([
                        # Activity threshold for behavioral patterns
                        dbc.Col([
                            html.Label("Activity Threshold (km):"),
                            dbc.Input(
                                id="behavioral-activity-threshold",
                                type="number",
                                min=0.01,
                                max=1.0,
                                step=0.01,
                                value=0.05,
                                className="mb-3"
                            ),
                            dbc.FormText("Minimum distance to classify as activity")
                        ], width=4),
                        
                        # Time window for behavioral pattern detection
                        dbc.Col([
                            html.Label("Time Window (minutes):"),
                            dbc.Input(
                                id="behavioral-time-window",
                                type="number",
                                min=5,
                                max=240,
                                step=5,
                                value=60,
                                className="mb-3"
                            ),
                            dbc.FormText("Time period for activity aggregation")
                        ], width=4),
                        
                        # Individual animal selection for behavioral analysis
                        dbc.Col([
                            html.Label("Select Individuals:"),
                            dcc.Dropdown(
                                id="behavioral-individuals",
                                multi=True,
                                placeholder="Select animals to analyze...",
                                className="mb-3"
                            ),
                            dbc.FormText("Leave empty to include all animals")
                        ], width=4)
                    ]),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "Recalculate Behavioral Patterns",
                                id="recalculate-behavior-btn",
                                color="primary",
                                className="w-100"
                            )
                        ], width=12)
                    ])
                ])
            ])
        ], width=12)
    ], className="mt-4"),
    
    # Hidden components to store state
    dcc.Store(id="behavioral-data-store"),
    dcc.Store(id="activity-settings-store"),
    dcc.Store(id="seasonal-patterns-store")
])

# Callbacks will be defined in app.py to avoid circular imports
