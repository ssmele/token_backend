from flask import jsonify


def success_response(resp_data, status="Success", status_code=0, http_code=200):
    return jsonify({'resp_data': resp_data, 'status': status, 'status_code': status_code}), http_code
