"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier permet de configurer la base de données, en fonction de la version de l'application.
Version de Python: 3.12
"""
# Import libraires
from config import version
from database.connection import connection


def setup_database(db_host=None, db_user=None, db_password=None, db_name=None, version=None):
    try:
        database_connection = connection(db_host=db_host, db_user=db_user, db_password=db_password)
        if database_connection.is_connected():
            print(f"Setting up database {db_name}")
            cursor = database_connection.cursor()
            with open(f"{version}/setup{version.lower()}.sql", "r") as file:
                cursor.execute(file.read(), multi=True)
                cursor.close()
            database_connection.close()
            print(f"Database setup complete. Version: {version}")
        else:
            database_connection.close()
            raise ValueError(f"Error setting up database: Connection is not open")
    except Exception as e:
        print(f"Error setting up database: {e}")
