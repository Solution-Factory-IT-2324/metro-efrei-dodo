from flask import Blueprint
from backend.api.services.data import get_all_metro_stations, get_stations_by_line_metro, is_station_accessible
from backend.api.utils.response import json_response
from backend.api.utils.cache import get_cache, set_cache

bp = Blueprint('stations', __name__, url_prefix='/api/stations')


@bp.route('/', methods=['GET'])
def list_metro_stations():
    cache_file = 'metro_stations.json'
    cache_data = get_cache(cache_file, max_age_seconds=3600)

    if cache_data is not None:
        return json_response(data=cache_data, message='Success - Cached file used')

    try:
        metro_stations = get_all_metro_stations()
        set_cache(cache_file, metro_stations)
        return json_response(data=metro_stations, message='Success')
    except Exception as e:
        return json_response(message=f"Error getting metro stations: {str(e)}", status=500)


@bp.route('/line/metro/<line_short_name>', methods=['GET'])
def list_stations_by_line_metro(line_short_name):
    cache_file = f'line_stations_{line_short_name}.json'
    cache_data = get_cache(cache_file, max_age_seconds=60)

    if cache_data is not None:
        return json_response(data=cache_data, message='Success - Cached file used')

    try:
        stations = get_stations_by_line_metro(line_short_name)
        set_cache(cache_file, stations)
        return json_response(data=stations, message='Success')
    except Exception as e:
        return json_response(message=f"Error getting stations for line {line_short_name}: {str(e)}", status=500)


@bp.route('/wheelchair/<station_id>', methods=['GET'])
def is_station_wheelchair_accessible(station_id):
    try:
        accessibility_info = is_station_accessible(station_id)
        if accessibility_info is not None:
            return json_response(data=accessibility_info, message='Success')
        else:
            return json_response(message=f"Station {station_id} not found", status=404)
    except Exception as e:
        return json_response(message=f"Error checking accessibility for station {station_id}: {str(e)}", status=500)