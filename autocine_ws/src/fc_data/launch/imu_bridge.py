#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import Imu
import numpy as np

class IMUBridge(Node):
    def __init__(self):
        super().__init__('imu_bridge')
        
        mavros_qos = QoSProfile(
            depth=200,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE
        )
        
        vins_qos = QoSProfile(
            depth=200,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE
        )
        
        self.mavros_imu_sub = self.create_subscription(
            Imu,
            '/mavros/imu/data_raw',
            self.imu_callback,
            mavros_qos
        )
        
        self.vins_imu_pub = self.create_publisher(
            Imu,
            '/imu_bridge/data_raw',
            vins_qos
        )
        
    def imu_callback(self, msg):
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
        
        msg.header.stamp = self.get_clock().now().to_msg()
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