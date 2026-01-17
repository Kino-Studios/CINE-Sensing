#!/usr/bin/env python3
"""
Test which IMU coordinate frame is correct by checking stationary IMU readings.
When drone is sitting level on ground:
- One axis should read ~9.8 m/s² (gravity)
- Other axes should read ~0 m/s²
- Gyro should all read ~0 rad/s
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import numpy as np

class IMUFrameTest(Node):
    def __init__(self):
        super().__init__('imu_frame_test')
        
        self.mavros_sub = self.create_subscription(
            Imu, '/mavros/imu/data_raw', self.mavros_cb, 10)
        
        self.bridge_sub = self.create_subscription(
            Imu, '/imu_bridge/data_raw', self.bridge_cb, 10)
            
        self.samples = []
        self.bridge_samples = []
        
    def mavros_cb(self, msg):
        acc = msg.linear_acceleration
        mag = np.sqrt(acc.x**2 + acc.y**2 + acc.z**2)
        
        self.samples.append([acc.x, acc.y, acc.z, mag])
        
        if len(self.samples) == 50:
            avg = np.mean(self.samples, axis=0)
            print(f"\n=== MAVROS IMU (no transform) ===")
            print(f"Avg Accel: X={avg[0]:.2f}, Y={avg[1]:.2f}, Z={avg[2]:.2f} m/s²")
            print(f"Magnitude: {avg[3]:.2f} m/s² (should be ~9.8)")
            print(f"Which axis has gravity? ", end="")
            if abs(avg[0]) > 8: print("X")
            elif abs(avg[1]) > 8: print("Y")
            elif abs(avg[2]) > 8: print("Z")
            else: print("NONE - IMU problem!")
            self.samples = []
            
    def bridge_cb(self, msg):
        acc = msg.linear_acceleration
        mag = np.sqrt(acc.x**2 + acc.y**2 + acc.z**2)
        
        self.bridge_samples.append([acc.x, acc.y, acc.z, mag])
        
        if len(self.bridge_samples) == 50:
            avg = np.mean(self.bridge_samples, axis=0)
            print(f"\n=== IMU BRIDGE (with transform) ===")
            print(f"Avg Accel: X={avg[0]:.2f}, Y={avg[1]:.2f}, Z={avg[2]:.2f} m/s²")
            print(f"Magnitude: {avg[3]:.2f} m/s² (should be ~9.8)")
            print(f"Which axis has gravity? ", end="")
            if abs(avg[0]) > 8: print("X")
            elif abs(avg[1]) > 8: print("Y")
            elif abs(avg[2]) > 8: print("Z")
            else: print("NONE - transform broke it!")
            self.bridge_samples = []

def main():
    rclpy.init()
    node = IMUFrameTest()
    print("=== IMU Frame Test ===")
    print("Place drone STATIONARY on LEVEL surface")
    print("Collecting 50 samples from each topic...\n")
    rclpy.spin(node)

if __name__ == '__main__':
    main()
