#!/usr/bin/env python3
"""
Simple Position Monitor - Tracks drone position over time
Shows position drift without velocity metrics
"""
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import numpy as np
import time

class PositionMonitor(Node):
    def __init__(self):
        super().__init__('position_monitor')
        
        self.odom_sub = self.create_subscription(
            Odometry, '/odometry', self.odom_callback, 10)
        
        self.start_pos = None
        self.start_time = None
        self.positions = []
        self.timestamps = []
        
        print("\n" + "="*60)
        print("POSITION MONITOR")
        print("="*60)
        print("Tracking drone position...")
        print("Press Ctrl+C to stop and see results")
        print("="*60 + "\n")
    
    def odom_callback(self, msg):
        if self.start_time is None:
            self.start_time = time.time()
            self.start_pos = np.array([
                msg.pose.pose.position.x,
                msg.pose.pose.position.y,
                msg.pose.pose.position.z
            ])
            print(f"Starting position: X={self.start_pos[0]:.2f}, Y={self.start_pos[1]:.2f}, Z={self.start_pos[2]:.2f}")
            return
        
        elapsed = time.time() - self.start_time
        
        current_pos = np.array([
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z
        ])
        
        # Calculate drift from start
        drift = np.linalg.norm(current_pos - self.start_pos)
        
        self.positions.append(current_pos)
        self.timestamps.append(elapsed)
        
        # Print every 5 seconds
        if len(self.positions) % 125 == 0:  # ~125 samples = 5 seconds at 25Hz
            print(f"[{elapsed:.1f}s] Position: X={current_pos[0]:.2f}, Y={current_pos[1]:.2f}, Z={current_pos[2]:.2f} | Drift from start: {drift:.3f}m")
    
    def analyze(self):
        if len(self.positions) == 0:
            print("No data collected")
            return
        
        positions = np.array(self.positions)
        total_time = self.timestamps[-1]
        
        # Calculate drift over time
        drifts = [np.linalg.norm(pos - self.start_pos) for pos in positions]
        final_drift = drifts[-1]
        max_drift = max(drifts)
        mean_drift = np.mean(drifts)
        
        print("\n" + "="*60)
        print("POSITION ANALYSIS")
        print("="*60)
        print(f"Duration: {total_time:.1f} seconds")
        print(f"Samples collected: {len(positions)}")
        print(f"\nStarting position:")
        print(f"  X: {self.start_pos[0]:.3f} m")
        print(f"  Y: {self.start_pos[1]:.3f} m")
        print(f"  Z: {self.start_pos[2]:.3f} m")
        print(f"\nFinal position:")
        print(f"  X: {positions[-1][0]:.3f} m")
        print(f"  Y: {positions[-1][1]:.3f} m")
        print(f"  Z: {positions[-1][2]:.3f} m")
        print(f"\nPosition change:")
        print(f"  ΔX: {positions[-1][0] - self.start_pos[0]:.3f} m")
        print(f"  ΔY: {positions[-1][1] - self.start_pos[1]:.3f} m")
        print(f"  ΔZ: {positions[-1][2] - self.start_pos[2]:.3f} m")
        print(f"\nDrift metrics:")
        print(f"  Final drift: {final_drift:.3f} m")
        print(f"  Max drift: {max_drift:.3f} m")
        print(f"  Mean drift: {mean_drift:.3f} m")
        print(f"  Drift rate: {(final_drift/total_time)*100:.2f} cm/s")
        
        print("\nDIAGNOSIS:")
        if final_drift < 0.2:
            print("✅ EXCELLENT: Drift < 20cm")
            print("   Very stable position tracking")
        elif final_drift < 0.5:
            print("✅ GOOD: Drift < 50cm")
            print("   Acceptable for most applications")
        elif final_drift < 2.0:
            print("⚠️  MODERATE: Drift < 2m")
            print("   Usable but needs improvement")
        else:
            print("❌ POOR: Drift > 2m")
            print("   Position tracking unreliable")
            print("   → Check IMU calibration")
            print("   → Verify feature tracking")
            print("   → Review config parameters")
        
        print("="*60 + "\n")

def main():
    rclpy.init()
    node = PositionMonitor()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.analyze()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
