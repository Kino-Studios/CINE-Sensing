#!/usr/bin/env python3

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


class IMUChecker(Node):
    def __init__(self):
        super().__init__('imu_checker')

        self.mavros_sub = self.create_subscription(
            Imu, '/mavros/imu/data_raw', self.mavros_callback, 10
        )

        self.bridge_sub = self.create_subscription(
            Imu, '/imu_bridge/data_raw', self.bridge_callback, 10
        )

        self.get_logger().info('IMU Checker started - monitoring both MAVROS and bridge topics')

    def mavros_callback(self, msg):
        acc = msg.linear_acceleration
        gyro = msg.angular_velocity
        acc_mag = np.sqrt(acc.x**2 + acc.y**2 + acc.z**2)

        self.get_logger().info(
            f'MAVROS: acc=[{acc.x:.2f}, {acc.y:.2f}, {acc.z:.2f}] mag={acc_mag:.2f} '
            f'gyro=[{gyro.x:.3f}, {gyro.y:.3f}, {gyro.z:.3f}]'
        )

    def bridge_callback(self, msg):
        acc = msg.linear_acceleration
        gyro = msg.angular_velocity
        acc_mag = np.sqrt(acc.x**2 + acc.y**2 + acc.z**2)

        self.get_logger().info(
            f'BRIDGE: acc=[{acc.x:.2f}, {acc.y:.2f}, {acc.z:.2f}] mag={acc_mag:.2f} '
            f'gyro=[{gyro.x:.3f}, {gyro.y:.3f}, {gyro.z:.3f}]'
        )


def main(args=None):
    rclpy.init(args=args)
    checker = IMUChecker()

    try:
        rclpy.spin(checker)
    except KeyboardInterrupt:
        pass
    finally:
        checker.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
