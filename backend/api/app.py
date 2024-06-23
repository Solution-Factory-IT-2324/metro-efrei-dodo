from flask import Flask
import backend.api.routes.stations as stations


def run(port=8080, debug=True):
    app = Flask(__name__)
    app.register_blueprint(stations.bp)

    app.run(port=port, debug=debug)
