from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os

def generate_launch_description():
    config_path = '/home/fishnos/CINE-Sensing/autocine_ws/src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/rpi_v3_mono_config.yaml'

    return LaunchDescription([
        ExecuteProcess(
            cmd=['/home/fishnos/CINE-Sensing/autocine_ws/src/fc_data/launch/start_mavros.sh'],
            output='screen',
            shell=True
        ),

        ExecuteProcess(
            cmd=['python3', '/home/fishnos/CINE-Sensing/autocine_ws/src/fc_data/launch/imu_bridge.py'],
            output='screen'
        ),

        ExecuteProcess(
            cmd=['python3', '/home/fishnos/CINE-Sensing/autocine_ws/src/rpi_camera_publisher/rpi_camera_publisher/camera_publisher.py'],
            output='screen'
        ),

        ExecuteProcess(
            cmd=['python3', '/home/fishnos/CINE-Sensing/autocine_ws/src/depth_publisher/depth_publisher/depth_publisher_node.py'],
            output='screen'
        ),

        ExecuteProcess(
            cmd=['/home/fishnos/CINE-Sensing/autocine_ws/install/vins/lib/vins/vins_node', config_path],
            output='screen'
        ),

        ExecuteProcess(
            cmd=['/home/fishnos/CINE-Sensing/autocine_ws/install/loop_fusion/lib/loop_fusion/loop_fusion_node', config_path],
            output='screen'
        ),
    ])
