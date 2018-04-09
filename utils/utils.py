from flask import jsonify


# For some reason
def success_response(resp_data={}, status="Success", status_code=0, http_code=200):
    resp = jsonify(success_response_dict(resp_data, status, status_code))
    resp.status_code = http_code
    return resp


def success_response_dict(resp_data={}, status="Success", status_code=0):
    return {'resp_data': resp_data, 'status': status, 'status_code': status_code}


def error_response(status="Error", status_code=-1, http_code=400):
    resp = jsonify({'status': status, 'status_code': status_code})
    resp.status_code = http_code
    return resp

# TODO: Make Error Handler
# TODO: Make db getter
# TODO: Make Authenticator
# TODO: Make Logger
