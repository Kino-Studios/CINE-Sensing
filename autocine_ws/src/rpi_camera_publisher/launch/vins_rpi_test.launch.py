#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
import os

def generate_launch_description():
    config_path = "/home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/"
    
    return LaunchDescription([
        ExecuteProcess(
            cmd=['python3', '/home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/rpi_camera_publisher/rpi_camera_publisher/camera_publisher.py'],
            name='camera_publisher',
            output='screen',
        ),
        
        ExecuteProcess(
            cmd=['bash', '-c', f'cd /home/fishnos/bspline-cinematography-generator-research/autocine_ws && source /opt/ros/jazzy/setup.bash && source install/setup.bash && /home/fishnos/bspline-cinematography-generator-research/autocine_ws/install/vins/lib/vins/vins_node {config_path}rpi_v3_mono_config.yaml'],
            name='vins_estimator',
            output='screen',
        ),
    ])