import sqlite3
from typing import Union, List, Dict, Tuple

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from modules.database import get_categories, add_category_to_db, read_spending_data
from modules.config import db_path

# ----------------------------------- Modal ---------------------------------- #

add_category_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle('Add New Category')),
        dbc.ModalBody(
            dcc.Input(id='new_category_input', type='text', placeholder='New Category Name')
        ),
        dbc.ModalFooter(
            dbc.Button('Add', id='add_new_category_button', className='ms-auto', n_clicks=0)
        ),
    ],
    id='modal_new_category',
    is_open=False
)

# ---------------------------------- Layout ---------------------------------- #

def layout() -> dbc.Container:
    """ 
    Returns the layout for the spending tracker module. This function is called each time the '/spending-tracker' route is accessed.
    
    Returns
    -------
    dbc.Container
        The layout for the spending tracker module.
    """
    # Fetch the latest categories directly from the database
    updated_categories = get_categories(db_path=db_path)
    updated_dropdown_options = [{'label': cat, 'value': cat} for cat in updated_categories]
    updated_dropdown_options_with_add_new = updated_dropdown_options + [{'label': 'Add new', 'value': 'ADD_NEW'}]

    
    return dbc.Container([
        
        # --------------------------- Add new category Card -------------------------- #
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Input(id='spending_amount', type='number', placeholder='Amount', className='mb-2'),
                        dcc.Dropdown(
                            id='category_dropdown',
                            options=updated_dropdown_options_with_add_new,
                            placeholder='Select a category',
                            searchable=True
                        ),
                        dbc.Button('Submit', id='submit_button', color='success', className='mt-2'),
                    ]),
                ]),
            ], width={'size': 6, 'offset': 3}),
        ]),
        dbc.Row([
            dbc.Col(html.Div(id='alert-container'), width=12),
        ]),
        dbc.Row([
            dbc.Col(html.Div(id='output-container'), width=12)
        ]),
        
        # ------------------------------- Plotting card ------------------------------ #
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Monthly Trends'),
                    dbc.CardBody([
                        dcc.Dropdown(
                            id='monthly_trend_dropdown',
                            options=updated_dropdown_options,
                            placeholder='Select a category',
                            searchable=True,
                            multi=True
                        ),
                        dcc.Graph(id='monthly_trend_graph')
                    ])
                ]),
            ], width=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Weekly Trends'),
                    dbc.CardBody([
                        dcc.Dropdown(
                            id='weekly_trend_dropdown',
                            options=updated_dropdown_options,
                            placeholder='Select a category',
                            searchable=True,
                            multi=True
                        ),
                        dcc.Graph(id='weekly_trend_graph')
                    ])
                ]),
            ], width=6),
        ]),
        
        dcc.Store(id='spending_data_store'),
        
        add_category_modal
        ], fluid=True)
    
# --------------------------------- Utilities -------------------------------- #

def prepare_trend_data(spending_data: pd.DataFrame, selected_category: str, freq: str) -> pd.DataFrame:
    """
    Prepares the spending data for plotting trends based on a given frequency.

    Parameters
    ----------
    spending_data : pd.DataFrame
        The spending data DataFrame.
    selected_category : str
        The selected category for which the trend is to be plotted.
    freq : str
        The frequency for resampling ('W' for weekly, 'M' for monthly).

    Returns
    -------
    pd.DataFrame
        The prepared DataFrame ready for plotting.
    """
    # Convert timestamp to datetime (if not already done)
    spending_data['timestamp'] = pd.to_datetime(spending_data['timestamp'])

    # Filter data for the selected category
    filtered_data = spending_data[spending_data['category'] == selected_category]

    # Set timestamp as index temporarily for resampling
    filtered_data = filtered_data.set_index('timestamp')
    resampled_data = filtered_data.resample(freq).sum().reset_index()

    # Create a complete range of periods
    full_range = pd.date_range(start=resampled_data['timestamp'].min(), end=resampled_data['timestamp'].max(), freq=freq)
    full_range = pd.DataFrame(full_range, columns=['timestamp'])

    # Merge with the full range to include periods with no data
    merged_data = pd.merge(full_range, resampled_data, on='timestamp', how='left')
    merged_data['amount'].fillna(0, inplace=True)  # Replace NaN with 0
    merged_data['category'] = selected_category  # Set category for all rows

    return merged_data

def update_trend_graph(selected_categories: List[str], stored_data: Union[List[Dict[str, str]], None], freq: str) -> go.Figure:
    """
    Generates a trend graph based on the selected categories and frequency.

    Parameters
    ----------
    selected_categories : List[str]
        The list of selected categories.
    stored_data : Union[List[Dict[str, str]], None]
        The stored spending data in JSON format.
    freq : str
        The frequency for the trend graph ('M' for monthly, 'W' for weekly).

    Returns
    -------
    go.Figure
        The generated trend graph.
    """
    if stored_data is None or not selected_categories:
        return go.Figure()

    spending_data = pd.DataFrame(stored_data)
    fig = go.Figure()

    for category in selected_categories:
        prepared_data = prepare_trend_data(spending_data, category, freq=freq)
        fig.add_trace(go.Scatter(x=prepared_data['timestamp'], y=prepared_data['amount'], mode='lines', name=category))

    title = 'Monthly Trends' if freq == 'M' else 'Weekly Trends'
    xaxis_title = 'Month' if freq == 'M' else 'Week'
    fig.update_layout(title=title, xaxis_title=xaxis_title, yaxis_title='Amount')

    return fig
    
