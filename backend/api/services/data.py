"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier permet de gérer et de traiter les données avant de le transmettre à l'API
Version de Python: 3.12
"""
import heapq
from datetime import datetime, timedelta

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
            WHERE r.route_type in (0,1,2)
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
                'wheelchair_accessible': result['wheelchair_boarding'] == 1  # Case == 0 treated as False
            }
        return None
    except Exception as e:
        raise Exception(f"Error checking accessibility for station {station_id}: {str(e)}")


def get_graph_data():
    db_connection = connection()
    db_connection.start_transaction(isolation_level='READ COMMITTED')
    cursor = db_connection.cursor(dictionary=True)

    # Fetch Stops
    from time import time
    start = time()
    print("Fetching stops")
    cursor.execute("""
        SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.zone_id, s.wheelchair_boarding, r.route_id, r.route_type
        FROM stops s
        JOIN stop_times st ON s.stop_id = st.stop_id
        JOIN trips t ON st.trip_id = t.trip_id
        JOIN routes r ON t.route_id = r.route_id
        WHERE r.route_type IN (0, 1, 2)
    """)
    stops = cursor.fetchall()
    print(f"Time to fetch stops: {time() - start}s")

    # Fetch Metro connections with average travel time
    start = time()
    print("Fetching connections")
    cursor.execute("""
        SELECT st1.stop_id AS from_stop_id, st2.stop_id AS to_stop_id,
               MAX(TIMESTAMPDIFF(SECOND, st1.departure_time, st2.arrival_time)) AS travel_time, t.route_id
        FROM stop_times st1
        JOIN (
            SELECT st_inner1.trip_id, st_inner1.stop_sequence, MIN(st_inner2.stop_sequence) AS next_sequence
            FROM stop_times st_inner1
            JOIN stop_times st_inner2 ON st_inner1.trip_id = st_inner2.trip_id AND st_inner1.stop_sequence < st_inner2.stop_sequence
            GROUP BY st_inner1.trip_id, st_inner1.stop_sequence
        ) AS next_stops ON st1.trip_id = next_stops.trip_id AND st1.stop_sequence = next_stops.stop_sequence
        JOIN stop_times st2 ON st1.trip_id = st2.trip_id AND next_stops.next_sequence = st2.stop_sequence
        JOIN trips t ON st1.trip_id = t.trip_id
        JOIN routes r ON t.route_id = r.route_id
        WHERE r.route_type IN (0, 1, 2)
        GROUP BY st1.stop_id, st2.stop_id, t.route_id
    """)
    connections = cursor.fetchall()
    print(f"Time to fetch connections: {time() - start}s")

    # Fetch transfers (can be between Metro and other lines, so no filter on route_type)
    print("Fetching transfers")
    start = time()
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
            WHERE r1.route_type IN (0, 1, 2) AND st1.stop_id = s1.stop_id
        )
        AND EXISTS (
            SELECT 1
            FROM stop_times st2
            JOIN trips t2 ON st2.trip_id = t2.trip_id
            JOIN routes r2 ON t2.route_id = r2.route_id
            WHERE r2.route_type IN (0, 1, 2) AND st2.stop_id = s2.stop_id
        )
    """)
    transfers = cursor.fetchall()
    print(f"Time to fetch transfers: {time() - start}s")

    cursor.close()
    db_connection.close()

    graph = {
        'vertex': {stop['stop_id']: {
            'stop_name': stop['stop_name'],
            'stop_lat': stop['stop_lat'],
            'stop_lon': stop['stop_lon'],
            'zone_id': stop.get('zone_id'),
            'line': stop.get('route_id'),
            'line_type': stop.get('route_type'),
            'wheelchair': stop.get('wheelchair_boarding')
        } for stop in stops},
        'edge': [
                    {
                        'from_stop_id': conn['from_stop_id'],
                        'to_stop_id': conn['to_stop_id'],
                        'travel_time': conn['travel_time'],
                        'line': conn['route_id'],
                        'type': 'connection'
                    } for conn in connections
                ] + [
                    {
                        'from_stop_id': transfer['from_stop_id'],
                        'to_stop_id': transfer['to_stop_id'],
                        'travel_time': transfer['min_transfer_time'],
                        'transfer_type': transfer['transfer_type'],
                        'type': 'transfer'
                    } for transfer in transfers
                ]
    }

    return graph


