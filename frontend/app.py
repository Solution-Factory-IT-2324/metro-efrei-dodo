from flask import Flask, send_from_directory
import matplotlib
matplotlib.use('Agg')  # Utilise le backend 'Agg' (pour les sorties en fichier) au lieu de 'interagg'

import matplotlib.pyplot as plt

import os

app = Flask(__name__)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


@app.route('/generate-image', methods=['GET'])
def generate_image():
    # Générer une image avec matplotlib
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])

    # Chemin pour enregistrer l'image
    image_path = os.path.join('static/images', 'plot.png')
    fig.savefig(image_path)

    return "Image generated"


if __name__ == '__main__':
    # Assurez-vous que le dossier existe
    os.makedirs('static/images', exist_ok=True)
    app.run(debug=True)
