from functools import wraps

import jwt
from flask import request, g

from utils.utils import error_response

SECRET_KEY = 'SECRET_420'


def generate_jwt(user):
    """
    Make a jwt out of user information.
    :param user: User information.
    :return:
    """
    alg_dict = {'alg': 'HS256'}
    user.update(alg_dict)
    return jwt.encode(user, SECRET_KEY, algorithm='HS256').decode('utf-8')


def verify_jwt(uv_jwt):
    """
    Get user information from the jwt.
    :param uv_jwt: jwt to decode.
    :return:
    """
    try:
        return jwt.decode(uv_jwt, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignature:
        return None
    except Exception:
        return None


def verify_issuer_jwt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        # Verify we something and the jwt contains the needed info.
        user_info = parse_jwt_out_of_auth()
        if not user_info or 'i_id' not in user_info:
            return error_response("Access Denied", http_code=403)

        # If we get it and its valid put it on the global request object.
        g.issuer_info = user_info
        return f(*args, **kwargs)
    return decorated_function


def verify_collector_jwt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        # Verify we something and the jwt contains the needed info.
        user_info = parse_jwt_out_of_auth()
        if not user_info or 'c_id' not in user_info:
            return error_response("Access Denied", http_code=403)

        # If we get it and its valid put it on the global request object.
        g.collector_info = user_info
        return f(*args, **kwargs)
    return decorated_function


def parse_jwt_out_of_auth():
    # Make sure we have an Authorization Header.
    if 'Authorization' in request.headers:
        parsed_jwt = request.headers['Authorization']

        try:
            # Verify the jwt has not been tampered with.
            verified_jwt = verify_jwt(parsed_jwt)
        except Exception:
            return None

        # Make sure the jwt contains information.
        if not verified_jwt:
            return None

        return verified_jwt
    else:
        return None