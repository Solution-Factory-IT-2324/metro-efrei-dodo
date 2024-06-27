"""
Projet : FT601 - Mastercamp (Solution Factory) - 2023/2024 - MED : Métro, Efrei, Dodo
Auteurs: KOCOGLU Lucas
Description: Ce fichier permet de gérer et de traiter les données avant de le transmettre à l'API
Version de Python: 3.12
"""
import heapq

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
        SELECT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.zone_id, s.wheelchair_boarding, r.route_id, r.route_type
        FROM stops s
        JOIN stop_times st ON s.stop_id = st.stop_id
        JOIN trips t ON st.trip_id = t.trip_id
        JOIN routes r ON t.route_id = r.route_id
        WHERE r.route_type IN (0, 1, 2)
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
        WHERE r.route_type IN (0, 1, 2)
        GROUP BY st1.stop_id, st2.stop_id, t.route_id
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
            SELECT r.route_id, r.agency_id, a.agency_name, r.route_short_name, r.route_long_name, r.route_color, r.route_text_color
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
            SELECT r.route_id, r.agency_id, a.agency_name, r.route_short_name, r.route_long_name, r.route_color, r.route_text_color
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
            SELECT r.route_id, r.agency_id, a.agency_name, r.route_short_name, r.route_long_name, r.route_color, r.route_text_color
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


def dijkstra(graph_data, start_stop_id, end_stop_id):
    vertices = graph_data["vertex"]
    edges = graph_data["edge"]

    distances = {stop_id: float('inf') for stop_id in vertices}
    distances[start_stop_id] = 0
    previous_nodes = {stop_id: None for stop_id in vertices}

    # Priority queue
    priority_queue = [(0, start_stop_id)]

    while priority_queue:
        current_distance, current_stop_id = heapq.heappop(priority_queue)

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
                    f"{i + 1}. {vertices[stop_id]['stop_name']} ({stop_id}) - Line {vertices[stop_id]['line']} - Time: {distances[stop_id]}s")
            return path, distances[end_stop_id]

        if current_distance > distances[current_stop_id]:
            continue

        neighbors = get_neighbors(edges, current_stop_id, vertices)

        for neighbor, travel_time in neighbors.items():
            distance = current_distance + travel_time
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_stop_id
                heapq.heappush(priority_queue, (distance, neighbor))

    return None  # No path found


def get_neighbors(edges, current_stop_id, vertices):
    neighbors = {}
    # Track all stops at the same station
    same_station_stops = {current_stop_id}

    # Add direct connections and transfers
    for edge in edges:
        if edge["from_stop_id"] == current_stop_id:
            neighbors[edge["to_stop_id"]] = edge["travel_time"]
        elif edge["to_stop_id"] == current_stop_id and edge["type"] == "transfer":
            neighbors[edge["from_stop_id"]] = edge["travel_time"]

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
                        neighbors[stop_id] = edge["travel_time"]
                        break

    return neighbors
