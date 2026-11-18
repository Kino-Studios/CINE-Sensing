"""Shared CINE-Sensing configuration, read from the JSON files this package installs.

A profile (`CINE_SENSING_PROFILE`) is a directory under `profiles/` whose files replace
same-named base files whole. The typed constant classes in `cine_sensing_config.constants`
are re-exported here lazily, so importing this package reads no file.
"""

import importlib
import json
import os
from pathlib import Path

CONFIG_DIRECTORY_ENVIRONMENT_VARIABLE = 'CINE_SENSING_CONFIG_DIR'
PROFILE_ENVIRONMENT_VARIABLE = 'CINE_SENSING_PROFILE'
PROFILES_DIRECTORY_NAME = 'profiles'

_CONSTANT_CLASS_NAMES = (
    'CameraConfig',
    'GyroscopeConfig',
    'ModelDetectionConstants',
    'RuleOfThirdsConstants',
    'UserRequestedParameters',
    'VinsConfig',
)


def config_directory() -> Path:
    """Return `CINE_SENSING_CONFIG_DIR` when set, else this package's installed config."""

    override_directory = os.environ.get(CONFIG_DIRECTORY_ENVIRONMENT_VARIABLE)
    if override_directory:
        return Path(override_directory)

    from ament_index_python.packages import get_package_share_directory

    return Path(get_package_share_directory('cine_sensing_config')) / 'config'


def active_profile() -> str:
    """Return the profile named by `CINE_SENSING_PROFILE`, or '' for the base files."""

    return os.environ.get(PROFILE_ENVIRONMENT_VARIABLE, '')


def profile_directory(profile: str) -> Path:
    """Return the directory of `profile`; raise ValueError when it does not exist."""

    directory = config_directory() / PROFILES_DIRECTORY_NAME / profile
    if not directory.is_dir():
        raise ValueError(f'Unknown config profile {profile!r}: {directory} does not exist')

    return directory


def config_file_path(name: str) -> Path:
    """Return the file `load(name)` reads: the active profile's copy, else the base file."""

    profile = active_profile()
    if profile:
        profile_file = profile_directory(profile) / f'{name}.json'
        if profile_file.is_file():
            return profile_file

    return config_directory() / f'{name}.json'


def load(name: str) -> dict:
    """Return `<name>.json` as a dict, the active profile's copy first.

    Raises FileNotFoundError when neither exists, ValueError for malformed JSON or an
    unknown profile.
    """

    config_path = config_file_path(name)
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
    'PROFILE_ENVIRONMENT_VARIABLE',
    'active_profile',
    'config_directory',
    'config_file_path',
    'load',
    'profile_directory',
    *_CONSTANT_CLASS_NAMES,
]
