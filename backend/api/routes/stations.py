from flask import Blueprint, jsonify
import json
from decimal import Decimal
from backend.api.services.data import get_all_metro_stations

bp = Blueprint('stations', __name__, url_prefix='/api/stations')

@bp.route('/', methods=['GET'])
def list_metro_stations():
    # Check if result is not in cache
    try:
        with open('api/services/cache/metro_stations.json', 'r') as file:
            cached_data = file.read()
            if cached_data:
                metro_stations = json.loads(cached_data)
                return jsonify(metro_stations)
    except FileNotFoundError:
        pass
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Generate the result and store it in cache
    try:
        metro_stations = get_all_metro_stations()
        with open('api/services/cache/metro_stations.json', 'w') as file:
            json.dump(metro_stations, file, default=lambda obj: float(obj) if isinstance(obj, Decimal) else obj)
        return jsonify(metro_stations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
