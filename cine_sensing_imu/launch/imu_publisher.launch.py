"""IMU publisher launch file.

The gyroscope serial-link parameters default to `config/gyroscope/comms.yaml` in the
`cine_sensing_config` share directory. That file is distinct from the MAVROS
`comms.yaml` installed by `cine_sensing_imu` itself.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'config_file',
                default_value=PathJoinSubstitution(
                    [FindPackageShare('cine_sensing_config'), 'config', 'gyroscope', 'comms.yaml']
                ),
                description='Absolute path to the gyroscope serial-link comms.yaml.',
            ),
            Node(
                package='cine_sensing_imu',
                executable='gyroscope_publisher',
                name='gyroscope_publisher',
                output='screen',
                parameters=[LaunchConfiguration('config_file')],
            ),
            Node(
                package='cine_sensing_imu',
                executable='vio_publisher',
                name='vio_publisher',
                output='screen',
            ),
        ]
    )
