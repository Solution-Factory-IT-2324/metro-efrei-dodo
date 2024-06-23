import json
from decimal import Decimal
from flask import Blueprint
from backend.api.services.data import get_all_metro_stations, get_stations_by_line_metro
from backend.api.utils.response import json_response

bp = Blueprint('stations', __name__, url_prefix='/api/stations')


@bp.route('/', methods=['GET'])
def list_metro_stations():
    # Check if result is not in cache
    try:
        with open('api/services/cache/metro_stations.json', 'r') as file:
            cached_data = file.read()
            if cached_data:
                metro_stations = json.loads(cached_data)
                return json_response(data=metro_stations, message='Success')
    except FileNotFoundError:
        pass
    except Exception as e:
        return json_response(message=f"Error reading cache file : {str(e)}", status=500)

    # Generate the result and store it in cache
    try:
        metro_stations = get_all_metro_stations()
        with open('api/services/cache/metro_stations.json', 'w') as file:
            json.dump(metro_stations, file, default=lambda obj: float(obj) if isinstance(obj, Decimal) else obj)
        return json_response(data=metro_stations, message='Success')
    except Exception as e:
        return json_response(message=f"Error getting metro stations : {str(e)}", status=500)


@bp.route('/line/metro/<line_id>', methods=['GET'])
def list_stations_by_line_metro(line_id):
    # Check if result is not in cache
    try:
        with open(f'api/services/cache/line_stations_{line_id}.json', 'r') as file:
            cached_data = file.read()
            if cached_data:
                stations = json.loads(cached_data)
                return json_response(data=stations, message='Success')
    except FileNotFoundError:
        pass
    except Exception as e:
        return json_response(message=f"Error reading cache file : {str(e)}", status=500)
    # Generate the result and store it in cache
    try:
        stations = get_stations_by_line_metro(line_id)
        with open(f'api/services/cache/line_stations_{line_id}.json', 'w') as file:
            json.dump(stations, file)
        return json_response(data=stations, message='Success')
    except Exception as e:
        return json_response(message=f"Error getting stations for line {line_id} : {str(e)}", status=500)
