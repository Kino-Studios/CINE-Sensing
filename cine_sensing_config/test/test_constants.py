import importlib
import json
from pathlib import Path

SHIPPED_CONFIG_DIRECTORY = Path(__file__).resolve().parents[1] / 'config'


def _write_minimal_config_directory(directory, camera_parameters):
    (directory / 'camera.json').write_text(
        json.dumps({'camera_publisher': {'ros__parameters': camera_parameters}})
    )
    (directory / 'gyroscope.json').write_text('{}')
    (directory / 'user_params.json').write_text('{}')
    (directory / 'vins.json').write_text('{}')


def _fresh_constants_module():
    return importlib.reload(importlib.import_module('cine_sensing_config.constants'))


def test_constant_classes_read_values_from_the_config_directory(tmp_path, monkeypatch):
    _write_minimal_config_directory(tmp_path, {'image_width': 640})
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(tmp_path))

    constants = _fresh_constants_module()

    assert constants.CameraConfig.IMAGE_WIDTH == 640


def test_package_reexports_constant_classes_from_the_constants_module(tmp_path, monkeypatch):
    _write_minimal_config_directory(tmp_path, {'image_width': 640})
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(tmp_path))
    constants = _fresh_constants_module()

    from cine_sensing_config import CameraConfig

    assert CameraConfig is constants.CameraConfig


def test_shipped_config_files_all_load(monkeypatch):
    monkeypatch.setenv('CINE_SENSING_CONFIG_DIR', str(SHIPPED_CONFIG_DIRECTORY))

    constants = _fresh_constants_module()

    assert constants.ModelDetectionConstants.BOUNDING_BOX_TOPIC == '/object_detection/bounding_box'


def test_package_relative_path_resolves_under_that_package_share_directory():
    from cine_sensing_config.constants import resolve_package_relative_path

    share_directories = {
        'cine_sensing_yolo': '/opt/ws/install/cine_sensing_yolo/share/cine_sensing_yolo'
    }

    resolved_path = resolve_package_relative_path(
        'cine_sensing_yolo/models/detector.pt', share_directories.__getitem__
    )

    assert (
        resolved_path
        == '/opt/ws/install/cine_sensing_yolo/share/cine_sensing_yolo/models/detector.pt'
    )


def test_path_whose_first_segment_is_not_a_package_is_returned_unchanged():
    from cine_sensing_config.constants import resolve_package_relative_path

    resolved_path = resolve_package_relative_path('not_a_package/detector.pt', {}.__getitem__)

    assert resolved_path == 'not_a_package/detector.pt'


def test_absolute_path_is_returned_unchanged():
    from cine_sensing_config.constants import resolve_package_relative_path

    resolved_path = resolve_package_relative_path('/models/detector.pt', {}.__getitem__)

    assert resolved_path == '/models/detector.pt'


def test_bare_model_name_is_returned_without_a_package_lookup():
    from cine_sensing_config.constants import resolve_package_relative_path

    def lookup_rejecting_the_name(package_name):
        raise ValueError(f'{package_name!r} is not a valid package name')

    resolved_path = resolve_package_relative_path('yolo11n.pt', lookup_rejecting_the_name)

    assert resolved_path == 'yolo11n.pt'
