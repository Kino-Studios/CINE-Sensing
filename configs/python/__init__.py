import json
import os
from pathlib import Path

_CONFIG_DIR = Path(__file__).parent.parent / 'json'


def _load_json(filename: str) -> dict:
    json_path = _CONFIG_DIR / filename
    if not json_path.exists():
        raise FileNotFoundError(f"Config file not found: {json_path}")
    with open(json_path, 'r') as f:
        return json.load(f)

_user_params = _load_json('user_params.json')
_camera_config = _load_json('camera.json')
_gyroscope_config = _load_json('gyroscope.json')

class ModelDetectionConstants:
    _data = _user_params.get('ModelDetectionConstants', {})

    MODEL_PATH = _data.get('MODEL_PATH', '')
    CAMERA_IMAGE_TOPIC = _data.get('CAMERA_IMAGE_TOPIC', '/camera/image_raw')
    BOUNDING_BOX_TOPIC = _data.get('BOUNDING_BOX_TOPIC', '/object_detection/bounding_box')
    IMAGE_ENCODING = _data.get('IMAGE_ENCODING', 'bgr8')
    IMAGE_DIR = _data.get('IMAGE_DIR', '~/object_detection_images')
    OBB_COORDS_LENGTH = _data.get('OBB_COORDS_LENGTH', 8)
    NUM_BOUNDING_BOX_POINTS = _data.get('NUM_BOUNDING_BOX_POINTS', 4)
    QOS_DEPTH = _data.get('QOS_DEPTH', 10)
    QOS_RELIABILITY = _data.get('QOS_RELIABILITY', 'RELIABLE')
    QOS_DURABILITY = _data.get('QOS_DURABILITY', 'VOLATILE')
    QOS_HISTORY = _data.get('QOS_HISTORY', 'KEEP_LAST')
    CONFIDENCE_THRESHOLD = _data.get('CONFIDENCE_THRESHOLD', 0.25)
    IOU_THRESHOLD = _data.get('IOU_THRESHOLD', 0.4)

class UserRequestedParameters:
    _data = _user_params.get('UserRequestedParameters', {})

    USER_OBJECT_ID = _data.get('USER_OBJECT_ID', 2)

class RuleOfThirdsConstants:
    _data = _user_params.get('RuleOfThirdsConstants', {})

    FRAME_WIDTH = _data.get('FRAME_WIDTH', 1152)
    FRAME_HEIGHT = _data.get('FRAME_HEIGHT', 648)
    GRID_LINE_1_X = _data.get('GRID_LINE_1_X', FRAME_WIDTH / 3.0)
    GRID_LINE_2_X = _data.get('GRID_LINE_2_X', 2 * FRAME_WIDTH / 3.0)
    GRID_LINE_1_Y = _data.get('GRID_LINE_1_Y', FRAME_HEIGHT / 3.0)
    GRID_LINE_2_Y = _data.get('GRID_LINE_2_Y', 2 * FRAME_HEIGHT / 3.0)

    ANCHOR_POINTS = [tuple(pt) for pt in _data.get('ANCHOR_POINTS', [])]
    CORE_ANCHOR_POINTS = [tuple(pt) for pt in _data.get('CORE_ANCHOR_POINTS', [])]

class CameraConfig:
    _data = _camera_config.get('camera_publisher', {}).get('ros__parameters', {})

    CAMERA_ID = _data.get('camera_id', 0)
    IMAGE_WIDTH = _data.get('image_width', 1920)
    IMAGE_HEIGHT = _data.get('image_height', 1080)
    FPS = _data.get('fps', 30.0)
    IMAGE_FORMAT = _data.get('image_format', 'BGR8')
    JPEG_QUALITY = _data.get('jpeg_quality', 95)
    CAMERA_TOPIC = _data.get('camera_topic', '/camera/image_raw')
    CAMERA_INFO_TOPIC = _data.get('camera_info_topic', '/camera/camera_info')
    CAMERA_MATRIX = _data.get('camera_matrix', {}).get('data', [])
    DISTORTION_COEFFICIENTS = _data.get('distortion_coefficients', {}).get('data', [])
    CAMERA_FRAME_ID = _data.get('camera_frame_id', 'camera_optical_frame')
    AUTO_EXPOSURE = _data.get('auto_exposure', True)
    EXPOSURE_TIME_US = _data.get('exposure_time_us', 10000)
    ANALOG_GAIN = _data.get('analog_gain', 1.0)
    DIGITAL_GAIN = _data.get('digital_gain', 1.0)
    WHITE_BALANCE_AUTO = _data.get('white_balance_auto', True)
    WHITE_BALANCE_RED_GAIN = _data.get('white_balance_red_gain', 1.0)
    WHITE_BALANCE_BLUE_GAIN = _data.get('white_balance_blue_gain', 1.0)
    BUFFER_SIZE = _data.get('buffer_size', 1)
    PUBLISH_RATE = _data.get('publish_rate', 30.0)

class GyroscopeConfig:
    _data = _gyroscope_config.get('gyroscope_data_publisher', {}).get('ros__parameters', {})

    BAUD_RATE = _data.get('baud_rate', 921600)
    SERIAL_PORT = _data.get('serial_port', '/dev/ttyAMA0')
    SERIAL_PORT_BAUD_RATE = _data.get('serial_port_baud_rate', 921600)

__all__ = [
    'ModelDetectionConstants',
    'UserRequestedParameters',
    'RuleOfThirdsConstants',
    'CameraConfig',
    'GyroscopeConfig'
]
