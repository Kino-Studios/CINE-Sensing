"""Shared CINE-Sensing configuration, read from the JSON files this package installs.

`load(name)` returns one JSON file as a dict. A profile, named by the
`CINE_SENSING_PROFILE` environment variable, is a directory under `profiles/` whose
files replace the base files of the same name, whole file, with no key merging. The
typed constant classes
(`CameraConfig`, `VinsConfig`, ...) live in `cine_sensing_config.constants` and are
re-exported here lazily, so importing this package never reads a file by itself.
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
    """Return the directory holding the config files.

    `CINE_SENSING_CONFIG_DIR` wins when set; otherwise the installed share
    directory of this package is used, so lookup works from any working directory.
    """
    override_directory = os.environ.get(CONFIG_DIRECTORY_ENVIRONMENT_VARIABLE)
    if override_directory:
        return Path(override_directory)

    from ament_index_python.packages import get_package_share_directory

    return Path(get_package_share_directory('cine_sensing_config')) / 'config'


def active_profile() -> str:
    """Return the profile named by `CINE_SENSING_PROFILE`, or '' for the base files."""

    return os.environ.get(PROFILE_ENVIRONMENT_VARIABLE, '')


def profile_directory(profile: str) -> Path:
    """Return the directory of `profile`.

    Raises ValueError naming the profile when no such directory exists.
    """
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
    """Return the `<name>.json` config file as a dict.

    The active profile's copy wins over the base file. Raises FileNotFoundError when
    neither exists, ValueError when the file is not valid JSON or the profile is
    unknown; the messages carry the full path.
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
