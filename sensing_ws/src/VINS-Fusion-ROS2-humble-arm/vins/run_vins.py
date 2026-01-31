import rclpy
from rclpy.node import Node
import subprocess
import os
import signal
import sys

class VINSRunner(Node):
    def __init__(self):
        super().__init__('vins_runner')
        self.vins_process = None
        self.loop_process = None
        self.imu_bridge_process = None
        self.start_vins()

    def start_vins(self):
        vins_ws = '/home/fishnos/CINE-Sensing/sensing_ws/src/VINS-Fusion-ROS2-humble-arm'

        os.chdir(vins_ws)

        vins_cmd = [
            'ros2', 'run', 'vins', 'vins_node',
            vins_ws + '/config/rpi_camera_v3/rpi_v3_mono_config.yaml'
        ]

        mavros_cmd = [
            'ros2', 'launch', 'mavros', 'px4.launch.py'
        ]

        imu_bridge_cmd = [
            'imu_bridge', '--ros-args', '-p', 'use_transform:=true'
        ]

        loop_cmd = [
            'ros2', 'run', 'loop_fusion', 'loop_fusion_node',
            vins_ws + '/config/rpi_camera_v3/rpi_v3_mono_config.yaml'
        ]

        try:
            env = os.environ.copy()
            env['ROS_DOMAIN_ID'] = '0'

            self.vins_process = subprocess.Popen(vins_cmd, env=env)
            self.mavros_process = subprocess.Popen(mavros_cmd, env=env)
            self.imu_bridge_process = subprocess.Popen(imu_bridge_cmd, env=env)
            self.loop_process = subprocess.Popen(loop_cmd, env=env)

            self.get_logger().info('VINS-Fusion started')

        except Exception as e:
            self.get_logger().error(f'Failed to start VINS: {str(e)}')

    def shutdown(self):
        if self.vins_process:
            self.vins_process.terminate()
        if self.imu_bridge_process:
            self.imu_bridge_process.terminate()
        if self.loop_process:
            self.loop_process.terminate()

def main(args=None):
    rclpy.init(args=args)
    runner = VINSRunner()

    def signal_handler(sig, frame):
        runner.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        rclpy.spin(runner)
    except KeyboardInterrupt:
        pass
    finally:
        runner.shutdown()
        runner.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
