"""Deterministic VIO replay launch.

Mirrors complete_vio.launch.py's config flow (regenerate from
cine_sensing_config/config/vins.json, or the profile chosen with `profile:=`, into
`config_path`, pass it to vins_node + loop_fusion_node), but the sensor stream comes
from a recorded rosbag instead of live camera/IMU. Identical inputs every run ->
comparable drift metrics. The live sensor nodes (mavros, imu_bridge, camera_publisher)
are intentionally NOT started; the bag already carries /camera/image_raw and
/imu_bridge/data_raw.
"""

import os
import subprocess

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _generate_config_and_start_replay(context):
    profile = LaunchConfiguration('profile').perform(context)
    generated_config_path = LaunchConfiguration('config_path').perform(context)
    os.environ['CINE_SENSING_PROFILE'] = profile

    generator_script = os.path.join(
        get_package_share_directory('vins'), 'launch', 'generate_vins_config.py'
    )
    subprocess.run(['python3', generator_script, generated_config_path], check=True)

    use_sim_time = {'use_sim_time': True}

    vins_estimator_node = Node(
        package='vins',
        executable='vins_node',
        arguments=[generated_config_path],
        name='vins_estimator',
        parameters=[use_sim_time],
        output='screen',
    )

    loop_fusion_node = Node(
        package='loop_fusion',
        executable='loop_fusion_node',
        arguments=[generated_config_path],
        name='loop_fusion',
        parameters=[use_sim_time],
        output='screen',
    )

    # --clock so /odometry timestamps follow the recorded stream deterministically.
    bag_play = ExecuteProcess(
        cmd=[
            'ros2',
            'bag',
            'play',
            LaunchConfiguration('bag'),
            '--clock',
            '--rate',
            LaunchConfiguration('rate'),
        ],
        output='screen',
    )

    return [vins_estimator_node, loop_fusion_node, bag_play]


def generate_launch_description():
    bag_arg = DeclareLaunchArgument('bag', description='Path to the canonical mcap bag directory')
    rate_arg = DeclareLaunchArgument('rate', default_value='1.0')
    config_path_arg = DeclareLaunchArgument(
        'config_path',
        default_value='/tmp/rpi_v3_mono_config_generated.yaml',
        description='Where to write the generated VINS configuration file',
    )
    profile_arg = DeclareLaunchArgument(
        'profile',
        default_value=os.environ.get('CINE_SENSING_PROFILE', ''),
        description='cine_sensing_config profile to use; empty means the base files only',
    )

    return LaunchDescription(
        [
            bag_arg,
            rate_arg,
            config_path_arg,
            profile_arg,
            OpaqueFunction(function=_generate_config_and_start_replay),
        ]
    )
