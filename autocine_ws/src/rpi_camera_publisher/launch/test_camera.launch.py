#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rpi_camera_publisher',
            executable='camera_publisher',
            name='camera_publisher',
            output='screen',
            parameters=[{
                'publish_rate': 2.0,
            }]
        ),
    ])