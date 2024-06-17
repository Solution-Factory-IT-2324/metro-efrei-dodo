"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier permet de récupérer les données de la base de donnée, et le transformer en graphe.
Version de Python: 3.12
"""
# Import librairies
from database.connection import connection


def get_graph_data():
    database_connection = connection()
    database_connection.start_transaction(isolation_level='READ COMMITTED')

    cursor = database_connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM stations")
    stations = cursor.fetchall()

    cursor.execute("SELECT * FROM connexions")
    connexions = cursor.fetchall()

    cursor.execute("SELECT * FROM positions")
    positions = cursor.fetchall()

    cursor.close()
    database_connection.close()

    graph = create_graph(stations, connexions, positions)
    return graph


def create_graph(stations, connexions, positions):
    graph = {
        'vertex': {},
        'arc': []
    }

    for station in stations:
        graph['vertex'][station['station_id']] = {
            'station_nom': station['station_nom'],
            'station_ligne': station['station_ligne'],
            'station_est_terminus': station['station_est_terminus'],
            'station_branchement': station['station_branchement'],
            'position': None
        }

    for position in positions:
        if position['station_id'] in graph['vertex']:
            graph['vertex'][position['station_id']]['position'] = (position['position_x'], position['position_y'])

    for connexion in connexions:
        station1_id = connexion['station1_id']
        station2_id = connexion['station2_id']
        temps_en_secondes = connexion['temps_en_secondes']
        direction = connexion['direction']

        arc = {
            'origine': station1_id,
            'destination': station2_id,
            'poids': temps_en_secondes,
            'direction': direction
        }

        graph['arc'].append(arc)

        if direction == 0:
            graph['arc'].append({
                'origine': station2_id,
                'destination': station1_id,
                'poids': temps_en_secondes,
                'direction': direction
            })

    return graph

