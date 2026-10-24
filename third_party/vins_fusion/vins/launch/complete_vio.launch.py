"""Live VIO launch: MAVROS, IMU bridge, camera, VINS estimator and loop fusion.

The VINS config is regenerated from cine_sensing_config on every launch into
`config_path`. `profile:=<name>` selects a config profile (see the README); it is
exported as CINE_SENSING_PROFILE before the generator runs, so the generator and
every node started here read the same profile.

The estimator and loop fusion start `vins_start_delay` seconds after the sensors, so
MAVROS and the camera are already publishing when VINS initialises. `use_depth:=true`
also starts `cine_depth` (from the CINE repository) on this machine; it is off by default
because the depth model normally runs on a separate GPU machine on the same ROS network.
"""

import os
import subprocess

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _generate_config_and_start_nodes(context):
    profile = LaunchConfiguration('profile').perform(context)
    generated_config_path = LaunchConfiguration('config_path').perform(context)
    vins_start_delay = float(LaunchConfiguration('vins_start_delay').perform(context))
    os.environ['CINE_SENSING_PROFILE'] = profile

    generator_script = os.path.join(
        get_package_share_directory('vins'), 'launch', 'generate_vins_config.py'
    )
    subprocess.run(['python3', generator_script, generated_config_path], check=True)

    imu_publisher_share_directory = get_package_share_directory('cine_sensing_imu')
    mavros_starter = ExecuteProcess(
        cmd=[os.path.join(imu_publisher_share_directory, 'launch', 'start_mavros.sh')],
        output='screen',
        shell=True,
    )

    imu_bridge_node = Node(
        package='cine_sensing_imu',
        executable='imu_bridge',
        name='imu_bridge',
        output='screen',
        parameters=[{'use_transform': LaunchConfiguration('use_transform')}],
    )

    camera_publisher_node = Node(
        package='cine_sensing_camera',
        executable='camera_publisher',
        name='camera_publisher',
        output='screen',
    )

    vins_estimator_node = Node(
        package='vins',
        executable='vins_node',
        arguments=[generated_config_path],
        name='vins_estimator',
        output='screen',
    )

    loop_fusion_node = Node(
        package='loop_fusion',
        executable='loop_fusion_node',
        arguments=[generated_config_path],
        name='loop_fusion',
        output='screen',
    )

    nodes_to_launch = [
        mavros_starter,
        imu_bridge_node,
        camera_publisher_node,
        TimerAction(period=vins_start_delay, actions=[vins_estimator_node, loop_fusion_node]),
    ]

    if LaunchConfiguration('use_depth').perform(context).lower() == 'true':
        try:
            get_package_share_directory('cine_depth')
        except PackageNotFoundError as error:
            raise RuntimeError(
                'use_depth:=true, but cine_depth is not installed in this workspace'
            ) from error
        depth_publisher_node = Node(
            package='cine_depth',
            executable='depth_publisher_node',
            name='depth_publisher',
            output='screen',
        )
        nodes_to_launch.append(depth_publisher_node)

    return nodes_to_launch


def generate_launch_description():
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

    vins_start_delay_arg = DeclareLaunchArgument(
        'vins_start_delay',
        default_value='5.0',
        description='Seconds to wait after the sensors start before starting VINS',
    )

    use_transform_arg = DeclareLaunchArgument(
        'use_transform',
        default_value='false',
        description='Remap IMU axes in imu_bridge (unvalidated on hardware; see README)',
    )

    use_depth_arg = DeclareLaunchArgument(
        'use_depth',
        default_value='false',
        description='Also start cine_depth here; normally it runs on a separate GPU machine',
    )

    return LaunchDescription(
        [
            config_path_arg,
            profile_arg,
            vins_start_delay_arg,
            use_transform_arg,
            use_depth_arg,
            OpaqueFunction(function=_generate_config_and_start_nodes),
        ]
    )
