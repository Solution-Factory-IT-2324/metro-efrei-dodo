from flask import Blueprint, request
from backend.api.services.data import dijkstra
from backend.api.utils.cache import get_cache
from backend.api.utils.response import json_response

bp = Blueprint('journey', __name__, url_prefix='/api/journey')


@bp.route('/', methods=['POST'])
def get_journey_from_to():
    # Load graph from cache
    cache_file = 'graph.json'
    graph_data = get_cache(cache_file, max_age_seconds=25200)

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
        return json_response(data={'path': path, 'distance': distance}, message='Success')
    except Exception as e:
        return json_response(message=f"Error calculating journey: {str(e)}", status=500)


@bp.route('/emission/<journey_id>', methods=['GET'])
def get_journey_emission(journey_id):
    # Get factors from cache
    cache_file = 'emission_factors.json'
    emission_data = get_cache(cache_file, max_age_seconds=604800)

    if emission_data is None:
        emission_data = get_emission_factors()
        set_cache(cache_file, emission_data)

    journey_data = get_cache(f'{journey_id}.json', max_age_seconds=25660)
    if journey_data is None:
        return json_response(message=f'Journey data with ID {journey_id} not available', status=500)

    graph_data = get_cache('graph.json', max_age_seconds=604800)
    if graph_data is None:
        return json_response(message='Graph data not available', status=500)

    try:
        emission_journey_public_transport, emission_journey_car, distance = emission_calculator(journey_data['path'], emission_data, graph_data)
        return json_response(data={'emission_journey_public_transport': emission_journey_public_transport,
                                   'emission_journey_car': emission_journey_car,
                                   'journey_id': journey_id,
                                   'distance': distance,
                                   'Unit emission': 'g CO2 eq.',
                                   'Unit distance': 'km'
                                   }, message='Success')
    except Exception as e:
        return json_response(message=f"Error calculating journey emission: {str(e)}", status=500)


@bp.route('/emission', methods=['GET'])
def get_emission():
    cache_file = 'emission_factors.json'
    emission_data = get_cache(cache_file, max_age_seconds=604800)

    if emission_data is None:
        return json_response(message='Emission factors not available', status=500)

    try:
        data = get_emission_factors()
        set_cache(cache_file, data)
        return json_response(data=data, message='Success')
    except Exception as e:
        return json_response(message=f"Error fetching emission factors: {str(e)}", status=500)