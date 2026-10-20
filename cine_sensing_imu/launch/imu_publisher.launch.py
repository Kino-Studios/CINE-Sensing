"""IMU publisher launch file: the gyroscope relay and the VIO pose relay.

Both nodes read MAVROS and VINS topics, so neither takes a parameters file; the
flight-controller serial link is set in `start_mavros.sh`.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package='cine_sensing_imu',
                executable='gyroscope_publisher',
                name='gyroscope_publisher',
                output='screen',
            ),
            Node(
                package='cine_sensing_imu',
                executable='vio_publisher',
                name='vio_publisher',
                output='screen',
            ),
        ]
    )
