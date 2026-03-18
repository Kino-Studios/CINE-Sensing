import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import Imu
import numpy as np

class IMUBridge(Node):
    def __init__(self):
        super().__init__('imu_bridge')

        self.get_logger().info("bridge started")

        self.declare_parameter('use_transform', False)
        self.use_transform = self.get_parameter('use_transform').value

        self.mavros_imu_sub = self.create_subscription(
            Imu,
            '/mavros/imu/data_raw',
            self.imu_callback,
            qos_profile_sensor_data
        )

        vins_qos = QoSProfile(
            depth=200,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE
        )

        self.vins_imu_pub = self.create_publisher(
            Imu,
            '/imu_bridge/data_raw',
            vins_qos
        )

        self.msg_count = 0

    def imu_callback(self, msg):
        self.msg_count += 1
        if self.msg_count % 100 == 1:
            self.get_logger().info(f"Received IMU message #{self.msg_count}")

        if self.use_transform:
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

            self.get_logger().info(f'transform applied: accel {accel_x:.2f},{accel_y:.2f} -> {msg.linear_acceleration.x:.2f},{msg.linear_acceleration.y:.2f}', once=True)

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
        except Exception:
            pass

if __name__ == '__main__':
    main()
