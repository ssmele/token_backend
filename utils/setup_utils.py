import os
import yaml


def load_config():
    """
    Reads in the yaml configuration file.
    :return: configuration object.
    """
    path = os.environ.get('BACKEND_CONFIG', "\\Users\\stone\\PycharmProjects\\TOKER\\configs\\config.sample.yml")
    with open(path) as fp:
        return yaml.load(fp)