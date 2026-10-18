import json

import pytest

import cine_sensing_config


def test_load_reads_json_from_override_directory(tmp_path, monkeypatch):
    (tmp_path / 'camera.json').write_text(json.dumps({'width': 640}))
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(tmp_path))
    assert cine_sensing_config.load('camera') == {'width': 640}


def test_load_missing_file_names_the_file(tmp_path, monkeypatch):
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(tmp_path))
    with pytest.raises(FileNotFoundError, match='camera.json'):
        cine_sensing_config.load('camera')


def test_load_malformed_json_names_the_file(tmp_path, monkeypatch):
    (tmp_path / 'camera.json').write_text('{not json')
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(tmp_path))
    with pytest.raises(ValueError, match='camera.json'):
        cine_sensing_config.load('camera')