def get_is_graph_connected(graph, option="dfs"):
    from time import time
    start = time()

    def get_neighbors(graph, vertex):
        neighbors = set()
        for edge in graph['edge']:
            if edge['from_stop_id'] == vertex:
                neighbors.add(edge['to_stop_id'])
            elif edge['to_stop_id'] == vertex:
                neighbors.add(edge['from_stop_id'])
        return neighbors

    vertices = list(graph['vertex'].keys())
    if not vertices:
        return False
    visited = set()

    match option:
        case "dfs":
            # Apply DFS algorithm to check if all vertices are connected
            stack = [vertices[0]]
            while stack:
                vertex = stack.pop()
                if vertex not in visited:
                    visited.add(vertex)
                    stack.extend(neighbor for neighbor in get_neighbors(graph, vertex) if neighbor not in visited)
        case "bfs":
            # Apply BFS algorithm to check if all vertices are connected
            queue = [vertices[0]]
            while queue:
                vertex = queue.pop(0)
                if vertex not in visited:
                    visited.add(vertex)
                    neighbors = get_neighbors(graph, vertex)
                    for neighbor in neighbors:
                        if neighbor not in visited:
                            queue.append(neighbor)
        case _:
            raise ValueError(f"Invalid option: {option}")

    print(f"Time to check connectivity with {option} : {time() - start:}s")
    return len(visited) == len(vertices)


def prim_algorithm(graph):
    # Initialize the tree and the list of vertices to process
    tree = {'vertex': {}, 'edge': []}
    vertices = set(graph['vertex'].keys())
    if not vertices:
        return tree

    # Mapping of station names to their respective IDs
    station_name_to_ids = {}
    for vertex_id, vertex_data in graph['vertex'].items():
        stop_name = vertex_data['stop_name']
        if stop_name not in station_name_to_ids:
            station_name_to_ids[stop_name] = []
        station_name_to_ids[stop_name].append(vertex_id)

    def add_edges(vertex):
        for edge in graph['edge']:
            if edge['from_stop_id'] == vertex and edge['to_stop_id'] in vertices:
                priority_queue.append((edge['travel_time'], edge))
            elif edge['to_stop_id'] == vertex and edge['from_stop_id'] in vertices:
                priority_queue.append((edge['travel_time'], edge))

    priority_queue = []

    # Start with the first vertex
    current_vertex = list(vertices)[0]
    current_name = graph['vertex'][current_vertex]['stop_name']
    for vertex_id in station_name_to_ids[current_name]:
        tree['vertex'][vertex_id] = graph['vertex'][vertex_id]
        vertices.remove(vertex_id)
        add_edges(vertex_id)

    while vertices:
        # Sort the priority queue to get the edge with minimum weight
        priority_queue.sort(key=lambda x: x[0])
        if not priority_queue:
            break

        # Get the edge with the smallest weight
        min_weight, min_edge = priority_queue.pop(0)
        if min_edge['from_stop_id'] in tree['vertex']:
            next_vertex = min_edge['to_stop_id']
        else:
            next_vertex = min_edge['from_stop_id']

        if next_vertex in vertices:
            # Add the smallest edge and the corresponding vertex to the tree
            tree['edge'].append(min_edge)
            next_name = graph['vertex'][next_vertex]['stop_name']
            for vertex_id in station_name_to_ids[next_name]:
                if vertex_id in vertices:
                    tree['vertex'][vertex_id] = graph['vertex'][vertex_id]
                    vertices.remove(vertex_id)
                    add_edges(vertex_id)

    # Verify if the tree is connected
    """if len(tree['vertex']) != len(graph['vertex']):
        raise Exception("The graph is not connected")"""

    # Re-Mapping of station names to their respective IDs
    station_name_to_ids = {}
    for vertex_id, vertex_data in tree['vertex'].items():
        stop_name = vertex_data['stop_name']
        if stop_name not in station_name_to_ids:
            station_name_to_ids[stop_name] = []
        station_name_to_ids[stop_name].append(vertex_id)

    # print(f"Tree has unique {len(station_name_to_ids)} (by name) stations")
    # print(f"Graph has {len(graph['vertex'])} vertices and {len(graph['edge'])} edges")
    # print(f"Tree has {len(tree['vertex'])} vertices and {len(tree['edge'])} edges")
    # print(f"Total weight of the tree: {sum(edge['travel_time'] for edge in tree['edge'])} seconds")
    # print("Tree is connected" if get_is_graph_connected(tree) else "Tree is not connected")
    # print("Tree is a minimum spanning tree" if len(tree['vertex']) - 1 == len(tree['edge']) else "Tree is not a minimum spanning tree")
    return tree


