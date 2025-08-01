"""
Environmental Context Page
Analyzes carnivore movement in relation to environmental features and habitat types
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

# Create environmental context layout with habitat analysis, proximity metrics, and terrain profile
layout = html.Div([
    # Page header
    html.Div([
        html.H2("Environmental Context", className="page-title"),
        html.P("Analyze relationships between carnivore movements and environmental features", 
               className="page-subtitle")
    ], className="page-header"),
    
    # Main content
    dbc.Row([
        # Left column - Habitat overlay and analysis
        dbc.Col([
            # Habitat Map Card
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("Habitat Overlay Map"), width="auto"),
                        dbc.Col([
                            dcc.Dropdown(
                                id="habitat-layer-dropdown",
                                options=[
                                    {"label": "Land Cover", "value": "landcover"},
                                    {"label": "Vegetation", "value": "vegetation"},
                                    {"label": "Protected Areas", "value": "protected"},
                                    {"label": "Water Bodies", "value": "water"},
                                    {"label": "Terrain", "value": "terrain"}
                                ],
                                value="landcover",
                                clearable=False,
                                style={"width": "150px"}
                            )
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dcc.Graph(
                        id="habitat-map",
                        config={
                            'scrollZoom': True,
                            'displayModeBar': True,
                        },
                        style={'height': '400px'}
                    )
                ])
            ], className="mb-4"),
            
            # Habitat Usage Card
            dbc.Card([
                dbc.CardHeader("Habitat Type Usage"),
                dbc.CardBody([
                    dbc.Row([
                        # Habitat usage chart
                        dbc.Col([
                            dcc.Graph(
                                id="habitat-usage-chart",
                                config={'displayModeBar': False},
                                style={'height': '300px'}
                            )
                        ], width=12)
                    ])
                ])
            ])
        ], width=6),
        
        # Right column - Proximity and elevation analysis
        dbc.Col([
            # Environmental Features Card
            dbc.Card([
                dbc.CardHeader("Proximity to Environmental Features"),
                dbc.CardBody([
                    # Feature selection
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Features:"),
                            dbc.Checklist(
                                options=[
                                    {"label": "Water Sources", "value": "water"},
                                    {"label": "Roads", "value": "roads"},
                                    {"label": "Settlements", "value": "settlements"},
                                    {"label": "Protected Areas", "value": "protected"}
                                ],
                                value=["water", "roads"],
                                id="proximity-features-checklist",
                                inline=True,
                                className="mb-3"
                            )
                        ], width=12)
                    ]),
                    
                    # Proximity chart
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(
                                id="proximity-chart",
                                config={'displayModeBar': True},
                                style={'height': '300px'}
                            )
                        ], width=12)
                    ])
                ])
            ], className="mb-4"),
            
            # Elevation Profile Card
            dbc.Card([
                dbc.CardHeader("Elevation Profile"),
                dbc.CardBody([
                    dbc.Row([
                        # Elevation profile chart
                        dbc.Col([
                            dcc.Graph(
                                id="elevation-profile",
                                config={'displayModeBar': True},
                                style={'height': '300px'}
                            )
                        ], width=12)
                    ])
                ])
            ])
        ], width=6)
    ]),
    
    # Bottom row - Environmental statistics and metrics
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Environmental Statistics"),
                dbc.CardBody([
                    dbc.Row([
                        # Elevation stats
                        dbc.Col([
                            html.H6("Elevation Range", className="stat-header"),
                            html.Div([
                                html.H4(id="elevation-range-stat", className="stat-value"),
                                html.P("meters (min-max)", className="stat-label")
                            ], className="stat-container")
                        ], width=3),
                        
                        # Dominant habitat
                        dbc.Col([
                            html.H6("Dominant Habitat", className="stat-header"),
                            html.Div([
                                html.H4(id="dominant-habitat-stat", className="stat-value"),
                                html.P("% of locations", className="stat-label")
                            ], className="stat-container")
                        ], width=3),
                        
                        # Water proximity
                        dbc.Col([
                            html.H6("Water Proximity", className="stat-header"),
                            html.Div([
                                html.H4(id="water-proximity-stat", className="stat-value"),
                                html.P("avg. distance (km)", className="stat-label")
                            ], className="stat-container")
                        ], width=3),
                        
                        # Human influence
                        dbc.Col([
                            html.H6("Human Influence", className="stat-header"),
                            html.Div([
                                html.H4(id="human-influence-stat", className="stat-value"),
                                html.P("index (0-100)", className="stat-label")
                            ], className="stat-container")
                        ], width=3)
                    ])
                ])
            ])
        ], width=12)
    ], className="mt-4"),
    
    # Settings and data sources row
    dbc.Row([
        # Analysis settings
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Analysis Settings"),
                dbc.CardBody([
                    dbc.Row([
                        # Proximity threshold
                        dbc.Col([
                            html.Label("Proximity Threshold (km):"),
                            dcc.Slider(
                                id="proximity-threshold",
                                min=0.1,
                                max=10,
                                step=0.1,
                                value=1.0,
                                marks={i: str(i) for i in range(0, 11, 2)},
                                className="mb-2"
                            )
                        ], width=6),
                        
                        # Habitat resolution
                        dbc.Col([
                            html.Label("Habitat Data Resolution:"),
                            dbc.Select(
                                id="habitat-resolution",
                                options=[
                                    {"label": "High (30m)", "value": "high"},
                                    {"label": "Medium (100m)", "value": "medium"},
                                    {"label": "Low (300m)", "value": "low"}
                                ],
                                value="medium",
                                className="mb-2"
                            )
                        ], width=6)
                    ]),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "Update Environmental Analysis",
                                id="update-environmental-btn",
                                color="primary",
                                className="w-100"
                            )
                        ], width=12)
                    ])
                ])
            ])
        ], width=6),
        
        # Data sources
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Environmental Data Sources"),
                dbc.CardBody([
                    html.Ul([
                        html.Li([
                            html.Strong("Land Cover: "),
                            "MODIS Land Cover Type (MCD12Q1)"
                        ]),
                        html.Li([
                            html.Strong("Elevation: "),
                            "SRTM Digital Elevation Model"
                        ]),
                        html.Li([
                            html.Strong("Water Bodies: "),
                            "Global Surface Water Dataset"
                        ]),
                        html.Li([
                            html.Strong("Protected Areas: "),
                            "World Database on Protected Areas (WDPA)"
                        ]),
                        html.Li([
                            html.Strong("Human Influence: "),
                            "Human Footprint Index"
                        ])
                    ])
                ])
            ])
        ], width=6)
    ], className="mt-4"),
    
    # Hidden components to store state
    dcc.Store(id="environmental-data-store"),
    dcc.Store(id="habitat-data-store"),
    dcc.Store(id="elevation-data-store")
])

# Callbacks will be defined in app.py to avoid circular imports
