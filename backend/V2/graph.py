from database.connection import connection

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

    graph = create_graph(stops, connections, transfers)
    return graph

def create_graph(stops, connections, transfers):
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
    for connection in connections:
        edge = {
            'from_stop_id': connection['from_stop_id'],
            'to_stop_id': connection['to_stop_id'],
            'travel_time': connection['travel_time'],
            'line': connection['route_id'],
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
