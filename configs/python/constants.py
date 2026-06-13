"""CINE-Sensing runtime constants.

MODEL_PATH is resolved at import time: CINE_SENSING_ROOT env var (preferred),
then a sentinel walk from this file up to the repo root.  No absolute paths
are baked in here.
"""

import os
import pathlib


def _repo_root() -> pathlib.Path:
    """Return repo root via CINE_SENSING_ROOT or sentinel walk from __file__."""
    root_env = os.environ.get("CINE_SENSING_ROOT", "")
    if root_env:
        return pathlib.Path(root_env)

    # This file lives at <repo_root>/configs/python/constants.py
    # parents[0]=python  parents[1]=configs  parents[2]=repo_root
    return pathlib.Path(__file__).resolve().parents[2]


class ModelDetectionConstants:
    MODEL_PATH: str = str(
        _repo_root()
        / "sensing_ws"
        / "src"
        / "yolo_detection"
        / "models"
        / "homeobjects_yolo11n_trained.pt"
    )

    CAMERA_IMAGE_TOPIC: str = "/camera/image_raw"
    BOUNDING_BOX_TOPIC: str = "/object_detection/bounding_box"

    IMAGE_ENCODING: str = "bgr8"
    IMAGE_DIR: str = "~/object_detection_images"

    OBB_COORDS_LENGTH: int = 8
    NUM_BOUNDING_BOX_POINTS: int = 4

    QOS_DEPTH: int = 10
    QOS_RELIABILITY: str = "RELIABLE"
    QOS_DURABILITY: str = "VOLATILE"
    QOS_HISTORY: str = "KEEP_LAST"

    CONFIDENCE_THRESHOLD: float = 0.25
    IOU_THRESHOLD: float = 0.4


class UserRequestedParameters:
    # Object ID the model assigns to the tracked object (2 = chair in default model)
    USER_OBJECT_ID: int = 2


class RuleOfThirdsConstants:
    FRAME_WIDTH: int = 1152
    FRAME_HEIGHT: int = 648

    GRID_LINE_1_X: float = FRAME_WIDTH / 3.0
    GRID_LINE_2_X: float = 2 * FRAME_WIDTH / 3.0
    GRID_LINE_1_Y: float = FRAME_HEIGHT / 3.0
    GRID_LINE_2_Y: float = 2 * FRAME_HEIGHT / 3.0

    ANCHOR_POINTS: list[tuple[float, float]] = [
        (GRID_LINE_1_X, GRID_LINE_1_Y),
        (GRID_LINE_2_X, GRID_LINE_1_Y),
        (FRAME_WIDTH, GRID_LINE_1_Y),
        (GRID_LINE_1_X, GRID_LINE_2_Y),
        (GRID_LINE_2_X, GRID_LINE_2_Y),
        (FRAME_WIDTH, GRID_LINE_2_Y),
        (GRID_LINE_1_X, FRAME_HEIGHT),
        (GRID_LINE_2_X, FRAME_HEIGHT),
        (FRAME_WIDTH, FRAME_HEIGHT),
    ]

    CORE_ANCHOR_POINTS: list[tuple[float, float]] = [
        (GRID_LINE_1_X, GRID_LINE_1_Y),
        (GRID_LINE_2_X, GRID_LINE_1_Y),
        (GRID_LINE_1_X, GRID_LINE_2_Y),
        (GRID_LINE_2_X, GRID_LINE_2_Y),
    ]
