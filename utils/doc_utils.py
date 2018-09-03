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

        def __init__(self, endpoint, endpoint_type, description, input_schema=None, output_schema=None, url_params=None):
            self.endpoint = endpoint
            self.endpoint_type = endpoint_type
            self.description = description
            self.input_schema = input_schema.doc_load_info if input_schema is not None else None
            self.output_schema = output_schema.doc_dump_info if output_schema is not None else None
            self.url_params = url_params

    def document(self, endpoint, endpoint_type, description, input_schema=None, output_schema=None, url_params=None):
        """
        This method is used for documenting blueprint endpoints.
        :param endpoint: Name of endpoint.
        :param endpoint_type: Type of HTTP Method.
        :param description: Description of what endpoint does.
        :param input_schema: Input Schema for the input parameters. Will look at doc_info on schema for info.
        :param output_schema: Output Schema for the output results. Will look at doc_info on schema for info.
        :param url_params:
        :return:
        """
        def decorator(endpoint_func):
            self.registered_endpoints[endpoint] = self.Endpoint(endpoint, endpoint_type, description,
                                                                input_schema, output_schema, url_params)
            return endpoint_func
        return decorator


def to_pretty_json(value):
    """Method jinja uses for parsing data objects to html parsable json"""
    if value is None:
        return "Not defined yet."
    return dumps(value, sort_keys=False, indent=4, separators=(',', ': '))
