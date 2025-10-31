#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='depth_publisher',
            executable='depth_publisher_node',
            name='depth_publisher_node',
            output='screen',
            parameters=[
                {'model_size': 'vits'},
                {'device': 'cpu'}
            ]
        ),
        Node(
            package='depth_publisher',
            executable='depth_visualizer_node',
            name='depth_visualizer_node',
            output='screen'
        )
    ])