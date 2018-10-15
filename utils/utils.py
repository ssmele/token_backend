import logging
import os
import traceback
from datetime import datetime

from flask import g, jsonify


USE_ETH = True if os.getenv('ETH_GETS', 'False') == 'True' else False
logging.basicConfig(format='{time} LOG_%(levelname)s: %(message)s'.format(time=str(datetime.now())),
                    filename='/tmp/log/toker.log', level=logging.DEBUG)


LOG_DEBUG = logging.debug
LOG_INFO = logging.info
LOG_WARNING = logging.warning
LOG_ERROR = logging.error
LOG_CRITICAL = logging.critical


def log_kv(log_level, data, exception=False):
    """ Logs a dictionary of key/value pairs at the given logging level

    :param log_level: The level at which to log (LOG_DEBUG, LOG_INFO, LOG_WARNING, LOG_ERROR, or LOG_CRITICAL)
    :param data: The dictionary of elements to log
    :param exception: True if we should log a traceback, False otherwise - DEFAULT: False
    """
    # Add the traceback if specified
    if exception:
        data['trace_back'] = traceback.format_exc()

    if hasattr(g, 'log_id'):
        data['request_id'] = g.log_id

    # Build the message to log and log it
    log_str = ''
    for key, val in data.items():
        log_str += f'\"{key}\"=\"{val}\" '
    log_level(log_str)


# For some reason
def success_response(resp_data=None, status="Success", status_code=0, http_code=200):
    log_kv(LOG_DEBUG, {'message': 'about to send response', 'status_code': status_code, 'http_code': http_code,
                       'status': status})
    try:
        resp_data = {} if not resp_data else resp_data
        resp = jsonify(success_response_dict(resp_data, status, status_code))
        resp.status_code = http_code
        return resp
    except Exception as e:
        log_kv(LOG_ERROR, {'error': 'could not build successful response', 'exception': str(e)})
        raise e


def success_response_dict(resp_data=None, status="Success", status_code=0):
    resp_data = {} if not resp_data else resp_data
    return {'resp_data': resp_data, 'status': status, 'status_code': status_code}


def error_response(status="Error", status_code=-1, http_code=400, **kwargs):
    log_kv(LOG_WARNING, {'warning': 'returning error response', 'status': status, 'status_code': status_code,
                         'http_code': http_code, **kwargs})
    try:
        resp = jsonify({'status': status, 'status_code': status_code, **kwargs})
        resp.status_code = http_code
        return resp
    except Exception as e:
        log_kv(LOG_ERROR, {'error': 'could not build error response', 'exception': str(e)})
        raise e
