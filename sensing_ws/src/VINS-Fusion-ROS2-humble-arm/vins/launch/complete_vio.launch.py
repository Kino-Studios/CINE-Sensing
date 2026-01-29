from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    config_path_arg = DeclareLaunchArgument(
        'config_path',
        default_value='/tmp/rpi_v3_mono_config_generated.yaml',
        description='Path to the generated VINS configuration file'
    )

    generated_config_path = LaunchConfiguration('config_path')

    vins_pkg = get_package_share_directory('vins')
    fc_data_pkg = get_package_share_directory('fc_data')

    generator_script = os.path.join(vins_pkg, 'launch', 'generate_vins_config.py')

    # Define the generator process
    config_generator = ExecuteProcess(
        cmd=['python3', generator_script, generated_config_path],
        output='screen'
    )

    # Define the nodes/processes that depend on the config
    mavros_starter = ExecuteProcess(
        cmd=[os.path.join(fc_data_pkg, 'launch', 'start_mavros.sh')],
        output='screen',
        shell=True
    )

    imu_bridge_node = Node(
        package='fc_data',
        executable='imu_bridge',
        name='imu_bridge',
        output='screen'
    )

    camera_publisher_node = Node(
        package='rpi_camera_publisher',
        executable='camera_publisher',
        name='camera_publisher',
        output='screen'
    )

    vins_estimator_node = Node(
        package='vins',
        executable='vins_node',
        arguments=[generated_config_path],
        name='vins_estimator',
        output='screen'
    )

    loop_fusion_node = Node(
        package='loop_fusion',
        executable='loop_fusion_node',
        arguments=[generated_config_path],
        name='loop_fusion',
        output='screen'
    )

    # Optional: depth publisher
    depth_publisher_node = Node(
        package='depth_publisher',
        executable='depth_publisher_node',
        name='depth_publisher',
        output='screen'
    )

    # Event handler to start dependent nodes after config is generated
    start_vins_system = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_process=config_generator,
            on_exit=[
                mavros_starter,
                imu_bridge_node,
                camera_publisher_node,
                vins_estimator_node,
                loop_fusion_node,
                depth_publisher_node
            ]
        )
    )

    return LaunchDescription([
        config_path_arg,
        config_generator,
        start_vins_system
    ])
