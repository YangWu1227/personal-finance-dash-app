import os
import sqlite3
from typing import List
import logging
import sys
import pandas as pd

def get_categories(db_path: str) -> List[str]:
    """
    Reads the categories from the database and returns them as a list.
    
    Parameters
    ----------
    db_path : str
        The path to the database.
        
    Returns
    -------
    List[str]
        The list of categories.
    """
    with sqlite3.connect(db_path) as conn:
        categories = pd.read_sql_query('SELECT category_name FROM categories', conn)
    return categories['category_name'].tolist()

def add_category_to_db(category_name: str, db_path: str) -> None:
    """
    Adds a new category to the database.
    
    Parameters
    ----------
    category_name : str
        The name of the category to be added.
    db_path : str
        The path to the database.
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO categories (category_name) VALUES (?)", (category_name,))
        
def read_spending_data(db_path: str) -> pd.DataFrame:
    """
    Reads the spending data from the database and returns it as a pandas DataFrame.
    
    Parameters
    ----------
    db_path : str
        The path to the database. 
        
    Returns
    -------
    pd.DataFrame
        The spending data.
    """
    with sqlite3.connect(db_path) as conn:
        spending_data = pd.read_sql_query(
            sql='SELECT * FROM spending', 
            con=conn, 
            index_col='id',
            parse_dates='timestamp'
        )
    return spending_data

def main():
    
    logger = logging.getLogger(__name__)
    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.info('Creating database...')
    
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db')
    with sqlite3.connect(os.path.join(db_dir, 'spending.db')) as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS spending (id INTEGER PRIMARY KEY, amount INTEGER, category TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        cursor.execute('CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, category_name TEXT)')
    conn.close()
    
    logger.info('Database created successfully!')
    
    return 0

if __name__ == '__main__':
    
    main()
    