"""Shared CINE-Sensing configuration, read from the JSON files this package installs.

`load(name)` returns one JSON file as a dict. The typed constant classes
(`CameraConfig`, `VinsConfig`, ...) live in `cine_sensing_config.constants` and are
re-exported here lazily, so importing this package never reads a file by itself.
"""

import importlib
import json
import os
from pathlib import Path

CONFIG_DIRECTORY_ENVIRONMENT_VARIABLE = 'CINE_SENSING_CONFIG_DIR'

_CONSTANT_CLASS_NAMES = (
    'CameraConfig',
    'GyroscopeConfig',
    'ModelDetectionConstants',
    'RuleOfThirdsConstants',
    'UserRequestedParameters',
    'VinsConfig',
)


def config_directory() -> Path:
    """Return the directory holding the config files.

    `CINE_SENSING_CONFIG_DIR` wins when set; otherwise the installed share
    directory of this package is used, so lookup works from any working directory.
    """
    override_directory = os.environ.get(CONFIG_DIRECTORY_ENVIRONMENT_VARIABLE)
    if override_directory:
        return Path(override_directory)

    from ament_index_python.packages import get_package_share_directory

    return Path(get_package_share_directory('cine_sensing_config')) / 'config'


def load(name: str) -> dict:
    """Return `<config directory>/<name>.json` as a dict.

    Raises FileNotFoundError when the file is absent and ValueError when it is not
    valid JSON; both messages carry the full path.
    """
    config_path = config_directory() / f'{name}.json'
    if not config_path.is_file():
        raise FileNotFoundError(f'Config file not found: {config_path}')

    with open(config_path, encoding='utf-8') as config_file:
        try:
            return json.load(config_file)
        except json.JSONDecodeError as error:
            raise ValueError(f'Malformed JSON in config file {config_path}: {error}') from error


def __getattr__(attribute_name: str):
    if attribute_name in _CONSTANT_CLASS_NAMES:
        constants_module = importlib.import_module('cine_sensing_config.constants')

        return getattr(constants_module, attribute_name)

    raise AttributeError(f'module {__name__!r} has no attribute {attribute_name!r}')


__all__ = [
    'CONFIG_DIRECTORY_ENVIRONMENT_VARIABLE',
    'config_directory',
    'load',
    *_CONSTANT_CLASS_NAMES,
]
