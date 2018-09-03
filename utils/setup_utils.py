import os

import yaml


def load_config(app_path_root):
    """
    Reads in the yaml configuration file.
    :return: configuration object.
    """
    # Figure out what environment your on to see where to append the config path at.
    config_path = os.path.join(app_path_root, 'configs', 'config.yml')
    path = os.environ.get('BACKEND_CONFIG', config_path)
    with open(path) as fp:
        return yaml.load(fp)