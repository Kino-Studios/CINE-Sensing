import importlib
import json
from pathlib import Path

import pytest

SHIPPED_CONFIG_DIRECTORY = Path(__file__).resolve().parents[1] / 'config'


@pytest.mark.parametrize('profile', ['rpi_v3_wide', 'rpi_v3_fullfov', 'rpi_v3_tune_maxcnt250'])
def test_shipped_profile_declares_a_known_status(profile):
    metadata_path = SHIPPED_CONFIG_DIRECTORY / 'profiles' / profile / 'profile.json'

    metadata = json.loads(metadata_path.read_text())

    assert metadata['status'] in {'calibrated', 'uncalibrated-candidate'}


def test_tuning_profile_feeds_its_values_to_the_vins_constants(monkeypatch):
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(SHIPPED_CONFIG_DIRECTORY))
    monkeypatch.setenv('CINE_SENSING_PROFILE', 'rpi_v3_tune_maxcnt250')

    constants = importlib.reload(importlib.import_module('cine_sensing_config.constants'))

    assert constants.VinsConfig.MAX_CNT == 250


def test_base_files_keep_the_default_vins_tuning(monkeypatch):
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(SHIPPED_CONFIG_DIRECTORY))
    monkeypatch.delenv('CINE_SENSING_PROFILE', raising=False)

    constants = importlib.reload(importlib.import_module('cine_sensing_config.constants'))

    assert constants.VinsConfig.MAX_CNT == 150
