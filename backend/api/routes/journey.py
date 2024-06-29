from flask import Blueprint, request
from uuid import uuid4
from backend.api.services.data import dijkstra, emission_calculator, get_emission_factors
from backend.api.utils.cache import get_cache, set_cache
from backend.api.utils.response import json_response

bp = Blueprint('journey', __name__, url_prefix='/api/journey')


@bp.route('/', methods=['POST'])
def get_journey_from_to():
    # Load graph from cache
    cache_file = 'graph.json'
    graph_data = get_cache(cache_file, max_age_seconds=604800)

    if graph_data is None:
        return json_response(message='Graph data not available', status=500)

    try:
        data = request.get_json()
        start, end = data.get('start_vertex'), data.get('end_vertex')
        if not start or not end:
            return json_response(message="Start and end points are required", status=400)

        from time import time
        start_time = time()
        path, distance = dijkstra(graph_data, start, end)
        print(f"Time taken to calculate path: {time() - start_time}")
        if distance == float('infinity'):
            return json_response(data={'path': path, 'distance': distance}, message='No path found', status=404)

        # Generate ID for journey calculated
        journey_id = f"journey-{uuid4()}.json"
        set_cache(journey_id, {'path': path, 'distance': distance, 'journey_id': journey_id})
        return json_response(data={'path': path, 'distance': distance, 'journey_id': journey_id}, message='Success')
    except Exception as e:
        return json_response(message=f"Error calculating journey: {str(e)}", status=500)
