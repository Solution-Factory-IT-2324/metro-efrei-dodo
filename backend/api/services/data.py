"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier permet de gérer et de traiter les données avant de le transmettre à l'API
Version de Python: 3.12
"""
from backend.database.connection import connection


def get_all_metro_stations():
    try:
        db_connection = connection()
        cursor = db_connection.cursor(dictionary=True)

        query = """
            SELECT DISTINCT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.zone_id, s.wheelchair_boarding
            FROM stops s
            JOIN stop_times st ON s.stop_id = st.stop_id
            JOIN trips t ON st.trip_id = t.trip_id
            JOIN routes r ON t.route_id = r.route_id
            WHERE r.route_type = 1
        """

        cursor.execute(query)
        metro_stations = cursor.fetchall()
        cursor.close()
        db_connection.close()

        return metro_stations
    except Exception as e:
        raise Exception(f"Error getting metro stations at BDD request : {str(e)}")


def get_stations_by_line_metro(line_id):
    try:
        db_connection = connection()
        cursor = db_connection.cursor(dictionary=True)

        # Query to get stations for the specific line, ordered by stop_sequence
        query = """
            SELECT
                s.stop_id,
                s.stop_name,
                st.stop_sequence AS stop_sequence,
                (0) as line_branch
            FROM stops s
            JOIN stop_times st ON s.stop_id = st.stop_id
            JOIN trips t ON st.trip_id = t.trip_id
            JOIN routes r ON t.route_id = r.route_id
            WHERE r.route_short_name = %s
              AND t.direction_id = %s
              AND r.route_type = 1
              AND st.trip_id = (
                  SELECT MAX(st_inner.trip_id)
                  FROM stop_times st_inner
                  JOIN trips t_inner ON st_inner.trip_id = t_inner.trip_id
                  JOIN routes r_inner ON t_inner.route_id = r_inner.route_id
                  WHERE r_inner.route_short_name = %s
                    AND t_inner.direction_id = %s
                    AND r_inner.route_type = 1
              )
            ORDER BY st.stop_sequence;
        """

        cursor.execute(query, (line_id, 0, line_id, 0,))
        stations_1 = cursor.fetchall()

        cursor.execute(query, (line_id, 1, line_id, 1,))
        stations_2 = cursor.fetchall()
        stations_3, stations_4 = [dico for dico in stations_1], [dico for dico in stations_2]

        if not stations_1 and not stations_2:
            raise Exception(f"No stations found for line {line_id}")

        if stations_1[0]['stop_name'] != stations_2[-1]['stop_name']:
            for station in stations_1:
                # Check if the station name is in the other list
                if station['stop_name'] in [s['stop_name'] for s in stations_2]:
                    station['line_branch'] = 1
                    del stations_2[[s['stop_name'] for s in stations_2].index(station['stop_name'])]
                else:
                    station['line_branch'] = 0

            for station in stations_2:
                station['line_branch'] = 2
                stations_1.append(station)

        for station in stations_3:
            # Detect if there is stations deserved only in one direction
            if station['stop_name'] not in [s['stop_name'] for s in stations_4]:
                station['line_branch'] = 3
                # stations_1.append(station)

        for station in stations_4:
            if station['stop_name'] not in [s['stop_name'] for s in stations_3]:
                station['line_branch'] = 4
                stations_1.append(station)

        return stations_1
    except Exception as e:
        raise Exception(f"{str(e)}")


def is_station_accessible(station_id):
    try:
        db_connection = connection()
        cursor = db_connection.cursor(dictionary=True)

        query = """
            SELECT wheelchair_boarding 
            FROM stops 
            WHERE stop_id = %s
        """
        cursor.execute(query, (station_id,))
        result = cursor.fetchone()

        cursor.close()
        db_connection.close()

        print(result)

        if result is not None:
            return {
                'station_id': station_id,
                'wheelchair_accessible': result['wheelchair_boarding'] == 1 # Case == 0 treated as False
            }
        return None
    except Exception as e:
        raise Exception(f"Error checking accessibility for station {station_id}: {str(e)}")


def get_graph_data():
    db_connection = connection()
    db_connection.start_transaction(isolation_level='READ COMMITTED')
    cursor = db_connection.cursor(dictionary=True)

    # Fetch Metro stops
    cursor.execute("""
        SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.zone_id, s.location_type, s.parent_station, s.wheelchair_boarding, r.route_id, r.route_short_name 
        FROM stops s
        JOIN stop_times st ON s.stop_id = st.stop_id
        JOIN trips t ON st.trip_id = t.trip_id
        JOIN routes r ON t.route_id = r.route_id
        WHERE r.route_type = 1  -- Only include Metro routes
    """)
    stops = cursor.fetchall()

    # Fetch Metro connections with average travel time
    cursor.execute("""
        SELECT st1.stop_id AS from_stop_id, st2.stop_id AS to_stop_id,
               MAX(TIMESTAMPDIFF(SECOND, st1.departure_time, st2.arrival_time)) AS travel_time, t.route_id
        FROM stop_times st1
        JOIN stop_times st2 ON st1.trip_id = st2.trip_id AND st1.stop_sequence + 1 = st2.stop_sequence
        JOIN trips t ON st1.trip_id = t.trip_id
        JOIN routes r ON t.route_id = r.route_id
        WHERE r.route_type = 1  -- Only include Metro routes
        GROUP BY from_stop_id, to_stop_id, route_id
    """)
    connections = cursor.fetchall()

    # Fetch transfers (can be between Metro and other lines, so no filter on route_type)
    cursor.execute("""
        SELECT DISTINCT tr.from_stop_id, tr.to_stop_id, tr.transfer_type, tr.min_transfer_time
        FROM transfers tr
        JOIN stops s1 ON tr.from_stop_id = s1.stop_id
        JOIN stops s2 ON tr.to_stop_id = s2.stop_id
        WHERE EXISTS (
            SELECT 1
            FROM stop_times st1
            JOIN trips t1 ON st1.trip_id = t1.trip_id
            JOIN routes r1 ON t1.route_id = r1.route_id
            WHERE r1.route_type = 1 AND st1.stop_id = s1.stop_id
        )
        AND EXISTS (
            SELECT 1
            FROM stop_times st2
            JOIN trips t2 ON st2.trip_id = t2.trip_id
            JOIN routes r2 ON t2.route_id = r2.route_id
            WHERE r2.route_type = 1 AND st2.stop_id = s2.stop_id
        )
    """)
    transfers = cursor.fetchall()

    cursor.close()
    db_connection.close()

    graph = {
        'vertex': {},
        'edge': []
    }

    # Build vertex for each stop
    for stop in stops:
        stop_id = stop['stop_id']
        if stop_id not in graph['vertex']:
            graph['vertex'][stop_id] = {
                'stop_name': stop['stop_name'],
                'stop_lat': stop['stop_lat'],
                'stop_lon': stop['stop_lon'],
                'zone_id': stop.get('zone_id'),
                'location_type': stop.get('location_type'),
                'parent_station': stop.get('parent_station'),
                'line': stop.get('route_id'),
                'wheelchair': stop.get('wheelchair_boarding')
            }

    # Build edges for connections
    for conn in connections:
        edge = {
            'from_stop_id': conn['from_stop_id'],
            'to_stop_id': conn['to_stop_id'],
            'travel_time': conn['travel_time'],
            'line': conn['route_id'],
            'type': 'connection'
        }
        graph['edge'].append(edge)

    # Build edges for transfers
    for transfer in transfers:
        edge = {
            'from_stop_id': transfer['from_stop_id'],
            'to_stop_id': transfer['to_stop_id'],
            'travel_time': transfer['min_transfer_time'],
            'transfer_type': transfer['transfer_type'],
            'type': 'transfer'
        }
        graph['edge'].append(edge)

    return graph