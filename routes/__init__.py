from flask import request, jsonify
from functools import wraps
from marshmallow import ValidationError


def make_error_response(message, status_code=400, **kwargs):
    response = jsonify(message=message, **kwargs)
    response.status_code = status_code

    return response


def load_with_schema(schema_cls, **schema_kwargs):
    """
    This decorator parsers fields in the request to the schema given.
    :param schema_cls:
    :param schema_kwargs:
    :return:
    """
    def outer(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            schema = schema_cls(**schema_kwargs)
            json = request.get_json(force=True)
            try:
                data = schema.load(json)
                return f(data=data, *args, **kwargs)
            except ValidationError as err:
                return make_error_response('Validation Failed', errors=err.messages)

        return wrapper
    return outer
