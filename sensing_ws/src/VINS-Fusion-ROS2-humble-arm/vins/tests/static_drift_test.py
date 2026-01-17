#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import numpy as np
import time

class StaticDriftTest(Node):
    def __init__(self):
        super().__init__('static_drift_test')
        self.positions = []
        self.velocities = []
        self.start_time = None
        self.start_position = None
        
        self.odom_sub = self.create_subscription(Odometry, '/odometry', self.odom_cb, 10)
        
    def odom_cb(self, msg):
        if self.start_time is None:
            self.start_time = time.time()
            self.start_position = np.array([
                msg.pose.pose.position.x,
                msg.pose.pose.position.y,
                msg.pose.pose.position.z
            ])
            print("\n" + "="*60)
            print("STATIC DRIFT TEST")
            print("="*60)
            print("Keep sensor COMPLETELY STILL for 30 seconds")
            print("="*60 + "\n")
            return
        
        elapsed = time.time() - self.start_time
        
        pos = np.array([
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z
        ])
        
        vel = np.array([
            msg.twist.twist.linear.x,
            msg.twist.twist.linear.y,
            msg.twist.twist.linear.z
        ])
        
        self.positions.append(pos)
        self.velocities.append(vel)
        
        if int(elapsed) % 5 == 0 and len(self.positions) > 0:
            drift = np.linalg.norm(pos - self.start_position)
            vel_mag = np.linalg.norm(vel)
            print(f"[{elapsed:.1f}s] Drift: {drift:.4f}m, Velocity: {vel_mag:.4f}m/s")
        
        if elapsed > 30:
            self.analyze_results()
            rclpy.shutdown()
    
    def analyze_results(self):
        if len(self.positions) == 0:
            return
        
        positions = np.array(self.positions)
        velocities = np.array(self.velocities)
        
        final_drift = np.linalg.norm(positions[-1] - self.start_position)
        max_drift = np.max(np.linalg.norm(positions - self.start_position, axis=1))
        mean_velocity = np.mean(np.linalg.norm(velocities, axis=1))
        max_velocity = np.max(np.linalg.norm(velocities, axis=1))
        
        drift_rate = final_drift / 30.0
        
        print("\n" + "="*60)
        print("STATIC DRIFT TEST RESULTS (30 seconds)")
        print("="*60)
        print(f"Final drift:      {final_drift:.4f} m")
        print(f"Max drift:        {max_drift:.4f} m")
        print(f"Drift rate:       {drift_rate*100:.2f} cm/s")
        print(f"Mean velocity:    {mean_velocity:.4f} m/s")
        print(f"Max velocity:     {max_velocity:.4f} m/s")
        
        print("\nDIAGNOSIS:")
        
        if final_drift < 0.05:
            print("✅ EXCELLENT: Drift < 5cm in 30s")
            print("   VIO is working very well")
        elif final_drift < 0.2:
            print("✅ GOOD: Drift < 20cm in 30s")
            print("   Acceptable for most applications")
        elif final_drift < 0.5:
            print("⚠️  ACCEPTABLE: Drift < 50cm in 30s")
            print("   Usable but could be improved")
            print("   → Check IMU noise parameters")
            print("   → Verify extrinsics calibration")
        elif final_drift < 2.0:
            print("⚠️  POOR: Drift < 2m in 30s")
            print("   → Check camera calibration (scale error)")
            print("   → Verify extrinsics (rotation error)")
            print("   → Check feature tracking quality")
        else:
            print("❌ FAIL: Excessive drift")
            print("   → Likely camera NOT calibrated")
            print("   → OR wrong extrinsics")
            print("   → OR time sync issues")
        
        if mean_velocity > 0.1:
            print(f"\n⚠️  High mean velocity: {mean_velocity:.3f} m/s")
            print("   → IMU bias may be incorrect")
            print("   → Check gravity alignment")
        
        print("="*60 + "\n")

def main():
    rclpy.init()
    node = StaticDriftTest()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()
