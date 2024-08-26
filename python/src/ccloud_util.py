from typing import Any, Dict

from yaml import load, dump
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

def read_config_file(config_file_name: str) -> Dict[str, Any]:
    try:
        with open(config_file_name, 'r') as fs:
            return load(fs, Loader=Loader)
    except OSError:
        pass
    raise Exception(f'Unable to open config file "{config_file_name}"')
