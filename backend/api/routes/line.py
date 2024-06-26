from flask import Blueprint
from backend.api.utils.response import json_response
from backend.api.utils.cache import get_cache, set_cache
from backend.api.services.data import get_all_lines_data, get_line_data_by_id, get_line_data_by_name

bp = Blueprint('line', __name__, url_prefix='/api/line')


@bp.route('/', methods=['GET'])
def get_all_routes_data():
    cache_file = 'lines.json'
    cache_data = get_cache(cache_file, max_age_seconds=25200)

    if cache_data is not None:
        return json_response(data=cache_data, message='Success - Cached file used')

    try:
        lines = get_all_lines_data()
        set_cache(cache_file, lines)
        return json_response(data=lines, message='Success')
    except Exception as e:
        return json_response(message=f"Error getting graph: {str(e)}", status=500)


@bp.route('/get-by-id/<line_id>', methods=['GET'])
def get_route_data_by_id(line_id):
    # cache_file = f'line_{line_id}_data.json'
    # cache_data = get_cache(cache_file, max_age_seconds=25200)

    # if cache_data is not None:
    #    return json_response(data=cache_data, message='Success - Cached file used')

    try:
        line = get_line_data_by_id(line_id)
        # set_cache(cache_file, line)
        return json_response(data=line, message='Success')
    except Exception as e:
        return json_response(message=f"Error getting line: {str(e)}", status=500)


@bp.route('/get-by-name/<line_short_name>', methods=['GET'])
def get_route_data_by_name(line_short_name):
    # cache_file = f'line_{line_short_name}_data.json'
    # cache_data = get_cache(cache_file, max_age_seconds=25200)

    # if cache_data is not None:
    #    return json_response(data=cache_data, message='Success - Cached file used')

    try:
        line = get_line_data_by_name(line_short_name)
        # set_cache(cache_file, line)
        return json_response(data=line, message='Success')
    except Exception as e:
        return json_response(message=f"Error getting line: {str(e)}", status=500)
