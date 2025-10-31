#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Vector3, Quaternion
from std_msgs.msg import Header
import math
import time

class FakeIMU(Node):
    def __init__(self):
        super().__init__('fake_imu')
        
        self.imu_pub = self.create_publisher(
            Imu,
            '/imu_bridge/data_raw',
            10
        )
        
        self.timer = self.create_timer(0.01, self.publish_imu)  # 100Hz
        self.start_time = time.time()
        
    def publish_imu(self):
        msg = Imu()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "imu_link"
        
        # Simulate some realistic IMU data
        t = time.time() - self.start_time
        
        # Simulate slight rotation (quaternion for small angles)
        msg.orientation.w = math.cos(0.01 * math.sin(t * 0.1))
        msg.orientation.x = 0.0
        msg.orientation.y = 0.0  
        msg.orientation.z = math.sin(0.01 * math.sin(t * 0.1))
        
        # Simulate gyroscope (small random motion)
        msg.angular_velocity.x = 0.01 * math.sin(t * 2.0)
        msg.angular_velocity.y = 0.005 * math.cos(t * 1.5)
        msg.angular_velocity.z = 0.002 * math.sin(t * 3.0)
        
        # Simulate accelerometer (mostly gravity with small perturbations)
        msg.linear_acceleration.x = 0.1 * math.sin(t * 0.5)
        msg.linear_acceleration.y = 0.05 * math.cos(t * 0.8)
        msg.linear_acceleration.z = 9.81 + 0.02 * math.sin(t * 2.0)
        
        # Set covariances (required by VINS)
        msg.orientation_covariance[0] = 0.001
        msg.orientation_covariance[4] = 0.001
        msg.orientation_covariance[8] = 0.001
        
        msg.angular_velocity_covariance[0] = 0.0001
        msg.angular_velocity_covariance[4] = 0.0001
        msg.angular_velocity_covariance[8] = 0.0001
        
        msg.linear_acceleration_covariance[0] = 0.01
        msg.linear_acceleration_covariance[4] = 0.01
        msg.linear_acceleration_covariance[8] = 0.01
        
        self.imu_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    
    try:
        fake_imu = FakeIMU()
        print("Publishing fake IMU data to /imu_bridge/data_raw at 100Hz")
        rclpy.spin(fake_imu)
    except KeyboardInterrupt:
        pass
    finally:
        if 'fake_imu' in locals():
            fake_imu.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()