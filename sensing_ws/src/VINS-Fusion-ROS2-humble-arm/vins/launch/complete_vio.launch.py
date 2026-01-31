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

    # Run the generator script synchronously before launching nodes
    import subprocess
    generated_config_path_str = '/tmp/rpi_v3_mono_config_generated.yaml'
    subprocess.run(['python3', generator_script, generated_config_path_str], check=True)

    # Define the nodes/processes
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
        arguments=[generated_config_path_str],
        name='vins_estimator',
        output='screen'
    )

    loop_fusion_node = Node(
        package='loop_fusion',
        executable='loop_fusion_node',
        arguments=[generated_config_path_str],
        name='loop_fusion',
        output='screen'
    )

    return LaunchDescription([
        config_path_arg,
        mavros_starter,
        imu_bridge_node,
        camera_publisher_node,
        vins_estimator_node,
        loop_fusion_node
    ])
