from flask import jsonify, make_response


def json_response(data=None, message='', status=200):
    response = {
        'status': status,
        'message': message,
        'data': data
    }
    return make_response(jsonify(response), status)
