import json
from flask import Blueprint
from backend.api.utils.response import json_response
from backend.api.utils.cache import get_cache, set_cache
from backend.api.services.data import get_graph_data

bp = Blueprint('graph', __name__, url_prefix='/api/graph')


@bp.route('/', methods=['GET'])
def get_graph():
    cache_file = 'graph.json'
    cache_data = get_cache(cache_file, max_age_seconds=25200)

    if cache_data is not None:
        return json_response(data=cache_data, message='Success - Cached file used')

    try:
        graph = get_graph_data()
        set_cache(cache_file, graph)
        return json_response(data=graph, message='Success')
    except Exception as e:
        return json_response(message=f"Error getting graph: {str(e)}", status=500)
