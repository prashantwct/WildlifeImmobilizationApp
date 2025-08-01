"""
Home Range Analysis Page
Provides visualization and analysis of home range estimates using different methods
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

# Create home range analysis layout with methods, visualizations, and statistics
layout = html.Div([
    # Page header
    html.Div([
        html.H2("Home Range Analysis", className="page-title"),
        html.P("Calculate and visualize home ranges using different estimation methods", 
               className="page-subtitle")
    ], className="page-header"),
    
    # Main content
    dbc.Row([
        # Left column - Method selection and settings
        dbc.Col([
            # Home Range Method Card
            dbc.Card([
                dbc.CardHeader("Home Range Estimation Method"),
                dbc.CardBody([
                    dbc.RadioItems(
                        options=[
                            {"label": "Kernel Density Estimation (KDE)", "value": "kde"},
                            {"label": "Minimum Convex Polygon (MCP)", "value": "mcp"},
                            {"label": "Time Local Convex Hull (T-LoCoH)", "value": "tlocoh"},
                            {"label": "Brownian Bridge", "value": "brownian"}
                        ],
                        value="kde",
                        id="home-range-method",
                        className="mb-3"
                    ),
                    
                    # KDE Settings
                    html.Div([
                        html.P("KDE Settings:", className="mb-2 fw-bold"),
                        
                        html.Label("Smoothing Factor (h):"),
                        dcc.Slider(
                            id="kde-smoothing-factor",
                            min=0.1,
                            max=2.0,
                            step=0.1,
                            value=1.0,
                            marks={i/10: str(i/10) for i in range(1, 21, 5)},
                            className="mb-3"
                        ),
                        
                        html.Label("Grid Resolution:"),
                        dcc.Slider(
                            id="kde-grid-resolution",
                            min=50,
                            max=200,
                            step=25,
                            value=100,
                            marks={i: str(i) for i in range(50, 201, 50)},
                            className="mb-3"
                        )
                    ], id="kde-settings-div"),
                    
                    # MCP Settings
                    html.Div([
                        html.P("MCP Settings:", className="mb-2 fw-bold"),
                        
                        html.Label("Percentage of points to include:"),
                        dcc.Slider(
                            id="mcp-percentage",
                            min=50,
                            max=100,
                            step=5,
                            value=95,
                            marks={i: str(i) for i in range(50, 101, 10)},
                            className="mb-3"
                        )
                    ], id="mcp-settings-div", style={"display": "none"}),
                    
                    # Other Settings
                    html.Div([
                        html.P("Additional Settings:", className="mb-2 fw-bold"),
                        
                        dbc.Checklist(
                            options=[
                                {"label": "Show core areas (50%)", "value": "show_core"},
                                {"label": "Show peripheral areas (95%)", "value": "show_peripheral"},
                                {"label": "Display raw GPS points", "value": "show_points"},
                                {"label": "Color by individual", "value": "color_individual"}
                            ],
                            value=["show_core", "show_peripheral", "show_points"],
                            id="home-range-options",
                            switch=True,
                            className="mb-3"
                        )
                    ]),
                    
                    dbc.Button(
                        "Calculate Home Range",
                        id="calculate-home-range-btn",
                        color="primary",
                        className="mt-2 w-100"
                    )
                ])
            ], className="mb-4"),
            
            # Home Range Statistics Card
            dbc.Card([
                dbc.CardHeader("Home Range Statistics"),
                dbc.CardBody([
                    html.Div(id="home-range-stats-container", className="stats-table")
                ])
            ], className="mb-4"),
            
            # Temporal Analysis Card
            dbc.Card([
                dbc.CardHeader("Temporal Home Range Analysis"),
                dbc.CardBody([
                    html.P("Analyze home range changes over time:"),
                    dbc.RadioItems(
                        options=[
                            {"label": "Monthly", "value": "monthly"},
                            {"label": "Seasonal", "value": "seasonal"},
                            {"label": "Custom periods", "value": "custom"}
                        ],
                        value="seasonal",
                        id="temporal-home-range-period",
                        inline=True,
                        className="mb-3"
                    ),
                    
                    dbc.Button(
                        "Calculate Temporal Changes",
                        id="calculate-temporal-home-range-btn",
                        color="secondary",
                        className="mt-2 w-100"
                    ),
                    
                    dbc.Spinner(
                        children=[html.Div(id="temporal-home-range-results")],
                        size="sm",
                        color="primary",
                        spinner_class_name="mt-3"
                    )
                ])
            ])
        ], width=4),
        
        # Right column - Home range map and comparison
        dbc.Col([
            # Home Range Map Card
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("Home Range Map"), width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button(html.I(className="fas fa-expand-arrows-alt"), 
                                          id="fullscreen-home-range-btn", 
                                          color="light", 
                                          size="sm",
                                          className="me-1"),
                                dbc.Button(html.I(className="fas fa-download"), 
                                          id="download-home-range-btn", 
                                          color="light", 
                                          size="sm")
                            ])
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Loading(
                        id="loading-home-range-map",
                        type="circle",
                        children=[
                            dcc.Graph(
                                id="home-range-map",
                                config={
                                    'scrollZoom': True,
                                    'displayModeBar': True,
                                    'modeBarButtonsToAdd': ['drawrect', 'eraseshape'],
                                },
                                style={'height': '400px'}
                            )
                        ]
                    )
                ])
            ], className="mb-4"),
            
            # Home Range Comparison Card
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("Home Range Comparison"), width="auto"),
                        dbc.Col([
                            dcc.Dropdown(
                                id="home-range-comparison-metric",
                                options=[
                                    {"label": "Area Size", "value": "area"},
                                    {"label": "Core/Peripheral Ratio", "value": "core_ratio"},
                                    {"label": "Overlap", "value": "overlap"},
                                    {"label": "Time in Core Areas", "value": "time_in_core"}
                                ],
                                value="area",
                                clearable=False,
                                style={"width": "180px"}
                            )
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Loading(
                        id="loading-home-range-comparison",
                        type="circle",
                        children=[
                            dcc.Graph(
                                id="home-range-comparison-chart",
                                config={'displayModeBar': True},
                                style={'height': '350px'}
                            )
                        ]
                    )
                ])
            ])
        ], width=8)
    ]),
    
    # Hidden components to store state
    dcc.Store(id="home-range-data-store"),
    dcc.Store(id="temporal-home-range-store"),
    dcc.Store(id="home-range-comparison-store")
])

# Callbacks will be defined in app.py to avoid circular imports
