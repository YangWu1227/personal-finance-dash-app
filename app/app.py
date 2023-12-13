import sqlite3
import os
import json
from datetime import datetime
from typing import Union, List, Dict, Tuple, Any

import pandas as pd

import dash
from dash import html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc

from modules.spending_tracker import layout as spending_tracker_layout, register_callbacks as register_spending_tracker_callbacks

# --------------------------------- App setup -------------------------------- #

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
app.title = 'Personal Finance Dashboard'
server = app.server
app.config.suppress_callback_exceptions = True

register_spending_tracker_callbacks(app)

# ---------------------------------- Sidebar --------------------------------- #

sidebar = dbc.Col(
    [
        html.H2('Modules', className='display-4', style={'font-size': '2rem'}),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink('Spending Tracker', href='/spending-tracker', active='exact'),
                dbc.NavLink('Place Holder', href='/place-holder', active='exact'),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    id='sidebar'
)

# ---------------------------------- Navbar ---------------------------------- #

top_navbar = dbc.NavbarSimple(
    children=[
        dbc.Button('Toggle Sidebar', id='sidebar-toggle', className='me-2'),
    ],
    brand='Personal Finance Dashboard',
    brand_href='#',
    color='primary',
    dark=True,
    id='top-navbar'
)

# ---------------------------------- Content --------------------------------- #

content = html.Div(id='page-content')

# ---------------------------------- Layout ---------------------------------- #

app.layout = html.Div(
    [
        dcc.Location(id='url'),
        top_navbar,  # Navbar at the top
        html.Div([
            sidebar,  # Sidebar below navbar
            content
        ], id='below-nav')  # Container for sidebar and content
    ]
)

# --------------------------------- Callbacks -------------------------------- #

@app.callback(
    [Output('sidebar', 'style'), Output('below-nav', "style"), Output('top-navbar', 'style')],
    [Input('sidebar-toggle', 'n_clicks')],
    [State('sidebar', 'style'), State('below-nav', 'style'), State('top-navbar', 'style')],
    prevent_initial_call=False
)
def toggle_sidebar(n, sidebar_style: Dict[str, str], below_nav_style: Dict[str, str], navbar_style: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """
    Callback to toggle the sidebar and adjust navbar and content accordingly.
    
    Parameters
    ----------
    n : int
        Number of times the toggle button has been clicked.
    sidebar_style : Dict[str, str]
        Style of the sidebar.
    below_nav_style : Dict[str, str]
        Style of the container below the navbar.
    navbar_style : Dict[str, str]
        Style of the navbar.
        
    Returns
    -------
    Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]
        Tuple containing the new styles for the sidebar, container below navbar, and navbar.
    """
    if n and (n % 2 == 1):  # If the number of clicks is odd, hide the sidebar
        sidebar_style = {'display': 'none'}
        below_nav_style = {'margin-left': '0', 'margin-right': '2rem', 'padding': '2rem 1rem'}
        navbar_style = {'width': '100%', 'margin-left': '0'}
    else:  # If the number of clicks is even, show the sidebar
        sidebar_style = {'position': 'fixed', 'top': 0, 'left': 0, 'bottom': 0, 'width': '16rem', 'padding': '2rem 1rem', 'background-color': '#f8f9fa'}
        below_nav_style = {'margin-left': '16rem', 'margin-right': '2rem', 'padding': '2rem 1rem'}
        navbar_style = {'width': 'calc(100% - 16rem)', 'margin-left': '16rem'}
    return sidebar_style, below_nav_style, navbar_style

# Callback for dynamic page content
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def render_page_content(pathname: str) -> Union[html.Div, dbc.Container]:
    """
    Callback to render the content of the page based on the URL.
    
    Parameters
    ----------
    pathname : str
        URL path.
        
    Returns
    -------
    Union[html.Div, dbc.Container]
        Content of the page.
    """
    if pathname == '/spending-tracker':
        return spending_tracker_layout()
    elif pathname == '/place-holder':
        return dbc.Container([
            html.H1('PlaceHolder', className='text-center mb-4'),
        ], fluid=True)

if __name__ == '__main__':
    
    app.run_server(debug=True)
    