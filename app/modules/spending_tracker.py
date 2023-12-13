import sqlite3
from typing import Union, List, Dict, Tuple

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

from modules.database import get_categories, add_category_to_db
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
    updated_dropdown_options = [{'label': cat, 'value': cat} for cat in updated_categories] + [{'label': 'Add new', 'value': 'ADD_NEW'}]
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Input(id='spending_amount', type='number', placeholder='Amount', className='mb-2'),
                        dcc.Dropdown(
                            id='category_dropdown',
                            options=updated_dropdown_options,
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
        add_category_modal
        ], fluid=True)
    
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
        [Output('category_dropdown', 'options'), Output('new_category_input', 'value'), Output('alert-container', 'children')],
        [Input('add_new_category_button', 'n_clicks')],
        [State('new_category_input', 'value')],
        prevent_initial_call=True
    )
    def update_category_dropdown(n_clicks: Union[int, None], new_category: str) -> Tuple[List[Dict[str, str]], str, dbc.Alert]:
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
        Tuple[List[Dict[str, str]], str, dbc.Alert]
            The updated options for the dropdown, the value of the new category input, and the alert to be displayed.
        """
        if n_clicks is None or not new_category:
            return dash.no_update, '', None

        if not new_category.isalnum():
            return dash.no_update, '', dbc.Alert('Invalid category name.', color='warning')

        add_category_to_db(category_name=new_category, db_path=db_path)
        updated_categories = get_categories(db_path=db_path)
        updated_options = [{'label': cat, 'value': cat} for cat in updated_categories] + [{'label': 'Add new', 'value': 'ADD_NEW'}]

        return updated_options, '', dbc.Alert(f'Category "{new_category}" added successfully!', color='success')

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