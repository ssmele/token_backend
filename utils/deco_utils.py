from flask import request

TEMP_JWT = 'SECRET_AND_SEUCRE_420'


def check_jwt(some_function):
    """
    Wrapper to check for authorization header. This will soon invovle logic for decoding and encoding jwts.
    :param some_function:
    :return:
    """
    def wrapper():
        key = request.headers.get('Authorization')
        key = key.split('Bearer ')[1]
        if key != TEMP_JWT:
            print("AUTHORIZE YOUR SELF!")
        some_function()
    return wrapper
