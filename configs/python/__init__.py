import json
import os
from pathlib import Path

_CONFIG_DIR = Path(__file__).parent.parent / "json"


def _repo_root() -> Path:
    """Return repo root via CINE_SENSING_ROOT env var, or resolve from fixed depth.

    This file lives at <repo_root>/configs/python/__init__.py, so the repo
    root is two directory levels up (parents[2]). Used to resolve repo-relative
    paths stored in the JSON source of truth into absolute paths for runtime consumers.
    """
    root_env = os.environ.get("CINE_SENSING_ROOT", "")
    if root_env:
        return Path(root_env)

    return Path(__file__).resolve().parents[2]


def _load_json(filename: str) -> dict:
    json_path = _CONFIG_DIR / filename
    if not json_path.exists():
        raise FileNotFoundError(f"Config file not found: {json_path}")

    with open(json_path, "r") as file_handle:
        return json.load(file_handle)


_user_params = _load_json("user_params.json")
_camera_config = _load_json("camera.json")
_gyroscope_config = _load_json("gyroscope.json")
_vins_config = _load_json("vins.json")


def _resolve_model_path(rel_or_abs: str) -> str:
    """Resolve a repo-relative MODEL_PATH from JSON into an absolute path.

    The JSON source stores the path relative to the repo root (see the
    "_note" key in user_params.json). An empty value is passed through
    unchanged, and an already-absolute path is left as-is.
    """
    if not rel_or_abs:
        return rel_or_abs

    candidate = Path(rel_or_abs)
    if candidate.is_absolute():
        return str(candidate)

    return str(_repo_root() / candidate)


class ModelDetectionConstants:
    _data = _user_params.get("ModelDetectionConstants", {})

    MODEL_PATH = _resolve_model_path(_data.get("MODEL_PATH", ""))
    CAMERA_IMAGE_TOPIC = _data.get("CAMERA_IMAGE_TOPIC", "/camera/image_raw")
    BOUNDING_BOX_TOPIC = _data.get("BOUNDING_BOX_TOPIC", "/object_detection/bounding_box")
    IMAGE_ENCODING = _data.get("IMAGE_ENCODING", "bgr8")
    IMAGE_DIR = _data.get("IMAGE_DIR", "~/object_detection_images")
    OBB_COORDS_LENGTH = _data.get("OBB_COORDS_LENGTH", 8)
    NUM_BOUNDING_BOX_POINTS = _data.get("NUM_BOUNDING_BOX_POINTS", 4)
    QOS_DEPTH = _data.get("QOS_DEPTH", 10)
    QOS_RELIABILITY = _data.get("QOS_RELIABILITY", "RELIABLE")
    QOS_DURABILITY = _data.get("QOS_DURABILITY", "VOLATILE")
    QOS_HISTORY = _data.get("QOS_HISTORY", "KEEP_LAST")
    CONFIDENCE_THRESHOLD = _data.get("CONFIDENCE_THRESHOLD", 0.25)
    IOU_THRESHOLD = _data.get("IOU_THRESHOLD", 0.4)


class UserRequestedParameters:
    _data = _user_params.get("UserRequestedParameters", {})

    USER_OBJECT_ID = _data.get("USER_OBJECT_ID", 2)


class RuleOfThirdsConstants:
    _data = _user_params.get("RuleOfThirdsConstants", {})

    FRAME_WIDTH = _data.get("FRAME_WIDTH", 1152)
    FRAME_HEIGHT = _data.get("FRAME_HEIGHT", 648)
    GRID_LINE_1_X = _data.get("GRID_LINE_1_X", FRAME_WIDTH / 3.0)
    GRID_LINE_2_X = _data.get("GRID_LINE_2_X", 2 * FRAME_WIDTH / 3.0)
    GRID_LINE_1_Y = _data.get("GRID_LINE_1_Y", FRAME_HEIGHT / 3.0)
    GRID_LINE_2_Y = _data.get("GRID_LINE_2_Y", 2 * FRAME_HEIGHT / 3.0)

    ANCHOR_POINTS = [tuple(pt) for pt in _data.get("ANCHOR_POINTS", [])]
    CORE_ANCHOR_POINTS = [tuple(pt) for pt in _data.get("CORE_ANCHOR_POINTS", [])]


