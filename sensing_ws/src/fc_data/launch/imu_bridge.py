import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import Imu
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from configs.python import VinsConfig
except ImportError:
    VinsConfig = None

class IMUBridge(Node):
    def __init__(self):
        super().__init__('imu_bridge')

        self.declare_parameters(
            '',
            [
                ('mavros_imu_topic', '/mavros/imu/data_raw'),
                ('vins_imu_topic', VinsConfig.IMU_TOPIC if VinsConfig else '/imu_bridge/data_raw'),
                ('qos_depth', 200),
            ]
        )

        mavros_imu_topic = self.get_parameter('mavros_imu_topic').value
        vins_imu_topic = self.get_parameter('vins_imu_topic').value
        qos_depth = self.get_parameter('qos_depth').value

        mavros_qos = QoSProfile(
            depth=qos_depth,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE
        )

        vins_qos = QoSProfile(
            depth=qos_depth,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE
        )

        self.mavros_imu_sub = self.create_subscription(
            Imu,
            mavros_imu_topic,
            self.imu_callback,
            mavros_qos
        )

        self.vins_imu_pub = self.create_publisher(
            Imu,
            vins_imu_topic,
            vins_qos
        )

        self.get_logger().info(f"Bridging IMU from {mavros_imu_topic} to {vins_imu_topic}")

    def imu_callback(self, msg):
        # Frame transformation (if needed) - current implementation swaps/negates axes for VINS expectations
        # Note: In a production system, these transforms should be defined in URDF/TF2
        accel_x = msg.linear_acceleration.x
        accel_y = msg.linear_acceleration.y
        gyro_x = msg.angular_velocity.x
        gyro_y = msg.angular_velocity.y

        msg.linear_acceleration.x = accel_y
        msg.linear_acceleration.y = accel_x
        msg.linear_acceleration.z = -msg.linear_acceleration.z

        msg.angular_velocity.x = gyro_y
        msg.angular_velocity.y = gyro_x
        msg.angular_velocity.z = -msg.angular_velocity.z

        msg.header.frame_id = 'imu'

        self.vins_imu_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)

    try:
        imu_bridge = IMUBridge()
        rclpy.spin(imu_bridge)
    except KeyboardInterrupt:
        pass
    finally:
        if 'imu_bridge' in locals():
            imu_bridge.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()
