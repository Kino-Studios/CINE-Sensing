import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Imu, Image
from collections import deque
import numpy as np

class TimeSyncTest(Node):
    def __init__(self):
        super().__init__('time_sync_test')
        self.imu_stamps = deque(maxlen=100)
        self.img_stamps = deque(maxlen=100)
        
        imu_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        img_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        
        self.imu_sub = self.create_subscription(Imu, '/mavros/imu/data_raw', self.imu_cb, imu_qos)
        self.img_sub = self.create_subscription(Image, '/camera/image_raw', self.img_cb, img_qos)
        self.timer = self.create_timer(2.0, self.analyze)
        
    def imu_cb(self, msg):
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.imu_stamps.append(t)
        
    def img_cb(self, msg):
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.img_stamps.append(t)
        
    def analyze(self):
        if len(self.imu_stamps) < 5 or len(self.img_stamps) < 5:
            print(f"Collecting... IMU: {len(self.imu_stamps)}, Camera: {len(self.img_stamps)}", end='\r')
            return
            
        imu_arr = np.array(self.imu_stamps)
        img_arr = np.array(self.img_stamps)
        
        time_diff = abs(imu_arr[-1] - img_arr[-1])
        
        print("\n" + "="*60)
        print("TIME SYNC TEST RESULTS")
        print("="*60)
        print(f"Latest IMU timestamp:    {imu_arr[-1]:.6f}")
        print(f"Latest Camera timestamp: {img_arr[-1]:.6f}")
        print(f"Time difference:         {time_diff:.6f} seconds")
        
        if time_diff > 100:
            print("\n❌ FAIL: Different time bases (differ by hours/days)")
            print("   FIX: Set use_system_time: true in MAVROS config")
            print("   OR: Enable MAVROS timesync")
        elif time_diff > 0.5:
            print("\n⚠️  WARN: Large constant offset")
            print(f"   FIX: Set estimate_td: 1 and td: {time_diff:.3f} in VIO config")
        else:
            print("\n✅ PASS: Time synchronization looks good")
        
        imu_jitter = np.std(np.diff(imu_arr)) * 1000
        img_jitter = np.std(np.diff(img_arr)) * 1000
        
        print(f"\nIMU timestamp jitter:    {imu_jitter:.2f} ms")
        print(f"Camera timestamp jitter: {img_jitter:.2f} ms")
        
        if imu_jitter > 10 or img_jitter > 20:
            print("⚠️  WARN: High jitter detected")
        print("="*60 + "\n")

def main():
    rclpy.init()
    node = TimeSyncTest()
    print("Running time sync test for 10 seconds...")
    try:
        for _ in range(50):
            rclpy.spin_once(node, timeout_sec=0.2)
    except:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()