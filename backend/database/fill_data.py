"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier permet de remplir la base de données, en fonction de la version de l'application.
Version de Python: 3.12
"""

# Import librairies
import mysql.connector.errors
from database.connection import connection
import config
from tqdm import tqdm
import csv

def fill_data():
    try:
        database_connection = connection()
        database_connection.start_transaction(isolation_level='READ COMMITTED')
        if database_connection.is_connected():
            match config.version:
                case "V1":
                    print(f"Filling database {config.db_name} with data from {config.version}")
                    try:
                        with open(f"{config.version}/metro.txt", "r") as file:
                            for line in file:
                                # Ignore lines starting with # or empty lines
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
                                    # Check if the direction exist
                                    direction = int(parts[4]) if len(parts) > 4 else 0

                                    cursor = database_connection.cursor()
                                    query = "INSERT INTO connexions (station1_id, station2_id, temps_en_secondes, direction) VALUES (%s, %s, %s, %s)"
                                    cursor.execute(query, (station1_id, station2_id, temps_en_secondes, direction))
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
                        station_coords = {}
                        with open(f"{config.version}/pospoints.txt", "r") as file:
                            for line in file:
                                parts = line.strip().split(';')
                                position_x = int(parts[0])
                                position_y = int(parts[1])
                                nom = parts[2].replace('@', ' ').strip()
                                if nom not in station_coords:
                                    station_coords[nom] = []
                                station_coords[nom].append((position_x, position_y))

                        print(station_coords)
                        # Asignate coordinates to stations
                        cursor = database_connection.cursor()
                        for nom in list(station_coords.keys()):
                            coords = station_coords[nom]
                            cursor.execute("SELECT station_id FROM stations WHERE station_nom = %s", (nom,))
                            results = cursor.fetchall()

                            if results:
                                for result in results:
                                    station_id = result[0]
                                    if coords:
                                        position_x, position_y = coords.pop(0) if len(coords) > 1 else coords[-1]
                                        print([station_id, position_x, position_y, nom])
                                        query = "INSERT INTO positions (station_id, position_x, position_y, nom) VALUES (%s, %s, %s, %s)"
                                        try:
                                            cursor.execute(query, (station_id, position_x, position_y, nom))
                                        except mysql.connector.Error as err:
                                            if err.errno == 1062:
                                                print(f"Duplicate entry for {nom} at {position_x}, {position_y}. Skipping...")
                                            else:
                                                raise err

                        cursor.close()

                        # Asignate last known coordinates for stations without position
                        cursor = database_connection.cursor()
                        cursor.execute("SELECT station_id, station_nom FROM stations")
                        stations_in_db = cursor.fetchall()
                        cursor.close()

                        for station_id, station_nom in stations_in_db:
                            cursor = database_connection.cursor()
                            cursor.execute("SELECT * FROM positions WHERE station_id = %s", (station_id,))
                            if cursor.fetchone() is None:
                                if station_nom in station_coords and station_coords[station_nom]:
                                    position_x, position_y = station_coords[station_nom][-1]  # Utiliser la dernière paire de coordonnées
                                    print(f"Assigning last known coordinates for {station_nom}: {position_x}, {position_y}")
                                    query = "INSERT INTO positions (station_id, position_x, position_y, nom) VALUES (%s, %s, %s, %s)"
                                    try:
                                        cursor.execute(query, (station_id, position_x, position_y, station_nom))
                                    except mysql.connector.Error as err:
                                        if err.errno == 1062:
                                            print(f"Duplicate entry for {station_nom} at {position_x}, {position_y}. Skipping...")
                                        else:
                                            raise err

                        cursor.close()
                        database_connection.commit()

                        cursor = database_connection.cursor()
                        cursor.execute("SELECT station_id, station_nom FROM stations WHERE station_id NOT IN (SELECT station_id FROM positions)")
                        stations_without_position = cursor.fetchall()
                        if stations_without_position:
                            for station_id, station_nom in stations_without_position:
                                print(f"Station {station_id} ({station_nom}) without position, skipping...")
                        print(station_coords)
                        cursor.close()

                    except Exception as e:
                        print(f"Error processing pospoints.txt: {e}")
                        database_connection.rollback()

                    database_connection.close()
                    print(f"Database filled with data. Version: {config.version}")
                case "V2":
                    print(f"Filling database {config.db_name} with data from {config.version}")
                    try:
                        tables = {
                            'agency': (
                            ["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_lang", "agency_phone", "agency_email", "agency_fare_url"], 'V2/agency.txt'),
                            'calendar': (
                            ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"], 'V2/calendar.txt'),
                            'calendar_dates': (["service_id", "date", "exception_type"], 'V2/calendar_dates.txt'),
                            'pathways': (
                            ["pathway_id", "from_stop_id", "to_stop_id", "pathway_mode", "is_bidirectional", "length", "traversal_time", "stair_count", "max_slope", "min_width", "signposted_as", "reversed_signposted_as"], 'V2/pathways.txt'),
                            'routes': (
                            ["route_id", "agency_id", "route_short_name", "route_long_name", "route_desc", "route_type", "route_url", "route_color", "route_text_color", "route_sort_order"], 'V2/routes.txt'),
                            'stop_extensions': (
                            ["object_id", "object_system", "object_code"], 'V2/stop_extensions.txt'),
                            'stop_times': (
                            ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence", "pickup_type", "drop_off_type", "local_zone_id", "stop_headsign", "timepoint"], 'V2/stop_times.txt'),
                            'stops': (
                            ['stop_id', 'stop_code', 'stop_name', 'stop_desc', 'stop_lon', 'stop_lat', 'zone_id', 'stop_url', 'location_type', 'parent_station', 'stop_timezone', 'level_id', 'wheelchair_boarding', 'platform_code'], 'V2/stops.txt'),
                            'transfers': (
                            ["from_stop_id", "to_stop_id", "transfer_type", "min_transfer_time"], 'V2/transfers.txt'),
                            'trips': (
                            ["route_id", "service_id", "trip_id", "trip_headsign", "trip_short_name", "direction_id", "block_id", "shape_id", "wheelchair_accessible", "bikes_allowed"], 'V2/trips.txt')
                        }
                        for table, (columns, file_path) in tables.items():
                            print(f"Processing {table}...")
                            with open(file_path, "r") as file:
                                reader = csv.DictReader(file, fieldnames=columns)
                                # Skip header
                                next(reader)
                                for row in tqdm(reader):
                                    cursor = database_connection.cursor()
                                    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
                                    values = [row[col].strip() if row[col] != '' else None for col in columns]
                                    cursor.execute(query, values)
                                    cursor.close()

                        from time import time
                        start = time()
                        database_connection.commit()
                        print(f"Time to commit: {time() - start}")
                        database_connection.close()
                    except Exception as e:
                        print(f"Error processing data: {e}")
                        print(row)
                        print(values)
                        database_connection.rollback()
                case "V3":
                    pass
                case _:
                    print(f"Error filling database: Version {config.version} not found")
        else:
            database_connection.close()
            raise ValueError(f"Error filling database: Connection is not open")
    except Exception as e:
        print(f"Error filling database: {e}")