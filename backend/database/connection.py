"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier est le fichier qui permet de se connecter à la base de données.
Version de Python: 3.12
"""
# Import librairies
import mysql.connector
import config

# Function to test connection to the database with db_name set
def test_connection(db_host=config.db_host, db_user=config.db_user, db_password=config.db_password, db_name=None):
    try:
        database_connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        return e.sqlstate
    connection_bool = database_connection.is_connected()
    database_connection.close()
    return connection_bool


# Function to connect to the database
def connection(db_host=config.db_host, db_user=config.db_user, db_password=config.db_password, db_name=config.db_name):
    try:
        if not db_host or not db_user or not db_password:
            raise ValueError("Error connecting to database: Missing required parameters")

        database_connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name if db_name else None
        )
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        return e.sqlstate
    return database_connection
