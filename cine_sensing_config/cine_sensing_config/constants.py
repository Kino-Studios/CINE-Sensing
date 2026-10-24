"""Typed constant classes built from the JSON config files.

Every value comes from `cine_sensing_config.load`; the defaults below only cover a key
missing from a file that exists. A missing or malformed file raises at import time.
"""

from collections.abc import Callable
from pathlib import Path, PurePosixPath

from cine_sensing_config import load


def package_share_directory(package_name: str) -> str:
    """Return the installed share directory of `package_name`.

    Raises LookupError when the package is not installed or ROS is not on the path.
    """
    try:
        from ament_index_python.packages import (
            PackageNotFoundError,
            get_package_share_directory,
        )
    except ImportError as error:
        raise LookupError('ament_index_python is not importable') from error

    try:
        return get_package_share_directory(package_name)
    except PackageNotFoundError as error:
        raise LookupError(f'package {package_name!r} is not installed') from error


def resolve_package_relative_path(
    path_text: str,
    share_directory_lookup: Callable[[str], str] = package_share_directory,
) -> str:
    """Resolve `<package>/<relative path>` against that package's share directory.

    The JSON stores paths such as `cine_sensing_yolo/models/<weights>.pt`, whose first
    segment is a package name. An empty or absolute path, a bare file name such as the
    stock `yolo11n.pt`, or a path whose first segment is not an installed package is
    returned unchanged.
    """
    if not path_text or Path(path_text).is_absolute():
        return path_text

    package_name, *remaining_segments = PurePosixPath(path_text).parts
    if not remaining_segments:
        return path_text

    try:
        share_directory = share_directory_lookup(package_name)
    except LookupError:
        return path_text

    return str(Path(share_directory, *remaining_segments))


_user_params = load('user_params')
_camera_config = load('camera')
_gyroscope_config = load('gyroscope')
_vins_config = load('vins')


class ModelDetectionConstants:
    _data = _user_params.get('ModelDetectionConstants', {})

    MODEL_PATH = resolve_package_relative_path(_data.get('MODEL_PATH', ''))
    CAMERA_IMAGE_TOPIC = _data.get('CAMERA_IMAGE_TOPIC', '/camera/image_color')
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

    USER_OBJECT_ID = _data.get('USER_OBJECT_ID', 56)


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
    COLOR_TOPIC = _data.get('color_topic', '/camera/image_color')
    CAMERA_INFO_TOPIC = _data.get('camera_info_topic', '/camera/camera_info')
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


class VinsConfig:
    _data = _vins_config.get('vins_config', {})

    IMU = _data.get('imu', 1)
    NUM_OF_CAM = _data.get('num_of_cam', 1)
    IMU_TOPIC = _data.get('imu_topic', '/imu_bridge/data_raw')
    IMAGE0_TOPIC = _data.get('image0_topic', '/camera/image_raw')
    OUTPUT_PATH = _data.get('output_path', '.ros/vins_output/')
    CAM0_CALIB = _data.get('cam0_calib', 'cam0_wide.yaml')
    ESTIMATE_EXTRINSIC = _data.get('estimate_extrinsic', 0)
    BODY_T_CAM0 = _data.get('body_T_cam0', {})
    MULTIPLE_THREAD = _data.get('multiple_thread', 1)
    FEATURE_TRACKER = _data.get('feature_tracker', 1)
    MIN_PARALLAX = _data.get('min_parallax', 10.0)
    MAX_CNT = _data.get('max_cnt', 150)
    MIN_DIST = _data.get('min_dist', 30)
    FREQ = _data.get('freq', 30)
    F_THRESHOLD = _data.get('F_threshold', 1.0)
    DETECT_THRESHOLD = _data.get('detect_threshold', 10)
    SHOW_TRACK = _data.get('show_track', 1)
    FLOW_BACK = _data.get('flow_back', 1)
    EQUALIZE = _data.get('equalize', 0)
    CLAHE_CLIP = _data.get('clahe_clip', 3.0)
    PYRAMID_LEVELS = _data.get('pyramid_levels', 5)
    WIN_SIZE = _data.get('win_size', 25)
    KEYFRAME_PARALLAX = _data.get('keyframe_parallax', 10.0)
    ACC_N = _data.get('acc_n', 0.1)
    GYR_N = _data.get('gyr_n', 0.01)
    ACC_W = _data.get('acc_w', 0.00002)
    GYR_W = _data.get('gyr_w', 0.00002)
    G_NORM = _data.get('g_norm', 9.81)
    GRAVITY_ALIGNED = _data.get('gravity_aligned', 1)
    ESTIMATE_TD = _data.get('estimate_td', 1)
    TD = _data.get('td', 0.0)
    TR = _data.get('tr', 0.0)
    LOOP_CLOSURE = _data.get('loop_closure', 1)
    LOAD_PREVIOUS_POSE_GRAPH = _data.get('load_previous_pose_graph', 0)
    POSE_GRAPH_SAVE_PATH = _data.get('pose_graph_save_path', '.ros/vins_output/pose_graph/')
    SAVE_IMAGE = _data.get('save_image', 0)
    USE_DEPTH = _data.get('use_depth', 0)
    DEPTH_TOPIC = _data.get('depth_topic', '/depth_publisher/depth')


__all__ = [
    'ModelDetectionConstants',
    'UserRequestedParameters',
    'RuleOfThirdsConstants',
    'CameraConfig',
    'GyroscopeConfig',
    'VinsConfig',
    'package_share_directory',
    'resolve_package_relative_path',
]