class CameraConfig:
    _data = _camera_config.get("camera_publisher", {}).get("ros__parameters", {})

    CAMERA_ID = _data.get("camera_id", 0)
    IMAGE_WIDTH = _data.get("image_width", 1920)
    IMAGE_HEIGHT = _data.get("image_height", 1080)
    FPS = _data.get("fps", 30.0)
    IMAGE_FORMAT = _data.get("image_format", "BGR8")
    JPEG_QUALITY = _data.get("jpeg_quality", 95)
    CAMERA_TOPIC = _data.get("camera_topic", "/camera/image_raw")
    CAMERA_INFO_TOPIC = _data.get("camera_info_topic", "/camera/camera_info")
    CAMERA_MATRIX = _data.get("camera_matrix", {}).get("data", [])
    DISTORTION_COEFFICIENTS = _data.get("distortion_coefficients", {}).get("data", [])
    CAMERA_FRAME_ID = _data.get("camera_frame_id", "camera_optical_frame")
    AUTO_EXPOSURE = _data.get("auto_exposure", True)
    EXPOSURE_TIME_US = _data.get("exposure_time_us", 10000)
    ANALOG_GAIN = _data.get("analog_gain", 1.0)
    DIGITAL_GAIN = _data.get("digital_gain", 1.0)
    WHITE_BALANCE_AUTO = _data.get("white_balance_auto", True)
    WHITE_BALANCE_RED_GAIN = _data.get("white_balance_red_gain", 1.0)
    WHITE_BALANCE_BLUE_GAIN = _data.get("white_balance_blue_gain", 1.0)
    BUFFER_SIZE = _data.get("buffer_size", 1)
    PUBLISH_RATE = _data.get("publish_rate", 30.0)


class GyroscopeConfig:
    _data = _gyroscope_config.get("gyroscope_data_publisher", {}).get("ros__parameters", {})

    BAUD_RATE = _data.get("baud_rate", 921600)
    SERIAL_PORT = _data.get("serial_port", "/dev/ttyAMA0")
    SERIAL_PORT_BAUD_RATE = _data.get("serial_port_baud_rate", 921600)


class VinsConfig:
    _data = _vins_config.get("vins_config", {})

    IMU = _data.get("imu", 1)
    NUM_OF_CAM = _data.get("num_of_cam", 1)
    IMU_TOPIC = _data.get("imu_topic", "/imu_bridge/data_raw")
    IMAGE0_TOPIC = _data.get("image0_topic", "/camera/image_raw")
    OUTPUT_PATH = _data.get("output_path", "CINE-Sensing/vins_output/")
    CAM0_CALIB = _data.get("cam0_calib", "cam0_wide.yaml")
    ESTIMATE_EXTRINSIC = _data.get("estimate_extrinsic", 0)
    BODY_T_CAM0 = _data.get("body_T_cam0", {})
    MULTIPLE_THREAD = _data.get("multiple_thread", 1)
    FEATURE_TRACKER = _data.get("feature_tracker", 1)
    MIN_PARALLAX = _data.get("min_parallax", 10.0)
    MAX_CNT = _data.get("max_cnt", 150)
    MIN_DIST = _data.get("min_dist", 30)
    FREQ = _data.get("freq", 30)
    F_THRESHOLD = _data.get("F_threshold", 1.0)
    DETECT_THRESHOLD = _data.get("detect_threshold", 10)
    SHOW_TRACK = _data.get("show_track", 1)
    FLOW_BACK = _data.get("flow_back", 1)
    EQUALIZE = _data.get("equalize", 0)
    CLAHE_CLIP = _data.get("clahe_clip", 3.0)
    PYRAMID_LEVELS = _data.get("pyramid_levels", 5)
    WIN_SIZE = _data.get("win_size", 25)
    KEYFRAME_PARALLAX = _data.get("keyframe_parallax", 10.0)
    ACC_N = _data.get("acc_n", 0.1)
    GYR_N = _data.get("gyr_n", 0.01)
    ACC_W = _data.get("acc_w", 0.00002)
    GYR_W = _data.get("gyr_w", 0.00002)
    G_NORM = _data.get("g_norm", 9.81)
    GRAVITY_ALIGNED = _data.get("gravity_aligned", 1)
    ESTIMATE_TD = _data.get("estimate_td", 1)
    TD = _data.get("td", 0.0)
    TR = _data.get("tr", 0.0)
    LOOP_CLOSURE = _data.get("loop_closure", 1)
    LOAD_PREVIOUS_POSE_GRAPH = _data.get("load_previous_pose_graph", 0)
    POSE_GRAPH_SAVE_PATH = _data.get("pose_graph_save_path", "CINE-Sensing/vins_output/pose_graph/")
    SAVE_IMAGE = _data.get("save_image", 0)
    USE_DEPTH = _data.get("use_depth", 0)
    DEPTH_TOPIC = _data.get("depth_topic", "/depth_publisher/depth")


__all__ = [
    "ModelDetectionConstants",
    "UserRequestedParameters",
    "RuleOfThirdsConstants",
    "CameraConfig",
    "GyroscopeConfig",
    "VinsConfig",
]
