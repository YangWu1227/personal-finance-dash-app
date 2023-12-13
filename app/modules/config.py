import os
from modules.database import get_categories

# Global configuration variables
db_path =  os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'spending.db')