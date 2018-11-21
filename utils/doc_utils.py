from json import dumps


class BlueprintDocumentation:
    """
    This method is used to decorate blueprint api files in order to create documentations after.
    """

    def __init__(self, bp, bp_name):
        self.blueprint = bp
        self.bp_name = bp_name
        self.registered_endpoints = {}

    class Endpoint:

        def __init__(self, endpoint, endpoint_type, description,
                     input_schema=None, output_schema=None, url_params=None, req_i_jwt=False, req_c_jwt=False,
                     error_codes=None):
            self.endpoint = endpoint
            self.endpoint_type = endpoint_type
            self.description = description
            self.input_schema = input_schema.doc_load_info if input_schema is not None else None
            if output_schema and hasattr(output_schema, 'doc_dump_info'):
                self.output_schema = output_schema.doc_dump_info
            elif isinstance(output_schema, dict):
                self.output_schema = output_schema
            else:
                self.output_schema = None
            self.url_params = url_params
            self.req_i_jwt = req_i_jwt
            self.req_c_jwt = req_c_jwt
            self.error_codes = error_codes

    def document(self, endpoint: object, endpoint_type: object, description: object,
                 input_schema: object = None, output_schema: object = None, url_params: object = None, req_i_jwt: object = False, req_c_jwt: object = False,
                 error_codes: object = None):
        """
        This method is used for documenting blueprint endpoints.
        :param endpoint: Name of endpoint.
        :param endpoint_type: Type of HTTP Method.
        :param description: Description of what endpoint does.
        :param input_schema: Input Schema for the input parameters. Will look at doc_info on schema for info.
        :param output_schema: Output Schema for the output results. Will look at doc_info on schema for info.
        :param url_params:
        :param req_i_jwt: If the method requires issuer verification.
        :param req_c_jwt: If the method requires collector verification.
        :param error_codes: Dict containing error codes and reason for failure.
        :return:
        """
        # If we have already seen the endpoint then dont do anything.
        if (endpoint, endpoint_type) in self.registered_endpoints:
            pass

        def decorator(endpoint_func):
            self.registered_endpoints[(endpoint, endpoint_type)] = self.Endpoint(endpoint,
                                                                                 endpoint_type,
                                                                                 description,
                                                                                 input_schema,
                                                                                 output_schema,
                                                                                 url_params,
                                                                                 req_i_jwt,
                                                                                 req_c_jwt,
                                                                                 error_codes)
            return endpoint_func
        return decorator


def to_pretty_json(value):
    """Method jinja uses for parsing data objects to html parsable json"""
    if value is None:
        return "Not defined yet."
    return dumps(value, sort_keys=False, indent=4, separators=(',', ': '))
