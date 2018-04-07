from flask import jsonify


def success_response(resp_data={}, status="Success", status_code=0, http_code=200):
    return jsonify(success_response_dict(resp_data, status, status_code)), http_code


def success_response_dict(resp_data={}, status="Success", status_code=0):
    return {'resp_data': resp_data, 'status': status, 'status_code': status_code}


def error_response(status="Error", status_code=-1, http_code=400):
    return jsonify({'status': status, 'status_code': status_code}), http_code

# TODO: Make Error Handler
# TODO: Make db getter
# TODO: Make Authenticator
# TODO: Make Logger
