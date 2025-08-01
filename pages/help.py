"""
Help Page
Provides documentation, tutorials, and information about the dashboard
"""

import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc

# Create help layout with documentation, FAQs, and tutorials
layout = html.Div([
    # Page header
    html.Div([
        html.H2("Help & Documentation", className="page-title"),
        html.P("Learn how to use the Carnivore GPS Tracking Dashboard", 
               className="page-subtitle")
    ], className="page-header"),
    
    # Main content
    dbc.Row([
        # Left column - Navigation and sections
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Documentation Sections"),
                dbc.CardBody([
                    dbc.Nav(
                        [
                            dbc.NavItem(dbc.NavLink("Getting Started", href="#getting-started", id="getting-started-link", active=True)),
                            dbc.NavItem(dbc.NavLink("Data Import", href="#data-import", id="data-import-link")),
                            dbc.NavItem(dbc.NavLink("Map Visualizations", href="#map-visualizations", id="map-link")),
                            dbc.NavItem(dbc.NavLink("Movement Analysis", href="#movement-analysis", id="movement-link")),
                            dbc.NavItem(dbc.NavLink("Home Range Analysis", href="#home-range", id="home-range-link")),
                            dbc.NavItem(dbc.NavLink("Behavioral Patterns", href="#behavioral", id="behavioral-link")),
                            dbc.NavItem(dbc.NavLink("Environmental Context", href="#environmental", id="environmental-link")),
                            dbc.NavItem(dbc.NavLink("Data Quality", href="#data-quality", id="quality-link")),
                            dbc.NavItem(dbc.NavLink("FAQs", href="#faqs", id="faqs-link")),
                            dbc.NavItem(dbc.NavLink("About & Credits", href="#about", id="about-link")),
                        ],
                        vertical=True,
                        pills=True,
                    ),
                    
                    html.Hr(),
                    
                    html.P("Need more help?"),
                    dbc.Button(
                        "Contact Support",
                        id="contact-support-btn",
                        color="info",
                        className="w-100"
                    ),
                    
                    html.Div([
                        html.P("Dashboard Version: 1.0.0", className="mt-3 text-muted small")
                    ])
                ])
            ])
        ], width=3),
        
        # Right column - Documentation content
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    # Getting Started Section
                    html.Div([
                        html.H3("Getting Started", className="anchor-offset", id="getting-started"),
                        html.Hr(),
                        
                        html.H5("Welcome to the Carnivore GPS Tracking Dashboard", className="mt-4"),
                        html.P([
                            "This dashboard provides comprehensive tools for analyzing GPS tracking data from carnivore species. ",
                            "The application integrates with Movebank's extensive tracking database and offers advanced analytical ",
                            "capabilities for ecological and behavioral insights."
                        ]),
                        
                        html.H5("Dashboard Layout", className="mt-4"),
                        html.P([
                            "The dashboard is organized into several main sections, accessible from the sidebar navigation:"
                        ]),
                        
                        html.Ul([
                            html.Li(html.Strong("Dashboard Overview: "), "Summary view with key metrics and visualizations"),
                            html.Li(html.Strong("Data Import: "), "Connect to Movebank and import tracking data"),
                            html.Li(html.Strong("Map Visualization: "), "Interactive maps with multiple layers and analyses"),
                            html.Li(html.Strong("Movement Analysis: "), "Detailed metrics on movement patterns and distances"),
                            html.Li(html.Strong("Home Range Analysis: "), "Calculate and visualize home range estimations"),
                            html.Li(html.Strong("Behavioral Patterns: "), "Analyze activity cycles and behavioral insights"),
                            html.Li(html.Strong("Environmental Context: "), "Explore habitat use and environmental factors"),
                            html.Li(html.Strong("Data Quality: "), "Assess GPS fix success and data reliability")
                        ]),
                        
                        html.H5("Quick Start Guide", className="mt-4"),
                        html.Ol([
                            html.Li("Begin by authenticating with Movebank in the Data Import section"),
                            html.Li("Select studies and individuals of interest"),
                            html.Li("Apply filters for date ranges if needed"),
                            html.Li("Import data to begin analysis"),
                            html.Li("Navigate to specific analysis pages using the sidebar menu"),
                            html.Li("Use the Dashboard Overview to see summarized insights")
                        ]),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader(html.H6("Tip: Data Caching", className="m-0")),
                                    dbc.CardBody([
                                        html.P([
                                            "Once data is imported, it is cached locally for faster access. ",
                                            "You can clear the cache and reset all data by clicking the 'Reset' ",
                                            "button in the Data Import section."
                                        ], className="mb-0")
                                    ])
                                ], color="light")
                            ], width=12)
                        ], className="mt-3 mb-4")
                    ], id="getting-started-section"),
                    
                    # Data Import Section
                    html.Div([
                        html.H3("Data Import", className="anchor-offset", id="data-import"),
                        html.Hr(),
                        
                        html.H5("Connecting to Movebank", className="mt-4"),
                        html.P([
                            "This dashboard uses the Movebank API to access tracking data. ",
                            "You'll need a Movebank account to access most datasets. Some public datasets ",
                            "may be available without authentication."
                        ]),
                        
                        html.H5("Authentication Process", className="mt-4"),
                        html.Ol([
                            html.Li("Enter your Movebank username and password in the authentication section"),
                            html.Li("Click 'Authenticate' to establish a connection"),
                            html.Li("Once connected, you'll see a list of available studies"),
                            html.Li("For license-restricted studies, you'll need to accept the license terms")
                        ]),
                        
                        html.H5("Selecting Data", className="mt-4"),
                        html.P([
                            "After authentication, you can browse and select studies and individuals:"
                        ]),
                        html.Ul([
                            html.Li("Search for studies by name or filter by species"),
                            html.Li("Select one or multiple studies for analysis"),
                            html.Li("Choose specific individuals within each study"),
                            html.Li("Apply date filters to focus on specific time periods"),
                            html.Li("Preview data before importing")
                        ]),
                        
                        html.H5("Data Types", className="mt-4"),
                        html.P([
                            "The dashboard works with the following data types from Movebank:"
                        ]),
                        html.Ul([
                            html.Li(html.Strong("GPS coordinates: "), "Latitude, longitude, and timestamp data"),
                            html.Li(html.Strong("Deployment metadata: "), "Information about tracked animals and devices"),
                            html.Li(html.Strong("Environmental data: "), "Associated environmental measurements when available"),
                            html.Li(html.Strong("Sensor data: "), "Additional sensor readings like acceleration, temperature, etc.")
                        ]),
                        
                        dbc.Alert([
                            html.H6("Note about Data Licenses", className="alert-heading"),
                            html.P([
                                "Many Movebank datasets have specific license restrictions. When importing data, ",
                                "you'll be required to accept the license terms. Please respect data usage terms ",
                                "and provide appropriate attribution when using the data."
                            ], className="mb-0")
                        ], color="info", className="mt-4")
                    ], id="data-import-section", style={"display": "none"}),
                    
                    # Additional documentation sections would be implemented similarly
                    # Map Visualizations, Movement Analysis, Home Range, Behavioral Patterns, 
                    # Environmental Context, Data Quality, FAQs, and About sections
                    # For brevity, only showing placeholder divs here
                    
                    html.Div(id="map-visualizations-section", style={"display": "none"}),
                    html.Div(id="movement-analysis-section", style={"display": "none"}),
                    html.Div(id="home-range-section", style={"display": "none"}),
                    html.Div(id="behavioral-section", style={"display": "none"}),
                    html.Div(id="environmental-section", style={"display": "none"}),
                    html.Div(id="data-quality-section", style={"display": "none"}),
                    
                    # FAQs Section
                    html.Div([
                        html.H3("Frequently Asked Questions", className="anchor-offset", id="faqs"),
                        html.Hr(),
                        
                        dbc.Accordion([
                            dbc.AccordionItem([
                                html.P([
                                    "The dashboard requires Python 3.8+ and several packages including Dash, ",
                                    "Plotly, Pandas, and others. All dependencies are listed in the requirements.txt ",
                                    "file. Use pip to install: ", html.Code("pip install -r requirements.txt")
                                ])
                            ], title="What are the system requirements?"),
                            
                            dbc.AccordionItem([
                                html.P([
                                    "Yes, you need a Movebank account to access most datasets. ",
                                    "You can create a free account at ", 
                                    html.A("Movebank.org", href="https://www.movebank.org/", target="_blank"),
                                    ". Some public datasets may be available without authentication."
                                ])
                            ], title="Do I need a Movebank account?"),
                            
                            dbc.AccordionItem([
                                html.P([
                                    "The dashboard stores cached data locally in a 'cache' directory. ",
                                    "No data is sent to external servers. Your Movebank credentials are used ",
                                    "only to authenticate with Movebank and are not stored permanently."
                                ])
                            ], title="Is my data secure?"),
                            
                            dbc.AccordionItem([
                                html.P([
                                    "The MCP method creates the smallest convex polygon containing all (or a percentage of) ",
                                    "GPS locations. KDE uses a probability density function to estimate the intensity of ",
                                    "space use. MCP is simpler but more affected by outliers, while KDE provides a more ",
                                    "nuanced view of space use but requires parameter tuning."
                                ])
                            ], title="What's the difference between MCP and KDE home range methods?"),
                            
                            dbc.AccordionItem([
                                html.P([
                                    "From any analysis page, look for the download or export button (usually in the ",
                                    "top right of charts or tables). You can export data in various formats including ",
                                    "CSV, GeoJSON (for spatial data), and PNG/SVG for visualizations."
                                ])
                            ], title="How do I export my analysis results?"),
                            
                            dbc.AccordionItem([
                                html.P([
                                    "The 'Data Quality' page provides comprehensive metrics on GPS fix success rates, ",
                                    "data gaps, and potential outliers. Use these metrics to assess data reliability ",
                                    "before drawing conclusions from your analyses."
                                ])
                            ], title="How can I assess the quality of my tracking data?")
                        ], start_collapsed=True, className="mt-4"),
                        
                    ], id="faqs-section", style={"display": "none"}),
                    
                    # About Section
                    html.Div([
                        html.H3("About & Credits", className="anchor-offset", id="about"),
                        html.Hr(),
                        
                        html.H5("About This Project", className="mt-4"),
                        html.P([
                            "The Carnivore GPS Tracking Dashboard was developed to provide ecologists, conservationists, ",
                            "and wildlife researchers with powerful tools to analyze and visualize movement data from ",
                            "GPS-collared carnivores. The dashboard aims to make advanced movement ecology analytics ",
                            "more accessible through an intuitive interface."
                        ]),
                        
                        html.H5("Technologies", className="mt-4"),
                        html.P("This dashboard is built with the following technologies:"),
                        html.Ul([
                            html.Li(html.Strong("Python: "), "Core programming language"),
                            html.Li(html.Strong("Dash & Plotly: "), "Interactive visualization framework"),
                            html.Li(html.Strong("Pandas & GeoPandas: "), "Data manipulation and analysis"),
                            html.Li(html.Strong("Dash Bootstrap Components: "), "UI components"),
                            html.Li(html.Strong("Movebank API: "), "Data source integration")
                        ]),
                        
                        html.H5("Acknowledgments", className="mt-4"),
                        html.P([
                            "We would like to thank the Movebank team for providing access to their API and extensive ",
                            "tracking database. We also acknowledge the countless researchers who have contributed ",
                            "tracking data to Movebank, enabling valuable insights into wildlife movement patterns."
                        ]),
                        
                        html.H5("Contact", className="mt-4"),
                        html.P([
                            "For questions, bug reports, or feature requests, please contact support at ",
                            html.A("support@carnivoregpstracking.org", href="mailto:support@carnivoregpstracking.org")
                        ]),
                        
                        html.H5("License", className="mt-4"),
                        html.P([
                            "This dashboard is open source software, licensed under the MIT License. ",
                            "See the LICENSE file for more information."
                        ])
                    ], id="about-section", style={"display": "none"})
                ])
            ])
        ], width=9)
    ])
])

# Simple callbacks for showing/hiding sections - will be implemented in app.py
# This would typically involve setting the display style of each section div
# based on which nav link is clicked
