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


def test_active_profile_file_replaces_the_base_file(tmp_path, monkeypatch):
    (tmp_path / 'vins.json').write_text(json.dumps({'max_cnt': 150}))
    profile_directory = tmp_path / 'profiles' / 'tuned'
    profile_directory.mkdir(parents=True)
    (profile_directory / 'vins.json').write_text(json.dumps({'max_cnt': 250}))
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(tmp_path))
    monkeypatch.setenv('CINE_SENSING_PROFILE', 'tuned')

    assert cine_sensing_config.load('vins') == {'max_cnt': 250}


def test_file_absent_from_the_active_profile_falls_back_to_the_base_file(tmp_path, monkeypatch):
    (tmp_path / 'camera.json').write_text(json.dumps({'width': 640}))
    (tmp_path / 'profiles' / 'tuned').mkdir(parents=True)
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(tmp_path))
    monkeypatch.setenv('CINE_SENSING_PROFILE', 'tuned')

    assert cine_sensing_config.load('camera') == {'width': 640}


def test_unknown_profile_names_the_profile(tmp_path, monkeypatch):
    (tmp_path / 'camera.json').write_text(json.dumps({'width': 640}))
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(tmp_path))
    monkeypatch.setenv('CINE_SENSING_PROFILE', 'no_such_profile')

    with pytest.raises(ValueError, match='no_such_profile'):
        cine_sensing_config.load('camera')


def test_empty_profile_reads_the_base_file(tmp_path, monkeypatch):
    (tmp_path / 'camera.json').write_text(json.dumps({'width': 640}))
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(tmp_path))
    monkeypatch.setenv('CINE_SENSING_PROFILE', '')

    assert cine_sensing_config.load('camera') == {'width': 640}
