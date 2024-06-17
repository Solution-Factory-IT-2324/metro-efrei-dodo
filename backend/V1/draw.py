import tkinter as tk
from PIL import Image, ImageTk


def draw_graph(graph_data):
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


    for arc in graph_data["arc"]:
        origine = graph_data["vertex"][arc["origine"]]["position"]
        destination = graph_data["vertex"][arc["destination"]]["position"]
        direction = arc["direction"]

        if not (0 <= origine[0] < image_width and 0 <= origine[1] < image_height):
            print(f"Coordonnées d'origine hors limites: {origine}")
            continue
        if not (0 <= destination[0] < image_width and 0 <= destination[1] < image_height):
            print(f"Coordonnées de destination hors limites: {destination}")
            continue

        # Mettre un rond pour chaque station
        canvas.create_oval(origine[0] - 2, origine[1] - 2, origine[0] + 2, origine[1] + 2, fill="black")

        match (graph_data["vertex"][arc["origine"]]["station_ligne"]):
            case "1":
                color = "#ffcd00"
            case "2":
                color = "#003ca6"
            case "3":
                color = "#837902"
            case "4":
                color = "#cf009e"
            case "5":
                color = "#ff7e2e"
            case "6":
                color = "#6eca97"
            case "7":
                color = "#fa9aba"
            case "8":
                color = "#e37ed1"
            case "9":
                color = "#b6bd00"
            case "10":
                color = "#c9910d"
            case "11":
                color = "#704b1c"
            case "12":
                color = "#007852"
            case "13":
                color = "#6ec4e8"
            case "14":
                color = "#62259d"
            case "3bis":
                color = "#7ba3dc"
            case "7bis":
                color = "#00c4b3"
            case _:
                color = "red"

        if direction == 0:
            canvas.create_line(origine[0], origine[1], destination[0], destination[1], fill=color, width=2)
        elif direction == 1:
            canvas.create_line(origine[0], origine[1], destination[0], destination[1], fill=color, width=2, arrow=tk.LAST)
        elif direction == 2:
            canvas.create_line(destination[0], destination[1], origine[0], origine[1], fill=color, width=2, arrow=tk.LAST)

    root.mainloop()

