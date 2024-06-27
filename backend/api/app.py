from flask import Flask, send_from_directory
import backend.api.routes.stations as stations
import backend.api.routes.graph as graph
import backend.api.routes.line as line
import backend.api.routes.journey as journey


def run(port=8080, debug=True):
    app = Flask(__name__, static_folder='../../frontend', static_url_path='')

    app.register_blueprint(line.bp)
    app.register_blueprint(stations.bp)
    app.register_blueprint(graph.bp)
    app.register_blueprint(journey.bp)

    @app.route('/<path:path>', methods=['GET'])
    def static_proxy(path):
        return send_from_directory(app.static_folder, path)

    @app.route('/', methods=['GET'])
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    # Print all routes
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        output.append(f"{rule.endpoint:50s} {methods:20s} {str(rule)}")
    for out in sorted(output):
        print(out)

    app.run(port=port, debug=debug)