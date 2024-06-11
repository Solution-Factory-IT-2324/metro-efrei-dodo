"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier permet de remplir la base de données, en fonction de la version de l'application.
Version de Python: 3.12
"""
# Import libraires
import mysql.connector.errors
from database.connection import connection


def fill_data(db_host=None, db_user=None, db_password=None, db_name=None, version=None):
    try:
        database_connection = connection(db_host=db_host, db_user=db_user, db_password=db_password, db_name=db_name)
        database_connection.start_transaction(isolation_level='READ COMMITTED')
        if database_connection.is_connected():
            match version:
                case "V1":
                    print(f"Filling database {db_name} with data from {version}")
                    try:
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
                                    station_nom = parts[0][5:].replace(';', '').replace('@', ' ').strip()
                                    station_ligne = parts[1].replace(';', '').strip()
                                    station_est_terminus = parts[2].split(' ')[0].replace(';', '').strip() == 'True'
                                    station_branchement = int(parts[2].split(' ')[-1].replace(';', ''))
                                    print(station_id, station_nom, station_ligne, station_est_terminus, station_branchement)

                                    # Insert data into database
                                    cursor = database_connection.cursor()
                                    query = "INSERT INTO stations (station_id, station_nom, station_ligne, station_est_terminus, station_branchement) VALUES (%s, %s, %s, %s, %s)"
                                    cursor.execute(query, (station_id, station_nom, station_ligne, station_est_terminus, station_branchement))
                                    cursor.close()
                                # Case if line starts with E
                                elif line.startswith("E"):
                                    parts = line.strip().split(' ')
                                    station1_id = int(parts[1])
                                    station2_id = int(parts[2])
                                    temps_en_secondes = int(parts[3])

                                    cursor = database_connection.cursor()
                                    query = "INSERT INTO connexions (station1_id, station2_id, temps_en_secondes) VALUES (%s, %s, %s)"
                                    cursor.execute(query, (station1_id, station2_id, temps_en_secondes))
                                    cursor.close()
                                else:
                                    continue

                        # Commit changes to the database
                        database_connection.commit()
                    except Exception as e:
                        print(f"Error processing metro.txt: {e}")
                        database_connection.rollback()
                    try:
                        # Process pospoints.txt
                        with open(f"{version}/pospoints.txt", "r") as file:
                            for line in file:
                                parts = line.strip().split(';')
                                position_x = int(parts[0])
                                position_y = int(parts[1])
                                nom = parts[2].replace('@', ' ').strip()
                                print([position_x, position_y, nom])

                                cursor = database_connection.cursor()
                                cursor.execute("SELECT station_id FROM stations WHERE station_nom = %s", (nom,))
                                results = cursor.fetchall()

                                if results:
                                    for result in results:
                                        station_id = result[0]
                                        print([station_id, position_x, position_y, nom])
                                        query = "INSERT INTO positions (station_id, position_x, position_y, nom) VALUES (%s, %s, %s, %s)"
                                        try:
                                            cursor.execute(query, (station_id, position_x, position_y, nom))
                                        except mysql.connector.Error as err:
                                            if err.errno == 1062:
                                                print(
                                                    f"Duplicate entry for {nom} at {position_x}, {position_y}. Skipping...")
                                            else:
                                                raise err
                                else:
                                    print(f"No matching station found for: {nom}")
                                cursor.close()

                        database_connection.commit()
                    except Exception as e:
                        print(f"Error processing pospoints.txt: {e}")
                        database_connection.rollback()

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