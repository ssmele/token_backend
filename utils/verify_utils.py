import jwt

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
    return jwt.decode(uv_jwt, SECRET_KEY, algorithms=['HS256'])