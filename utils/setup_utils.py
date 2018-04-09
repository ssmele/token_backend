import yaml
import os, sys


def load_config(app_path_root):
    """
    Reads in the yaml configuration file.
    :return: configuration object.
    """
    # Figure out what environment your on to see where to append the config path at.
    platform = sys.platform
    if platform in ['linux', 'darwin']:
        config_path = app_path_root + '/configs/config.sample.yml'
    else:
        app_path_root += '\\configs\\config.sample.yml'
        config_path = app_path_root.lstrip('C:')
    path = os.environ.get('BACKEND_CONFIG', config_path)
    with open(path) as fp:
        return yaml.load(fp)