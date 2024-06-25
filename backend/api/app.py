from flask import Flask
import backend.api.routes.stations as stations
import backend.api.routes.graph as graph


def run(port=8080, debug=True):
    app = Flask(__name__)
    app.register_blueprint(stations.bp)
    app.register_blueprint(graph.bp)

    # Print all routes
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        line = f"{rule.endpoint:50s} {methods:20s} {str(rule)}"
        output.append(line)
    for out in sorted(output):
        print(out)

    app.run(port=port, debug=debug)
