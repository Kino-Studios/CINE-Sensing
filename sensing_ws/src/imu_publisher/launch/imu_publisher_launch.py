"""IMU publisher launch file.

Resolves the gyroscope config path via CINE_SENSING_ROOT env var (preferred)
or by walking up from __file__ to the repo root as a fallback.  The config
lives at <repo_root>/configs/gyroscope/comms.yaml and is NOT installed into
the package share directory (it is distinct from the MAVROS comms.yaml that
lives in imu_publisher/config/).
"""

import os
import pathlib

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _default_config_path() -> str:
    """Return absolute path to configs/gyroscope/comms.yaml.

    Priority:
    1. CINE_SENSING_ROOT env var
    2. Sentinel walk: find the repo root by locating sensing_ws/ from __file__
    """
    root = os.environ.get("CINE_SENSING_ROOT", "")
    if root:
        return os.path.join(root, "configs", "gyroscope", "comms.yaml")

    # Walk up from this file: .../sensing_ws/src/imu_publisher/launch/__file__
    # parents: [0]=launch [1]=imu_publisher [2]=src [3]=sensing_ws
    this_file = pathlib.Path(__file__).resolve()
    sensing_ws_dir = this_file.parents[3]
    # configs/ lives at the repo root, i.e. one level above sensing_ws/.
    return str(sensing_ws_dir.parent / "configs" / "gyroscope" / "comms.yaml")


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument(
            "config_file",
            default_value=_default_config_path(),
            description=(
                "Absolute path to gyroscope comms.yaml.  "
                "Override with CINE_SENSING_ROOT env var or pass explicitly."
            ),
        ),

        Node(
            package="imu_publisher",
            executable="gyroscope_publisher",
            name="gyroscope_publisher",
            output="screen",
            parameters=[LaunchConfiguration("config_file")],
        ),

        Node(
            package="imu_publisher",
            executable="vio_publisher",
            name="vio_publisher",
            output="screen",
        ),
    ])
