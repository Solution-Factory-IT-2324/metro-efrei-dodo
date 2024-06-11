"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier permet de remplir la base de données, en fonction de la version de l'application.
Version de Python: 3.12
"""
# Import libraires
from database.connection import connection


def fill_data(db_host=None, db_user=None, db_password=None, db_name=None, version=None):
    try:
        database_connection = connection(db_host=db_host, db_user=db_user, db_password=db_password, db_name=db_name)
        if database_connection.is_connected():
            match version:
                case "V1":
                    print(f"Filling database {db_name} with data from {version}")
                    with open(f"{version}/metro.txt", "r") as file:
                        for line in file:
                            # Ignore line starting with # or empty line
                            if line.startswith("#") or not line.strip():
                                continue

                            # Split data into variables
                            # Case if line starts with V
                            if line.startswith("V"):
                                line = line[2:]
                                parts = line.strip().split(';')
                                station_id = int(parts[0].split(' ')[0].replace(';', ''))
                                station_nom = parts[0][5:].replace(';', '').replace('@', ' ')[:-1]
                                station_ligne = parts[1].replace(';', '')[:-1]
                                station_est_terminus = parts[2].split(' ')[0].replace(';', '')
                                station_branchement = int(parts[2].split(' ')[-1].replace(';', ''))
                                print(station_id, station_nom, station_ligne, station_est_terminus, station_branchement)

                                # Insert data into database
                                cursor = database_connection.cursor()
                                cursor.execute(f"INSERT INTO stations (station_id, station_nom, station_ligne, station_est_terminus, station_branchement) VALUES ({station_id}, \"{station_nom}\", \"{station_ligne}\", {station_est_terminus}, {station_branchement})")
                                cursor.close()
                            # Case if line starts with E
                            elif line.startswith("E"):
                                parts = line.strip().split(' ')
                                station1_id = int(parts[1])
                                station2_id = parts[2].replace(';', '').replace('@', ' ')
                                temps_en_secondes = int(parts[3].replace(';', ''))

                                cursor = database_connection.cursor()
                                cursor.execute(f"INSERT INTO connexions (station1_id, station2_id, temps_en_secondes) VALUES ({station1_id}, {station2_id}, {temps_en_secondes})")
                                cursor.close()
                            else:
                                continue
                    with open(f"{version}/pospoints.txt", "r") as file:
                        for line in file:
                            parts = line.strip().split(';')
                            position_x = int(parts[0])
                            position_y = int(parts[1])
                            nom = parts[2].replace('@', ' ')

                            cursor = database_connection.cursor()
                            cursor.execute(f"INSERT INTO positions (position_x, position_y, nom) VALUES ({position_x}, {position_y}, \"{nom}\")")
                            cursor.close()
                    database_connection.close()
                    print(f"Database filled with data. Version: {version}")
                case "V2":
                    pass
                case "V3":
                    pass
                case _:
                    print(f"Error filling database: Version {version} not found")
        else:
            database_connection.close()
            raise ValueError(f"Error filling database: Connection is not open")
    except Exception as e:
        print(f"Error filling database: {e}")