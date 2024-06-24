from flask import Flask
import backend.api.routes.stations as stations
import backend.api.routes.graph as graph


def run(port=8080, debug=True):
    app = Flask(__name__)
    app.register_blueprint(stations.bp)
    app.register_blueprint(graph.bp)

    app.run(port=port, debug=debug)
