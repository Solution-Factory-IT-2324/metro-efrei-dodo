"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier est le fichier principale du backend.
Version de Python: 3.12
"""
# Files from the backend
import config
import database.connection as db
from backend.database import setup as setup

# Test connection to the database
test_connection = db.test_connection(db_name=config.db_name)

# Case if connection is OK
if test_connection == True:
    print(f"Connected to MySQL, database \"{config.db_name}\" exists")
# Case if table db_name does not exist
elif test_connection == "42000":
    print(f"Database does not exist, setting up now")
    setup.setup_database()
# Other case
else:
    print(f"Error connecting to database: Connection failed")

match (config.version):
    case "V1":
        from V1.graph import get_graph_data
        from V1.draw import draw_graph

        graph = get_graph_data()
        draw_graph(graph)
    case "V2":
        pass
    case "V3":
        pass
