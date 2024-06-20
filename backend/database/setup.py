"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier permet de configurer la base de données, en fonction de la version de l'application.
Version de Python: 3.12
"""
# Import libraires
import config
from database.connection import connection
from database.fill_data import fill_data


def setup_database(db_host=config.db_host, db_user=config.db_user, db_password=config.db_password, db_name=config.db_name, version=config.version):
    try:
        database_connection = connection(db_name=None)
        if database_connection.is_connected():
            print(f"Setting up database {db_name}")
            cursor = database_connection.cursor()
            with open(f"{version}/setup{version.lower()}.sql", "r") as file:
                cursor.execute(file.read(), multi=True)
            cursor.close()
            database_connection.close()
            print(f"Database \"{db_name}\" created. Version: {version}")
            fill_data()
            print(f"Database setup complete. Version: {version}")
        else:
            database_connection.close()
            raise ValueError(f"Error setting up database: Connection is not open")
    except Exception as e:
        print(f"Error setting up database: {e}")