def kruskal_algorithm(graph):
    # Initialize the tree and the list of edges to process
    tree = {'vertex': {}, 'edge': []}
    vertices = set(graph['vertex'].keys())
    if not vertices:
        return tree

    def find(parent, vertex):
        if parent[vertex] != vertex:
            parent[vertex] = find(parent, parent[vertex])
        return parent[vertex]

    def union(parent, rank, root1, root2):
        if rank[root1] > rank[root2]:
            parent[root2] = root1
        elif rank[root1] < rank[root2]:
            parent[root1] = root2
        else:
            parent[root2] = root1
            rank[root1] += 1

    # Sort all edges in the graph in ascending order of their weight
    edges = sorted(graph['edge'], key=lambda edge: edge['travel_time'])

    # Initialize the disjoint-set
    parent = {}
    rank = {}
    for vertex in vertices:
        parent[vertex] = vertex
        rank[vertex] = 0

    # Mapping of station names to their respective IDs
    station_name_to_ids = {}
    for vertex_id, vertex_data in graph['vertex'].items():
        stop_name = vertex_data['stop_name']
        if stop_name not in station_name_to_ids:
            station_name_to_ids[stop_name] = []
        station_name_to_ids[stop_name].append(vertex_id)

    def unify_same_name_stations(station_name_to_ids):
        for station_ids in station_name_to_ids.values():
            if len(station_ids) > 1:
                root = find(parent, station_ids[0])
                for vertex_id in station_ids[1:]:
                    union(parent, rank, root, find(parent, vertex_id))

    # Unify all stations with the same name initially
    unify_same_name_stations(station_name_to_ids)

    # Iterate through the sorted edges and construct the MST
    for edge in edges:
        from_vertex = edge['from_stop_id']
        to_vertex = edge['to_stop_id']
        weight = edge['travel_time']

        root1 = find(parent, from_vertex)
        root2 = find(parent, to_vertex)

        # Add the edge to the tree if it doesn't form a cycle
        if root1 != root2:
            tree['edge'].append(edge)
            union(parent, rank, root1, root2)

            # Add the vertices to the tree
            if from_vertex not in tree['vertex']:
                tree['vertex'][from_vertex] = graph['vertex'][from_vertex]
            if to_vertex not in tree['vertex']:
                tree['vertex'][to_vertex] = graph['vertex'][to_vertex]

    # Verify if the tree is connected
    """if len(tree['vertex']) != len(graph['vertex']):
        raise Exception("The graph is not connected")"""

    # print(f"Tree has unique {len(station_name_to_ids)} (by name) stations")
    # print(f"Graph has {len(graph['vertex'])} vertices and {len(graph['edge'])} edges")
    # print(f"Tree has {len(tree['vertex'])} vertices and {len(tree['edge'])} edges")
    # print(f"Total weight of the tree: {sum(edge['travel_time'] for edge in tree['edge'])} seconds")
    # print("Tree is connected" if get_is_graph_connected(tree) else "Tree is not connected")
    # print("Tree is a minimum spanning tree" if len(tree['vertex']) - 1 == len(tree['edge']) else "Tree is not a minimum spanning tree")
    return tree


