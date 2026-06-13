#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="imu_publisher",
                executable="imu_bridge",
                name="imu_bridge",
                output="screen",
                parameters=[],
            )
        ]
    )
