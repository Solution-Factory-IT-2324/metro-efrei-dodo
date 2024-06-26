import json
import heapq

# Charger les données depuis le fichier JSON
with open('graph.json', 'r') as f:
    data = json.load(f)

# Extraire les arrêts et les connexions
vertex = data['vertex']
edges = data['edge']

# Construire le graphe orienté
graph = {}
for edge in edges:
    stop_from = edge['from_stop_id']
    stop_to = edge['to_stop_id']
    time = edge['travel_time']  # Ajustez ici selon les clés correctes
    if stop_from not in graph:
        graph[stop_from] = []
    graph[stop_from].append((time, stop_to))
    
# Fonction pour l'algorithme de Dijkstra
def dijkstra(graph, start, end):
    queue = [(0, start)]
    distances = {start: 0}
    previous_nodes = {start: None}
    visited = set()  # Pour suivre les nœuds visités
    
    while queue:
        current_distance, current_node = heapq.heappop(queue)
        
        if current_node in visited:
            continue
        
        visited.add(current_node)
        
        if current_node == end:
            break
        
        for neighbor_distance, neighbor in graph.get(current_node, []):
            distance = current_distance + neighbor_distance
            if distance < distances.get(neighbor, float('inf')):
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(queue, (distance, neighbor))
    
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = previous_nodes[node]
    
    path.reverse()
    return path, distances[end]

# Exemple d'utilisation
start = 'IDFM:463307'  # Par exemple, VLA
end = 'IDFM:463067'  # Par exemple, Nation
path, distance = dijkstra(graph, start, end)
print(f"Chemin le plus court de {start} à {end}: {path} avec une distance de {distance}")

for i in range(len(path)):
    station = vertex[path[i]]
    print(station["stop_name"])