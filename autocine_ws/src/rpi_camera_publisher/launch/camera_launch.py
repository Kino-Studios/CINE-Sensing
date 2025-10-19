#!/usr/bin/env python3
"""
Launch file for the Raspberry Pi Camera Publisher

This launch file starts the camera publisher node with the appropriate
configuration parameters.

Author: Your Name
License: MIT
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():
    """Generate launch description for camera publisher."""
    
    # Declare launch arguments
    camera_id_arg = DeclareLaunchArgument(
        'camera_id',
        default_value='0',
        description='Camera device ID (usually 0 for RPi camera)'
    )
    
    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=PathJoinSubstitution([
            FindPackageShare('rpi_camera_publisher'),
            'config',
            'camera_params.yaml'
        ]),
        description='Path to camera configuration file'
    )
    
    image_topic_arg = DeclareLaunchArgument(
        'image_topic',
        default_value='/camera/image_raw',
        description='Topic name for publishing raw images'
    )
    
    camera_info_topic_arg = DeclareLaunchArgument(
        'camera_info_topic',
        default_value='/camera/camera_info',
        description='Topic name for publishing camera info'
    )
    
    frame_id_arg = DeclareLaunchArgument(
        'frame_id',
        default_value='camera_optical_frame',
        description='Frame ID for camera optical frame'
    )
    
    camera_publisher_node = Node(
        package='rpi_camera_publisher',
        executable='camera_publisher',
        name='camera_publisher',
        output='screen',
        parameters=[
            LaunchConfiguration('config_file'),
            {
                'camera_id': LaunchConfiguration('camera_id'),
                'camera_topic': LaunchConfiguration('image_topic'),
                'camera_info_topic': LaunchConfiguration('camera_info_topic'),
                'camera_frame_id': LaunchConfiguration('frame_id'),
            }
        ],
        remappings=[
            ('/camera/image_raw', LaunchConfiguration('image_topic')),
            ('/camera/camera_info', LaunchConfiguration('camera_info_topic')),
        ]
    )
    
    static_transform_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='camera_transform_publisher',
        arguments=[
            '0', '0', '0.1',  # x, y, z translation
            '0', '0', '0', '1',  # x, y, z, w quaternion rotation
            'base_link',
            'camera_link'
        ]
    )
    
    optical_transform_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='camera_optical_transform_publisher',
        arguments=[
            '0', '0', '0',  # x, y, z translation
            '-0.5', '0.5', '-0.5', '0.5',  # 90-degree rotation around x-axis
            'camera_link',
            LaunchConfiguration('frame_id')
        ]
    )
    
    launch_info = LogInfo(
        msg=[
            'Starting Raspberry Pi Camera Publisher...\n',
            'Camera ID: ', LaunchConfiguration('camera_id'), '\n',
            'Image topic: ', LaunchConfiguration('image_topic'), '\n',
            'Camera info topic: ', LaunchConfiguration('camera_info_topic'), '\n',
            'Frame ID: ', LaunchConfiguration('frame_id')
        ]
    )
    
    return LaunchDescription([
        camera_id_arg,
        config_file_arg,
        image_topic_arg,
        camera_info_topic_arg,
        frame_id_arg,
        
        launch_info,
        
        camera_publisher_node,
        static_transform_node,
        optical_transform_node,
    ])