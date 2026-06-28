import os

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    config_path_arg = DeclareLaunchArgument(
        "config_path",
        default_value="/tmp/rpi_v3_mono_config_generated.yaml",
        description="Path to the generated VINS configuration file",
    )

    generated_config_path = LaunchConfiguration("config_path")

    vins_pkg = get_package_share_directory("vins")
    imu_publisher_pkg = get_package_share_directory("imu_publisher")

    generator_script = os.path.join(vins_pkg, "launch", "generate_vins_config.py")

    import subprocess

    generated_config_path_str = "/tmp/rpi_v3_mono_config_generated.yaml"
    subprocess.run(["python3", generator_script, generated_config_path_str], check=True)

    mavros_starter = ExecuteProcess(
        cmd=[os.path.join(imu_publisher_pkg, "launch", "start_mavros.sh")],
        output="screen",
        shell=True,
    )

    imu_bridge_node = Node(
        package="imu_publisher", executable="imu_bridge", name="imu_bridge", output="screen"
    )

    camera_publisher_node = Node(
        package="camera_publisher",
        executable="camera_publisher",
        name="camera_publisher",
        output="screen",
    )

    vins_estimator_node = Node(
        package="vins",
        executable="vins_node",
        arguments=[generated_config_path_str],
        name="vins_estimator",
        output="screen",
    )

    loop_fusion_node = Node(
        package="loop_fusion",
        executable="loop_fusion_node",
        arguments=[generated_config_path_str],
        name="loop_fusion",
        output="screen",
    )

    nodes_to_launch = [
        config_path_arg,
        mavros_starter,
        imu_bridge_node,
        camera_publisher_node,
        vins_estimator_node,
        loop_fusion_node,
    ]

    try:
        get_package_share_directory("depth_publisher")
        depth_publisher_node = Node(
            package="depth_publisher",
            executable="depth_publisher_node",
            name="depth_publisher",
            output="screen",
        )
        nodes_to_launch.append(depth_publisher_node)
        print("[complete_vio.launch.py] depth_publisher package found - will launch depth node")
    except PackageNotFoundError:
        print("[complete_vio.launch.py] depth_publisher package not found - skipping depth node")

    return LaunchDescription(nodes_to_launch)
