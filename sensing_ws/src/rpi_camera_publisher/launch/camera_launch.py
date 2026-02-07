from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


import sys
from configs.python import CameraConfig

def generate_launch_description():
    camera_id_arg = DeclareLaunchArgument(
        'camera_id',
        default_value=str(CameraConfig.CAMERA_ID),
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
        default_value=CameraConfig.CAMERA_TOPIC,
        description='Topic name for publishing raw images'
    )

    camera_info_topic_arg = DeclareLaunchArgument(
        'camera_info_topic',
        default_value=CameraConfig.CAMERA_INFO_TOPIC,
        description='Topic name for publishing camera info'
    )

    frame_id_arg = DeclareLaunchArgument(
        'frame_id',
        default_value=CameraConfig.CAMERA_FRAME_ID,
        description='Frame ID for camera optical frame'
    )

    save_latest_frame_arg = DeclareLaunchArgument(
        'save_latest_frame',
        default_value='false',
        description='Whether to save the latest frame to disk'
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
                'save_latest_frame': LaunchConfiguration('save_latest_frame'),
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
        save_latest_frame_arg,

        launch_info,

        camera_publisher_node,
        static_transform_node,
        optical_transform_node,
    ])
