from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'config_file',
            default_value='/home/fishnos/CINE-Sensing/configs/gyroscope/comms.yaml',
            description='Path to the configuration file'
        ),

        Node(
            package='fc_data',
            executable='gyroscope_publisher',
            name='gyroscope_publisher',
            output='screen',
            parameters=[LaunchConfiguration('config_file')]
        ),

        Node(
            package='fc_data',
            executable='vio_publisher',
            name='vio_publisher',
            output='screen'
        )
    ])
