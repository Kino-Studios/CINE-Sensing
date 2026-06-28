"""Deterministic VIO replay launch.

Mirrors complete_vio.launch.py's config flow (regenerate from configs/json/vins.json
into /tmp, pass to vins_node + loop_fusion_node), but the sensor stream comes from a
recorded rosbag instead of live camera/IMU. Identical inputs every run -> comparable
drift metrics. The live sensor nodes (mavros, imu_bridge, camera_publisher) are
intentionally NOT started; the bag already carries /camera/image_raw and
/imu_bridge/data_raw.
"""

import os
import subprocess

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    bag_arg = DeclareLaunchArgument("bag", description="Path to the canonical mcap bag directory")
    rate_arg = DeclareLaunchArgument("rate", default_value="1.0")

    bag = LaunchConfiguration("bag")
    rate = LaunchConfiguration("rate")

    vins_pkg = get_package_share_directory("vins")
    generator_script = os.path.join(vins_pkg, "launch", "generate_vins_config.py")

    # Same generated config the canonical launcher uses, from the one source of truth.
    generated_config_path_str = "/tmp/rpi_v3_mono_config_generated.yaml"
    subprocess.run(["python3", generator_script, generated_config_path_str], check=True)

    use_sim_time = {"use_sim_time": True}

    vins_estimator_node = Node(
        package="vins",
        executable="vins_node",
        arguments=[generated_config_path_str],
        name="vins_estimator",
        parameters=[use_sim_time],
        output="screen",
    )

    loop_fusion_node = Node(
        package="loop_fusion",
        executable="loop_fusion_node",
        arguments=[generated_config_path_str],
        name="loop_fusion",
        parameters=[use_sim_time],
        output="screen",
    )

    # --clock so /odometry timestamps follow the recorded stream deterministically.
    bag_play = ExecuteProcess(
        cmd=["ros2", "bag", "play", bag, "--clock", "--rate", rate],
        output="screen",
    )

    return LaunchDescription(
        [
            bag_arg,
            rate_arg,
            vins_estimator_node,
            loop_fusion_node,
            bag_play,
        ]
    )
