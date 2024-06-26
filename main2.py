import json

# Charger les données depuis le fichier JSON
with open('graph.json', 'r') as f:
    data = json.load(f)

# Extraire les arrêts et les connexions
vertex = data['vertex']
edges = data['edge']

# Construire le graphe orienté en excluant les IDFM avec le même stop_name et line
graph = {}
visited_stations = set()  # Pour garder une trace des stations déjà ajoutées au graphe

for edge in edges:
    stop_from = edge['from_stop_id']
    stop_to = edge['to_stop_id']
    time = edge['travel_time']
    
    station_from = vertex[stop_from]
    station_to = vertex[stop_to]
    
    # Vérifier si les deux stations ont le même stop_name et line
    if (station_from['stop_name'], station_from['line']) == (station_to['stop_name'], station_to['line']):
        continue  # Ignorer cette connexion
    
    # Ajouter au graphe si la station de départ n'a pas encore été ajoutée
    if stop_from not in graph:
        graph[stop_from] = []
    graph[stop_from].append((time, stop_to))

def dijkstra(graph, start, end):
    # Priority queue implemented as a list
    queue = [(0, start)]
    # Dictionary to store the shortest path to each vertex
    shortest_paths = {start: (None, 0)}
    visited = set()

    while queue:
        # Sort queue to get the element with the smallest cost
        queue.sort()
        current_cost, current_vertex = queue.pop(0)

        if current_vertex in visited:
            continue

        visited.add(current_vertex)

        if current_vertex == end:
            break

        for edge_cost, neighbor in graph.get(current_vertex, []):
            cost = current_cost + edge_cost
            if neighbor not in shortest_paths or cost < shortest_paths[neighbor][1]:
                shortest_paths[neighbor] = (current_vertex, cost)
                queue.append((cost, neighbor))

    # Build the shortest path from start to end
    path = []
    current_vertex = end
    while current_vertex is not None:
        path.append(current_vertex)
        next_vertex = shortest_paths[current_vertex][0]
        current_vertex = next_vertex
    path = path[::-1]  # Reverse the path

    return path, shortest_paths[path[-1]][1]

# Exemple d'utilisation
start = "IDFM:22400"  # Par exemple, VLA
end = "IDFM:22010"
path, cost = dijkstra(graph, start, end)
print(f"Le plus court chemin de {start} à {end} est {path} avec un temps de {cost/60} min ")

# Afficher les noms des stations
for stop_id in path:
    station = vertex[stop_id]
    print(station["stop_name"])