def get_all_lines_data():
    try:
        db_connection = connection()
        cursor = db_connection.cursor(dictionary=True)

        query = """
            SELECT r.route_id, r.agency_id, a.agency_name, r.route_short_name, r.route_long_name, r.route_color, r.route_text_color, r.route_type
            FROM routes r
            JOIN agency a ON r.agency_id = a.agency_id
            WHERE r.route_type in (0, 1, 2)
            ORDER BY r.route_id
        """

        cursor.execute(query)
        lines = cursor.fetchall()
        cursor.close()
        db_connection.close()

        return lines
    except Exception as e:
        raise Exception(f"Error getting metro lines at BDD request : {str(e)}")


def get_line_data_by_id(line_id):
    try:
        db_connection = connection()
        cursor = db_connection.cursor(dictionary=True)

        query = """
            SELECT r.route_id, r.agency_id, a.agency_name, r.route_short_name, r.route_long_name, r.route_color, r.route_text_color, r.route_type
            FROM routes r
            JOIN agency a ON r.agency_id = a.agency_id
            WHERE r.route_type = 1
            AND r.route_id = %s
            ORDER BY r.route_id
        """

        cursor.execute(query, (line_id,))
        lines = cursor.fetchall()
        cursor.close()
        db_connection.close()

        return lines
    except Exception as e:
        raise Exception(f"Error getting metro lines at BDD request : {str(e)}")


def get_line_data_by_name(line_short_name):
    try:
        db_connection = connection()
        cursor = db_connection.cursor(dictionary=True)

        query = """
            SELECT r.route_id, r.agency_id, a.agency_name, r.route_short_name, r.route_long_name, r.route_color, r.route_text_color, r.route_type
            FROM routes r
            JOIN agency a ON r.agency_id = a.agency_id
            WHERE r.route_type = 1
            AND r.route_short_name = %s
            ORDER BY r.route_id
        """

        cursor.execute(query, (line_short_name,))
        lines = cursor.fetchall()
        cursor.close()
        db_connection.close()

        return lines
    except Exception as e:
        raise Exception(f"Error getting metro lines at BDD request : {str(e)}")


def get_neighbors(edges, current_stop_id, vertices):
    neighbors = {}
    # Track all stops at the same station
    same_station_stops = {current_stop_id}

    # Add direct connections and transfers
    for edge in edges:
        if edge["from_stop_id"] == current_stop_id:
            neighbors[edge["to_stop_id"]] = (edge["travel_time"], vertices[edge["to_stop_id"]]['line'])
        elif edge["to_stop_id"] == current_stop_id and edge["type"] == "transfer":
            neighbors[edge["from_stop_id"]] = (edge["travel_time"], vertices[edge["from_stop_id"]]['line'])

        if vertices[edge["from_stop_id"]]["stop_name"] == vertices[current_stop_id]["stop_name"]:
            same_station_stops.add(edge["from_stop_id"])
        if vertices[edge["to_stop_id"]]["stop_name"] == vertices[current_stop_id]["stop_name"]:
            same_station_stops.add(edge["to_stop_id"])

    for stop_id in same_station_stops:
        if stop_id != current_stop_id:
            for edge in edges:
                if (edge["from_stop_id"] == current_stop_id and edge["to_stop_id"] == stop_id) or \
                        (edge["from_stop_id"] == stop_id and edge["to_stop_id"] == current_stop_id):
                    if edge["type"] == "transfer":
                        neighbors[stop_id] = (edge["travel_time"], vertices[stop_id]['line'])
                        break

    return neighbors


