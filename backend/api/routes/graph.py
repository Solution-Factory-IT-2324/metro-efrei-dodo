import json
from flask import Blueprint
from datetime import datetime
from backend.api.utils.response import json_response
from backend.api.utils.cache import get_cache, set_cache
from backend.api.services.data import get_graph_data, get_is_graph_connected, prim_algorithm, kruskal_algorithm, update_graph_with_real_time

bp = Blueprint('graph', __name__, url_prefix='/api/graph')


@bp.route('/', methods=['GET'])
def get_graph():
    cache_file = 'graph.json'
    cache_data = get_cache(cache_file, max_age_seconds=604800)

    if cache_data is not None:
        return json_response(data=cache_data, message='Success - Cached file used')

    try:
        graph = get_graph_data()
        set_cache(cache_file, graph)
        return json_response(data=graph, message='Success')
    except Exception as e:
        return json_response(message=f"Error getting graph: {str(e)}", status=500)


@bp.route('/real-time/<datetime_str>', methods=['GET'])
def get_real_time_graph(datetime_str):
    cache_file = 'graph_real_time.json'
    cache_data = get_cache(cache_file, max_age_seconds=43200)

    if cache_data is not None:
        return json_response(data=cache_data, message='Success - Cached file used')

    try:
        graph_data = get_cache('graph.json', max_age_seconds=604800)
        if graph_data is None:
            graph_data = get_graph_data()
            set_cache("graph.json", graph_data)

        if datetime:
            current_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        else:
            current_datetime = datetime.now()
        from time import time
        start = time()
        real_time_graph = update_graph_with_real_time(graph_data, current_datetime)
        print(f"Time taken: {time() - start}s")
        set_cache(cache_file, real_time_graph)
        return json_response(data=real_time_graph, message='Success')
    except Exception as e:
        return json_response(message=f"Error getting real-time graph: {str(e)}", status=500)


@bp.route('/is-connected/<option>', methods=['GET'])
def is_graph_connected(option):
    # cache_file = 'graph_is_connected.json'
    # cache_data = get_cache(cache_file, max_age_seconds=3660)

    # if cache_data is not None:
    #    return json_response(data=cache_data, message='Success - Cached file used')

    try:
        # Get graph
        graph_data = get_cache('graph.json', max_age_seconds=604800)
        if graph_data is None:
            graph_data = get_graph_data()
            set_cache("graph.json", graph_data)

        # Check if graph is connected
        from time import time
        start = time()
        is_connected = get_is_graph_connected(graph_data, option)
        return json_response(data={'result': is_connected, 'method': option}, message='Success')
    except Exception as e:
        return json_response(message=f"Error checking graph connectivity: {str(e)}", status=500)


@bp.route('/is-connected/', methods=['GET'])
def is_graph_connected_default():
    return is_graph_connected('bfs')


@bp.route('/tree-structure/<option>', methods=['GET'])
def get_tree_structure(option):
    cache_file = f'tree_structure_{option}.json'
    cache_data = get_cache(cache_file, max_age_seconds=604800)

    if cache_data is not None:
        return json_response(data=cache_data, message='Success - Cached file used')

    try:
        # Get graph
        graph_data = get_cache('graph.json', max_age_seconds=604800)
        if graph_data is None:
            graph_data = get_graph_data()
            set_cache("graph.json", graph_data)

        # Check if graph is connected
        from time import time
        start = time()
        match option:
            case 'prim':
                tree_structure = prim_algorithm(graph_data)
            case 'kruskal':
                tree_structure = kruskal_algorithm(graph_data)
            case _:
                raise ValueError(f"Invalid option: {option}")
        print(f"Time taken: {time() - start}s")
        # set_cache(f"tree_structure_{option}.json", tree_structure)
        return json_response(data=tree_structure, message='Success')
    except Exception as e:
        return json_response(message=f"Error getting tree structure: {str(e)}", status=500)


@bp.route('/tree-structure/', methods=['GET'])
def get_tree_structure_default():
    return get_tree_structure('prim')
