import importlib
import importlib.util
import json
from pathlib import Path

import yaml

GENERATOR_PATH = Path(__file__).resolve().parents[2] / 'launch' / 'generate_vins_config.py'
SHIPPED_CONFIG_DIRECTORY = Path(__file__).resolve().parents[5] / 'cine_sensing_config' / 'config'
CAMERA_VALUES = {
    'model_type': 'PINHOLE',
    'camera_name': 'test_camera',
    'image_width': 1152,
    'image_height': 648,
    'distortion_parameters': {'k1': -0.1, 'k2': 0.05, 'p1': 0.001, 'p2': 0.002},
    'projection_parameters': {'fx': 123.5, 'fy': 124.5, 'cx': 576.0, 'cy': 324.0},
}


def _load_generator(monkeypatch, config_directory, profile):
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(config_directory))
    monkeypatch.setenv('CINE_SENSING_PROFILE', profile)
    importlib.reload(importlib.import_module('cine_sensing_config.constants'))
    spec = importlib.util.spec_from_file_location('generate_vins_config', GENERATOR_PATH)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    return generator


def _read_opencv_yaml(path):
    text = Path(path).read_text()

    return yaml.safe_load(text.removeprefix('%YAML:1.0\n'))


def _config_directory_with_camera_profile(tmp_path):
    config_directory = tmp_path / 'config'
    profile_directory = config_directory / 'profiles' / 'test_camera'
    profile_directory.mkdir(parents=True)
    for name in ('camera', 'gyroscope', 'user_params', 'vins'):
        (config_directory / f'{name}.json').write_text(
            (SHIPPED_CONFIG_DIRECTORY / f'{name}.json').read_text()
        )
    (profile_directory / 'vins_camera.json').write_text(json.dumps(CAMERA_VALUES))

    return config_directory


def _fake_vins_share_directory(tmp_path):
    share_directory = tmp_path / 'share' / 'vins'
    camera_directory = share_directory / 'config' / 'rpi_camera_v3'
    camera_directory.mkdir(parents=True)
    (camera_directory / 'cam0_wide.yaml').write_text('%YAML:1.0\n---\nmodel_type: PINHOLE\n')

    return share_directory


def test_generated_config_parses_as_yaml(tmp_path, monkeypatch):
    generator = _load_generator(monkeypatch, _config_directory_with_camera_profile(tmp_path), 'test_camera')
    output_path = tmp_path / 'out' / 'vins.yaml'

    generator.generate_config(str(output_path))

    assert _read_opencv_yaml(output_path)['image0_topic'] == '/camera/image_raw'


def test_generated_config_carries_the_do_not_edit_banner_naming_its_source(tmp_path, monkeypatch):
    generator = _load_generator(monkeypatch, _config_directory_with_camera_profile(tmp_path), 'test_camera')
    output_path = tmp_path / 'out' / 'vins.yaml'

    generator.generate_config(str(output_path))

    banner = output_path.read_text()
    assert 'GENERATED FILE - DO NOT EDIT BY HAND' in banner
    assert 'cine_sensing_config/config/vins.json' in banner
    assert 'Profile: test_camera' in banner


def test_profile_camera_values_become_the_camera_yaml_vins_reads(tmp_path, monkeypatch):
    generator = _load_generator(monkeypatch, _config_directory_with_camera_profile(tmp_path), 'test_camera')
    output_path = tmp_path / 'out' / 'vins.yaml'

    generator.generate_config(str(output_path))

    cam0_calib = _read_opencv_yaml(output_path)['cam0_calib']
    camera = _read_opencv_yaml(output_path.parent / cam0_calib)
    assert camera['projection_parameters']['fx'] == 123.5
    assert camera['distortion_parameters']['k1'] == -0.1


def test_without_profile_camera_values_vins_reads_the_installed_cam0_wide(tmp_path, monkeypatch):
    generator = _load_generator(monkeypatch, SHIPPED_CONFIG_DIRECTORY, '')
    share_directory = _fake_vins_share_directory(tmp_path)
    output_path = tmp_path / 'out' / 'vins.yaml'

    generator.generate_config(str(output_path), {'vins': str(share_directory)}.__getitem__)

    cam0_calib = _read_opencv_yaml(output_path)['cam0_calib']
    assert not Path(cam0_calib).is_absolute()
    assert (output_path.parent / cam0_calib).resolve() == (
        share_directory / 'config' / 'rpi_camera_v3' / 'cam0_wide.yaml'
    ).resolve()


def test_generated_config_omits_the_unread_intrinsics_keys(tmp_path, monkeypatch):
    generator = _load_generator(monkeypatch, _config_directory_with_camera_profile(tmp_path), 'test_camera')
    output_path = tmp_path / 'out' / 'vins.yaml'

    generator.generate_config(str(output_path))

    assert 'cam0_intrinsics' not in _read_opencv_yaml(output_path)
