def dijkstra(start, end, arcs):
    # Création du graphe à partir de la liste des arcs
    graph = {}
    for arc in arcs:
        origine = arc["origine"]
        destination = arc["destination"]
        poids = arc["poids"]
        direction = arc["direction"]
        # Ajout des arêtes dans les deux sens si le graphe est non orienté
        if origine not in graph:
            graph[origine] = []
        if destination not in graph:
            graph[destination] = []

        graph[origine].append((poids, destination))
        if direction == 0:  # Si le graphe est non orienté
            graph[destination].append((poids, origine))

    # Initialisation des temps avec des valeurs infinies, sauf pour le sommet de départ
    time = {node: float('inf') for node in graph}
    time[start] = 0
    priority_queue = [(0, start)]  # Liste de tuples (temps, sommet) pour la file de priorité
    predecessors = {node: None for node in graph}  # Prédécesseurs pour reconstruire le chemin

    # Boucle principale de l'algorithme de Dijkstra
    while priority_queue:
        # Tri de la file de priorité et extraction du sommet avec le plus petit temps
        priority_queue.sort()
        current_time, current_node = priority_queue.pop(0)

        # Si nous avons atteint le sommet de destination, nous arrêtons la recherche
        if current_node == end:
            break

        # Si le temps actuel est plus grand que le temps enregistré, nous continuons
        if current_time > time[current_node]:
            continue

        # Exploration des voisins du sommet actuel
        for weight, neighbor in graph[current_node]:
            distance = current_time + weight

            # Mise à jour du temps et ajout à la file de priorité si un temps plus court est trouvé
            if distance < time[neighbor]:
                time[neighbor] = distance
                predecessors[neighbor] = current_node
                priority_queue.append((distance, neighbor))

    # Reconstruction du chemin le plus court en suivant les prédécesseurs
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = predecessors[current]
    path.reverse()  # Inversion du chemin pour obtenir le bon ordre

    return path, time[end]


def prim(start, arcs):
    # Création du graphe à partir de la liste d'arcs
    graph = {}
    for arc in arcs:
        origine = arc["origine"]
        destination = arc["destination"]
        poids = arc["poids"]

        if origine not in graph:
            graph[origine] = []
        if destination not in graph:
            graph[destination] = []

        graph[origine].append((poids, destination))
        graph[destination].append((poids, origine))  # Graphe non orienté

    # Initialisation
    mst = []
    visited = set([start])
    edges = [(poids, start, destination) for poids, destination in graph[start]]

    while edges:
        # Trouver l'arête avec le poids minimal
        edges.sort()
        poids, origine, destination = edges.pop(0)

        if destination not in visited:
            visited.add(destination)
            mst.append((origine, destination, poids))

            for next_poids, next_destination in graph[destination]:
                if next_destination not in visited:
                    edges.append((next_poids, destination, next_destination))

    return mst