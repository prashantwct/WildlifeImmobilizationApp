"""
Map Visualization Page
Provides interactive map view of carnivore GPS tracks, home ranges, and movement patterns
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

# Create map visualization layout with map, layers control, and animation options
layout = html.Div([
    # Page header
    html.Div([
        html.H2("Map Visualization", className="page-title"),
        html.P("Interactive map display of GPS tracks, home ranges, and movement patterns", 
               className="page-subtitle")
    ], className="page-header"),
    
    # Map and controls container
    dbc.Row([
        # Left sidebar for map controls
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Map Layers"),
                dbc.CardBody([
                    dbc.Checklist(
                        options=[
                            {"label": "GPS Tracks", "value": "tracks"},
                            {"label": "Movement Points", "value": "points"},
                            {"label": "Home Range (95% KDE)", "value": "home_range_95"},
                            {"label": "Home Range (50% KDE)", "value": "home_range_50"},
                            {"label": "Minimum Convex Polygon", "value": "mcp"},
                            {"label": "Utilization Heatmap", "value": "heatmap"}
                        ],
                        value=["tracks", "points"],
                        id="map-layers-checklist",
                        switch=True,
                        className="mb-3"
                    ),
                    
                    html.Hr(),
                    
                    html.P("Base Map Style:", className="mt-3 mb-2"),
                    dbc.RadioItems(
                        options=[
                            {"label": "Satellite", "value": "satellite"},
                            {"label": "Streets", "value": "streets"},
                            {"label": "Outdoors", "value": "outdoors"},
                            {"label": "Light", "value": "light"},
                            {"label": "Dark", "value": "dark"}
                        ],
                        value="outdoors",
                        id="base-map-style",
                        inline=True,
                        className="mb-3"
                    ),
                    
                    html.Hr(),
                    
                    html.P("Environmental Overlays:", className="mt-3 mb-2"),
                    dbc.Checklist(
                        options=[
                            {"label": "Terrain", "value": "terrain"},
                            {"label": "Water Bodies", "value": "water"},
                            {"label": "Land Cover", "value": "landcover"},
                            {"label": "Protected Areas", "value": "protected"},
                            {"label": "Roads", "value": "roads"},
                            {"label": "Settlements", "value": "settlements"}
                        ],
                        value=[],
                        id="environmental-layers",
                        className="mb-3"
                    )
                ])
            ], className="mb-3"),
            
            dbc.Card([
                dbc.CardHeader("Animation Controls"),
                dbc.CardBody([
                    html.P("Movement Animation:"),
                    dbc.Button(
                        html.Span([
                            html.I(className="fas fa-play me-2"), 
                            "Play Animation"
                        ]),
                        id="play-animation-btn",
                        color="success",
                        className="mb-2 w-100"
                    ),
                    
                    html.P("Animation Speed:", className="mt-3 mb-2"),
                    dcc.Slider(
                        id="animation-speed-slider",
                        min=1,
                        max=10,
                        step=1,
                        value=5,
                        marks={i: str(i) for i in range(1, 11, 3)},
                        className="mb-3"
                    ),
                    
                    html.P("Time Period:", className="mt-3 mb-2"),
                    dcc.RangeSlider(
                        id="time-period-slider",
                        min=0,
                        max=100,
                        step=1,
                        value=[0, 100],
                        marks={},
                        className="mb-3"
                    ),
                    
                    dbc.Button(
                        html.Span([
                            html.I(className="fas fa-camera me-2"), 
                            "Capture Screenshot"
                        ]),
                        id="capture-screenshot-btn",
                        color="info",
                        outline=True,
                        className="mb-2 w-100 mt-3"
                    ),
                ])
            ]),
            
            # Individual Selection and Statistics
            dbc.Card([
                dbc.CardHeader("Individual Selection"),
                dbc.CardBody([
                    html.P("Select Individuals:"),
                    dcc.Dropdown(
                        id="map-individual-select",
                        multi=True,
                        className="mb-3"
                    ),
                    
                    html.Div([
                        html.H6("Selected Individual Stats", className="mt-3"),
                        html.Div(id="selected-individual-stats")
                    ], id="individual-stats-container")
                ])
            ], className="mt-3")
        ], width=3),
        
        # Main map area
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("GPS Tracking Map"), width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button(html.I(className="fas fa-expand-arrows-alt"), 
                                          id="fullscreen-map-btn", 
                                          color="light", 
                                          size="sm",
                                          className="me-1"),
                                dbc.Button(html.I(className="fas fa-home"), 
                                          id="reset-view-btn", 
                                          color="light", 
                                          size="sm",
                                          className="me-1"),
                                dbc.Button(html.I(className="fas fa-download"), 
                                          id="download-map-btn", 
                                          color="light", 
                                          size="sm"),
                            ])
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Graph(
                        id="movement-map",
                        config={
                            'scrollZoom': True,
                            'displayModeBar': True,
                            'modeBarButtonsToAdd': ['drawrect', 'eraseshape'],
                        },
                        style={'height': '700px'}
                    )
                ])
            ]),
            
            # Time slider at bottom of map
            dbc.Card([
                dbc.CardBody([
                    dcc.RangeSlider(
                        id="date-filter-slider",
                        min=0,
                        max=100,
                        step=1,
                        value=[0, 100],
                        marks={},
                        className="mb-1"
                    ),
                    html.Div(id="date-range-display", className="text-center text-muted")
                ])
            ], className="mt-3")
        ], width=9)
    ]),
    
    # Analysis results section (hidden initially, shown after map interaction)
    html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Path Analysis"),
                    dbc.CardBody([
                        html.Div(id="path-analysis-content")
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Environmental Context"),
                    dbc.CardBody([
                        html.Div(id="environmental-context-content")
                    ])
                ])
            ], width=6)
        ])
    ], id="map-analysis-section", style={"display": "none", "marginTop": "20px"}),
    
    # Hidden components to store state
    dcc.Store(id="map-data-store"),
    dcc.Store(id="map-state-store"),
    dcc.Store(id="map-timestamps-store"),
    dcc.Store(id="selected-area-store")
])

# Callbacks will be defined in app.py to avoid circular imports