def emission_calculator(journey_path, emission_factors, graph):
    def haversine(coord1, coord2):
        import math

        # Radius of Earth (km)
        R = 6371.0
        lat1, lon1 = float(coord1[0]), float(coord1[1])
        lat2, lon2 = float(coord2[0]), float(coord2[1])

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(
            dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        d = R * c
        return d

    cpt_CO2_journey = 0.0
    cpt_distance = 0.0

    for i in range(len(journey_path) - 1):
        from_stop_id = journey_path[i]
        to_stop_id = journey_path[i + 1]

        from_vertex = graph['vertex'].get(from_stop_id)
        to_vertex = graph['vertex'].get(to_stop_id)

        if not from_vertex or not to_vertex:
            continue

        from_coord = (from_vertex['stop_lat'], from_vertex['stop_lon'])
        to_coord = (to_vertex['stop_lat'], to_vertex['stop_lon'])

        distance = haversine(from_coord, to_coord)
        mode = from_vertex['line_type']
        match mode:
            case 0:
                mode = 'tram'
            case 1:
                mode = 'metro'
            case 2:
                mode = 'train'
            case 3:
                mode = 'bus'
            case 7:
                mode = 'funiculaire'
            case _:
                continue

        line = from_vertex.get('line', None)

        if line and line.startswith('IDFM:'):
            line = line[5:]
        # If the mode is bus, we don't have line information
        if mode == 'bus':
            co2_line, co2_mode = emission_factors.get(mode, {}).get('null', (0, 0))
        else:
            co2_line, co2_mode = emission_factors.get(mode, {}).get(line, (0, 0))
        emission_factor = co2_line if co2_line else co2_mode

        cpt_CO2_journey += distance * float(emission_factor)
        cpt_distance += distance

    CO2_journey_car = 99.0
    return cpt_CO2_journey, cpt_distance * CO2_journey_car, cpt_distance


def get_emission_factors():
    db_connection = connection()
    cursor = db_connection.cursor(dictionary=True)
    cursor.execute("SELECT transport_mode, id_line, co2e_voy_km_line, co2e_voy_km_mode FROM emissions")
    emission_factors = {}
    for row in cursor.fetchall():
        mode = row['transport_mode']
        line = row['id_line']
        co2_line = row['co2e_voy_km_line']
        co2_mode = row['co2e_voy_km_mode']
        if mode not in emission_factors:
            emission_factors[mode] = {}
        emission_factors[mode][line] = (co2_line, co2_mode)
    cursor.close()
    db_connection.close()
    return emission_factors


def update_graph_with_real_time(graph_data, date_set):
    db_connection = connection()
    cursor = db_connection.cursor(dictionary=True)

    query = """
    SELECT st.trip_id, st.arrival_time, st.departure_time, st.stop_id, t.route_id, t.service_id
    FROM stop_times st
    JOIN trips t ON st.trip_id = t.trip_id
    JOIN calendar c ON t.service_id = c.service_id
    WHERE c.start_date <= %s AND c.end_date >= %s
    AND (
        (c.monday = 1 AND DAYOFWEEK(%s) = 2) OR
        (c.tuesday = 1 AND DAYOFWEEK(%s) = 3) OR
        (c.wednesday = 1 AND DAYOFWEEK(%s) = 4) OR
        (c.thursday = 1 AND DAYOFWEEK(%s) = 5) OR
        (c.friday = 1 AND DAYOFWEEK(%s) = 6) OR
        (c.saturday = 1 AND DAYOFWEEK(%s) = 7) OR
        (c.sunday = 1 AND DAYOFWEEK(%s) = 1)
    )
    """

    date = date_set.date()
    cursor.execute(query, (date, date, date, date, date, date, date, date, date))
    real_time_data = cursor.fetchall()

    cursor.close()
    db_connection.close()

    for record in real_time_data:
        trip_id = record['trip_id']
        arrival_time = record['arrival_time']
        departure_time = record['departure_time']
        stop_id = record['stop_id']
        route_id = record['route_id']

        # Convert arrival and departure times to seconds from midnight for easier comparison
        if isinstance(arrival_time, timedelta):
            arrival_seconds = arrival_time.total_seconds()
        else:
            arrival_seconds = arrival_time.hour * 3600 + arrival_time.minute * 60 + arrival_time.second

        if isinstance(departure_time, timedelta):
            departure_seconds = departure_time.total_seconds()
        else:
            departure_seconds = departure_time.hour * 3600 + departure_time.minute * 60 + departure_time.second

        # Update the graph_data with real-time stop_times
        if stop_id in graph_data['vertex']:
            if 'real_time' not in graph_data['vertex'][stop_id]:
                graph_data['vertex'][stop_id]['real_time'] = {}

            if route_id not in graph_data['vertex'][stop_id]['real_time']:
                graph_data['vertex'][stop_id]['real_time'][route_id] = {}

            graph_data['vertex'][stop_id]['real_time'][route_id][trip_id] = {
                'arrival_time': arrival_seconds,
                'departure_time': departure_seconds
            }

    return graph_data


def preprocess_real_time_data(vertices):
    real_time_lookup = {}
    for stop_id, stop_data in vertices.items():
        if 'real_time' in stop_data:
            if stop_id not in real_time_lookup:
                real_time_lookup[stop_id] = []
            for line_id, trips in stop_data['real_time'].items():
                for trip_id, times in trips.items():
                    if 'departure_time' in times:
                        real_time_lookup[stop_id].append(times['departure_time'])
            real_time_lookup[stop_id].sort()
    return real_time_lookup


def dijkstra(graph_data, start_stop_id, end_stop_id, current_datetime=None):
    vertices = graph_data["vertex"]
    edges = graph_data["edge"]

    if current_datetime is None:
        current_datetime = datetime.now()

    current_time_seconds = current_datetime.hour * 3600 + current_datetime.minute * 60 + current_datetime.second

    real_time_lookup = preprocess_real_time_data(vertices)

    distances = {stop_id: float('inf') for stop_id in vertices}
    distances[start_stop_id] = 0
    previous_nodes = {stop_id: None for stop_id in vertices}
    arrival_times = {stop_id: float('inf') for stop_id in vertices}
    arrival_times[start_stop_id] = current_time_seconds
    current_lines = {stop_id: None for stop_id in vertices}

    # Priority queue
    priority_queue = [(0, start_stop_id, current_time_seconds, None)]

    while priority_queue:
        current_distance, current_stop_id, current_arrival_time, current_line = heapq.heappop(priority_queue)

        # Destination reached
        if current_stop_id == end_stop_id:
            path = []
            while previous_nodes[current_stop_id]:
                path.insert(0, current_stop_id)
                current_stop_id = previous_nodes[current_stop_id]
            path.insert(0, start_stop_id)

            # Print path and distance, with station name and line
            for i, stop_id in enumerate(path):
                vertices[stop_id]['line'] = vertices[stop_id].get('line', 'N/A')
                print(
                    f"{i + 1}. {vertices[stop_id]['stop_name']} ({stop_id}) - Line {vertices[stop_id]['line']} - Time: {distances[stop_id]}s at Hour: {arrival_times[stop_id] // 3600}h{arrival_times[stop_id] % 3600 // 60}m{arrival_times[stop_id] % 60}s ({arrival_times[stop_id]})")
            return path, distances[end_stop_id]

        if current_distance > distances[current_stop_id]:
            continue

        neighbors = get_neighbors(edges, current_stop_id, vertices)

        for neighbor, (travel_time, neighbor_line) in neighbors.items():
            wait_time = 0

            # Check for line change
            if neighbor_line != current_line and current_stop_id in real_time_lookup:
                next_departure_time = float('inf')
                for departure_time in real_time_lookup[current_stop_id]:
                    if current_arrival_time <= departure_time < next_departure_time:
                        next_departure_time = departure_time
                        break

                if next_departure_time < float('inf'):
                    wait_time = next_departure_time - current_arrival_time
                else:
                    continue  # No valid departure time found

            # Calculate total distance including wait time and travel time
            distance = current_distance + travel_time + wait_time
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_stop_id
                arrival_times[neighbor] = current_arrival_time + travel_time + wait_time
                heapq.heappush(priority_queue, (distance, neighbor, arrival_times[neighbor], neighbor_line))

    return None  # No path found
