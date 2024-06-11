"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier est le fichier principale du backend.
Version de Python: 3.12
"""

# Import libraires
from dotenv import load_dotenv
import os

# Files from the backend
import database.connection as db
import config
from backend.database import setup as setup

# Charge environment variables
load_dotenv(dotenv_path='.env')

# Fetch environment & config variable
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = config.database_name
app_version = config.version

# Test connection to the database
test_connection = db.test_connection(db_host=db_host, db_user=db_user, db_password=db_password, db_name=db_name)

# Case if connection is OK
if test_connection == True:
    print(f"Connected to MySQL, database \"{db_name}\" exists")
# Case if table db_name does not exist
elif test_connection == "42000":
    print(f"Database does not exist, setting up now")
    setup.setup_database(db_host=db_host, db_user=db_user, db_password=db_password, db_name=db_name, version=app_version)
# Other case
else:
    print(f"Error connecting to database: Connection failed")