# --------------------------------- Callbacks -------------------------------- #

def register_callbacks(app: dash.Dash) -> None:
    """
    Registers the callbacks for the spending tracker module.
    
    Parameters
    ----------
    app : dash.Dash
        The Dash app to which the callbacks will be registered.
    """
    # Callback for toggling the modal
    @app.callback(
        Output('modal_new_category', 'is_open'),
        [Input('category_dropdown', 'value')],
        [State('modal_new_category', 'is_open')]
    )
    def toggle_modal(selected_value: Union[str, None], is_open: bool) -> bool:
        """
        This callback toggles the modal for adding a new category.
        
        Parameters
        ----------
        selected_value : Union[str, None]
            The value of the selected option in the dropdown.
        is_open : bool
            The current state of the modal.
            
        Returns
        -------
        bool
            The updated state of the modal. 
        """
        if selected_value and 'ADD_NEW' in selected_value:
            return True
        return is_open

    # Callback for both populating and updating the category dropdown
    @app.callback(
        [
            Output('category_dropdown', 'options'),
            Output('monthly_trend_dropdown', 'options'),
            Output('weekly_trend_dropdown', 'options'),
            Output('new_category_input', 'value'),
            Output('alert-container', 'children')
        ],
        [Input('add_new_category_button', 'n_clicks')],
        [State('new_category_input', 'value')],
        prevent_initial_call=True
    )
    def update_category_dropdown(n_clicks: Union[int, None], new_category: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]], str, dbc.Alert]:
        """
        This callback updates the category dropdown with the categories from the database.
        
        Parameters
        ----------
        n_clicks : Union[int, None]
            The number of times the button has been clicked.
        new_category : str
            The name of the new category to be added.
            
        Returns
        -------
        Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]], str, dbc.Alert]
            The updated options for the dropdowns, the value of the new category input, and the alert to be displayed.
        """
        if n_clicks is None or not new_category:
            return dash.no_update, dash.no_update, dash.no_update, '', None

        if not new_category.isalnum():
            return dash.no_update, dash.no_update, dash.no_update, '', dbc.Alert('Invalid category name.', color='warning')

        add_category_to_db(category_name=new_category, db_path=db_path)
        updated_categories = get_categories(db_path=db_path)
        updated_options = [{'label': cat, 'value': cat} for cat in updated_categories]

        # For category_dropdown, include 'Add new' option
        updated_options_with_add_new = updated_options + [{'label': 'Add new', 'value': 'ADD_NEW'}]

        return updated_options_with_add_new, updated_options, updated_options, '', dbc.Alert(f'Category "{new_category}" added successfully!', color='success')

    # Callback for submitting spending data
    @app.callback(
        Output('output-container', 'children'),
        [Input('submit_button', 'n_clicks')],
        [State('spending_amount', 'value'),
        State('category_dropdown', 'value')]
    )
    def update_output(n_clicks: Union[int, None], amount: Union[int, float, None], category: Union[str, None]) -> dbc.Alert:
        """
        This callback updates the output container with the amount and category of the spending.
        
        Parameters
        ----------
        n_clicks : Union[int, None]
            The number of times the button has been clicked.
        amount : Union[int, float, None]
            The amount of the spending.
        category : Union[str, None]
            The category of the spending.
            
        Returns
        -------
        dbc.Alert
            The alert to be displayed in the output container.
        """
        if n_clicks is None:
            return dash.no_update
        
        if n_clicks > 0:
            if amount is None or category is None:
                return dbc.Alert('Please enter a valid amount and select a category', color='danger', duration=3000)
            else:
                try:
                    conn = sqlite3.connect(db_path)
                    c = conn.cursor()
                    c.execute('INSERT INTO spending (amount, category) VALUES (?, ?)', (amount, category))
                    conn.commit()
                except sqlite3.Error as e:
                    return dbc.Alert(f'Database error: {e}', color='danger', duration=3000)
                finally:
                    conn.close()
                return dbc.Alert(f'Amount: {amount}, Category: {category} added successfully!', color='success', duration=3000)
        return dbc.Alert('Enter amount and select a category', color='warning', duration=3000)
    
    # Callback to load spending data into dcc.Store
    @app.callback(
        Output('spending_data_store', 'data'),
        [Input('url', 'pathname')]  # Assuming you have a dcc.Location component with id='url'
    )
    def load_spending_data(pathname: str) -> Union[Dict[str, str], None]:
        """
        Callback to load the spending data into dcc.Store.
        
        Parameters
        ----------
        pathname : str
            The URL path.
            
        Returns
        -------
        Union[Dict[str, str], None]
            The spending data in dictionary format. 
        """
        if pathname == '/spending-tracker':  # Update the path as per your app's URL structure
            spending_data = read_spending_data(db_path)
            return spending_data.to_dict('records')  # Convert DataFrame to a dictionary for storage
        return dash.no_update
    
    # Callback for updating the monthly trend graph
    @app.callback(
        Output('monthly_trend_graph', 'figure'),
        [Input('monthly_trend_dropdown', 'value')],
        [State('spending_data_store', 'data')]
    )
    def update_monthly_trend(selected_categories, stored_data):
        return update_trend_graph(selected_categories, stored_data, freq='M')

    # Callback for updating the weekly trend graph
    @app.callback(
        Output('weekly_trend_graph', 'figure'),
        [Input('weekly_trend_dropdown', 'value')],
        [State('spending_data_store', 'data')]
    )
    def update_weekly_trend(selected_categories, stored_data):
        return update_trend_graph(selected_categories, stored_data, freq='W')