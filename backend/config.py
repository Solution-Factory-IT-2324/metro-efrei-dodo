"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier permet d'établir les variables de configuration pour le backend.
Version de Python: 3.12
"""
# Import libraires
from dotenv import load_dotenv
import os

# Choix de la version
version = "V2"
database_name = "MED" + version

# Charge environment variables
load_dotenv(dotenv_path='.env')

# Fetch environment & config variable
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = database_name

# API settings
port = 8080
debug = True
