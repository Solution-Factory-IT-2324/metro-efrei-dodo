from flask import jsonify, make_response


def json_response(data=None, message='', status=200):
    response = {
        'status': status,
        'message': message,
        'data': data
    }

    if not data:
        response['message'] = 'No data found'
        response['status'] = 404

    return make_response(jsonify(response), status)
