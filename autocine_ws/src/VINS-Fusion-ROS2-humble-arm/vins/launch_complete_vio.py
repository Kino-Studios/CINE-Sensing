import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node

def generate_launch_description():
    vins_ws = '/home/fishnos/CINE-Sensing/autocine_ws'
    config_path = os.path.join(vins_ws, 'src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/rpi_v3_mono_config.yaml')
    vins_install = os.path.join(vins_ws, 'install/vins/lib/vins/vins_node')
    loop_install = os.path.join(vins_ws, 'install/loop_fusion/lib/loop_fusion/loop_fusion_node')

    return LaunchDescription([
        ExecuteProcess(
            cmd=['bash', os.path.join(vins_ws, 'src/fc_data/launch/start_mavros.sh')],
            output='screen'
        ),

        ExecuteProcess(
            cmd=['python3', os.path.join(vins_ws, 'src/fc_data/launch/imu_bridge.py')],
            output='screen'
        ),

        ExecuteProcess(
            cmd=['python3', os.path.join(vins_ws, 'src/rpi_camera_publisher/rpi_camera_publisher/camera_publisher.py')],
            output='screen'
        ),

        TimerAction(
            period=5.0,
            actions=[
                ExecuteProcess(
                    cmd=[vins_install, config_path],
                    output='screen'
                ),
            ]
        ),

        TimerAction(
            period=5.0,
            actions=[
                ExecuteProcess(
                    cmd=[loop_install, config_path],
                    output='screen'
                ),
            ]
        ),
    ])
