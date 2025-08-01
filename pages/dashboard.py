"""
Dashboard Overview Page
Provides summary of all KPIs and key visualizations
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

# Create dashboard layout with summary cards, map preview, and key charts
layout = html.Div([
    # Page header
    html.Div([
        html.H2("Carnivore GPS Tracking Dashboard", className="dashboard-title"),
        html.P("Interactive analysis of movement patterns, home ranges, and behavioral insights", 
               className="dashboard-subtitle")
    ], className="page-header"),
    
    # Filter bar
    html.Div([
        dbc.Row([
            # Study selection
            dbc.Col([
                html.Label("Select Study:", className="filter-label"),
                dcc.Dropdown(
                    id="study-select",
                    placeholder="Select a study...",
                    className="filter-dropdown"
                )
            ], width=3),
            
            # Individual selection
            dbc.Col([
                html.Label("Select Individuals:", className="filter-label"),
                dcc.Dropdown(
                    id="individual-select",
                    placeholder="Select individuals...",
                    multi=True,
                    className="filter-dropdown"
                )
            ], width=3),
            
            # Date range
            dbc.Col([
                html.Label("Date Range:", className="filter-label"),
                dcc.DatePickerRange(
                    id="date-range",
                    className="filter-date"
                )
            ], width=4),
            
            # Apply filters button
            dbc.Col([
                html.Br(),
                dbc.Button(
                    "Apply Filters", 
                    id="apply-filters-btn", 
                    color="primary",
                    className="filter-button"
                )
            ], width=2)
        ])
    ], className="filter-bar"),
    
    # Loading indicator
    dcc.Loading(
        id="loading-kpis",
        type="circle",
        children=[
            # KPI Summary Cards
            html.Div([
                dbc.Row([
                    # Distance Traveled Card
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Total Distance", className="card-title"),
                                html.H2(id="total-distance-value", className="kpi-value"),
                                html.P("kilometers traveled", className="kpi-label"),
                                dcc.Graph(id="distance-trend-sparkline", config={'displayModeBar': False})
                            ])
                        ], className="kpi-card")
                    ], width=3),
                    
                    # Home Range Card
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Home Range", className="card-title"),
                                html.H2(id="home-range-value", className="kpi-value"),
                                html.P("sq. kilometers (95% KDE)", className="kpi-label"),
                                dcc.Graph(id="home-range-comparison", config={'displayModeBar': False})
                            ])
                        ], className="kpi-card")
                    ], width=3),
                    
                    # Activity Card
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Active Time", className="card-title"),
                                html.H2(id="active-time-value", className="kpi-value"),
                                html.P("of total monitoring time", className="kpi-label"),
                                dcc.Graph(id="activity-day-night", config={'displayModeBar': False})
                            ])
                        ], className="kpi-card")
                    ], width=3),
                    
                    # Data Quality Card
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Fix Success Rate", className="card-title"),
                                html.H2(id="fix-rate-value", className="kpi-value"),
                                html.P("of expected GPS fixes", className="kpi-label"),
                                dcc.Graph(id="fix-trend-sparkline", config={'displayModeBar': False})
                            ])
                        ], className="kpi-card")
                    ], width=3)
                ]),
                
                # Second row of KPI cards
                dbc.Row([
                    # Average Daily Movement Card
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Avg. Daily Movement", className="card-title"),
                                html.H2(id="avg-daily-movement-value", className="kpi-value"),
                                html.P("kilometers per day", className="kpi-label")
                            ])
                        ], className="kpi-card")
                    ], width=3),
                    
                    # Speed Card
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Avg/Max Speed", className="card-title"),
                                html.H2(id="speed-value", className="kpi-value"),
                                html.P("km/h (avg) / km/h (max)", className="kpi-label")
                            ])
                        ], className="kpi-card")
                    ], width=3),
                    
                    # Core Area Usage Card
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Core Area Usage", className="card-title"),
                                html.H2(id="core-area-value", className="kpi-value"),
                                html.P("of time in core zones", className="kpi-label")
                            ])
                        ], className="kpi-card")
                    ], width=3),
                    
                    # Data Points Card
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Data Points", className="card-title"),
                                html.H2(id="data-points-value", className="kpi-value"),
                                html.P("GPS locations", className="kpi-label")
                            ])
                        ], className="kpi-card")
                    ], width=3)
                ])
            ], className="kpi-container"),
            
            # Map and Charts Section
            html.Div([
                dbc.Row([
                    # Movement Map Preview
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Movement Map Preview"),
                            dbc.CardBody([
                                dcc.Graph(
                                    id="movement-map-preview",
                                    config={'scrollZoom': True, 'displayModeBar': True},
                                    style={'height': '380px'}
                                )
                            ])
                        ])
                    ], width=6),
                    
                    # Activity Pattern Chart
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Activity Patterns"),
                            dbc.CardBody([
                                dcc.Graph(
                                    id="activity-pattern-chart",
                                    config={'displayModeBar': True},
                                    style={'height': '380px'}
                                )
                            ])
                        ])
                    ], width=6)
                ]),
                
                dbc.Row([
                    # Daily Distance Chart
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Daily Movement Distance"),
                            dbc.CardBody([
                                dcc.Graph(
                                    id="daily-distance-chart",
                                    config={'displayModeBar': True},
                                    style={'height': '320px'}
                                )
                            ])
                        ])
                    ], width=6),
                    
                    # Net Squared Displacement Chart
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Net Squared Displacement"),
                            dbc.CardBody([
                                dcc.Graph(
                                    id="nsd-chart",
                                    config={'displayModeBar': True},
                                    style={'height': '320px'}
                                )
                            ])
                        ])
                    ], width=6)
                ], className="mt-4")
            ], className="charts-container"),
            
            # Export and Analysis Actions
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Export Data", id="export-data-btn", color="secondary", className="me-2"),
                        dbc.Button("Export Visualizations", id="export-vis-btn", color="secondary", className="me-2"),
                        dbc.Button("Compare Individuals", id="compare-btn", color="info", className="me-2"),
                        dbc.Button("View Data Quality", id="data-quality-btn", color="warning", className="me-2"),
                    ], className="d-flex justify-content-end")
                ])
            ], className="actions-container")
        ]
    )
])

# Callbacks will be defined in app.py to avoid circular imports
