import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
from V1.pccacpm import dijkstra


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def draw_graph(graph_data, start_station=363, end_station=245):
    root = tk.Tk()
    root.title("Metro Map")

    image_width = 987
    image_height = 952

    canvas = tk.Canvas(root, width=image_width, height=image_height)
    canvas.pack()

    # Charger et modifier l'image de fond
    bg_image = Image.open("V1/assets/metrof_r.png")
    bg_image = bg_image.resize((image_width, image_height), Image.Resampling.LANCZOS)

    # Appliquer l'opacité (transparence)
    alpha = 64  # 0 (transparent) à 255 (opaque)
    bg_image.putalpha(alpha)

    bg_photo = ImageTk.PhotoImage(bg_image)
    canvas.create_image(0, 0, anchor=tk.NW, image=bg_photo)

    # Calcul Dijkstra
    shortest_path, total_distance = dijkstra(start_station, end_station, graph_data["arc"])

    # Convertir le chemin le plus court en un set de tuples pour un accès rapide
    path_set = set(zip(shortest_path, shortest_path[1:]))

    transparent_lines = Image.new("RGBA", (image_width, image_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(transparent_lines)

    for arc in graph_data["arc"]:
        origine = graph_data["vertex"][arc["origine"]]["position"]
        destination = graph_data["vertex"][arc["destination"]]["position"]
        direction = arc["direction"]

        if origine is None:
            print(f"Station {arc['origine']} sans position du chemin {arc}")
            continue
        if destination is None:
            print(f"Station {arc['destination']} sans position du chemin {arc}")
            continue
        if not (0 <= origine[0] < image_width and 0 <= origine[1] < image_height):
            print(f"Coordonnées d'origine hors limites: {origine}")
            continue
        if not (0 <= destination[0] < image_width and 0 <= destination[1] < image_height):
            print(f"Coordonnées de destination hors limites: {destination}")
            continue

        line_color_map = {
            "1": "#ffcd00",
            "2": "#003ca6",
            "3": "#837902",
            "4": "#cf009e",
            "5": "#ff7e2e",
            "6": "#6eca97",
            "7": "#fa9aba",
            "8": "#e37ed1",
            "9": "#b6bd00",
            "10": "#c9910d",
            "11": "#704b1c",
            "12": "#007852",
            "13": "#6ec4e8",
            "14": "#62259d",
            "3bis": "#7ba3dc",
            "7bis": "#00c4b3"
        }
        color = line_color_map.get(graph_data["vertex"][arc["origine"]]["station_ligne"], "red")
        rgb_color = hex_to_rgb(color)

        if (arc["origine"], arc["destination"]) in path_set or (arc["destination"], arc["origine"]) in path_set:
            path_color = color
            width = 4

            # Dessiner les arcs du chemin le plus court avec opacité normale
            if direction == 0:
                canvas.create_line(origine[0], origine[1], destination[0], destination[1], fill=path_color, width=width)
            elif direction == 1:
                canvas.create_line(origine[0], origine[1], destination[0], destination[1], fill=path_color, width=width,
                                   arrow=tk.LAST)
            elif direction == 2:
                canvas.create_line(destination[0], destination[1], origine[0], origine[1], fill=path_color, width=width,
                                   arrow=tk.LAST)

        else:
            # Dessiner les arcs normaux sur l'image transparente avec transparence basse
            if direction == 0:
                draw.line([origine[0], origine[1], destination[0], destination[1]], fill=rgb_color + (64,), width=2)
            elif direction == 1:
                draw.line([origine[0], origine[1], destination[0], destination[1]], fill=rgb_color + (64,),
                          width=2)  # Transparence basse
            elif direction == 2:
                draw.line([destination[0], destination[1], origine[0], origine[1]], fill=rgb_color + (64,),
                          width=2)  # Transparence basse

    transparent_lines_photo = ImageTk.PhotoImage(transparent_lines)
    canvas.create_image(0, 0, anchor=tk.NW, image=transparent_lines_photo)

    # Dessiner les stations
    for station_id, station_data in graph_data["vertex"].items():
        position = station_data["position"]
        if position:
            canvas.create_oval(position[0] - 2, position[1] - 2, position[0] + 2, position[1] + 2, fill="black")

    root.mainloop()
