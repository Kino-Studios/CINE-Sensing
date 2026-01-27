#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import os

import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from configs.python import CameraConfig

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
HEADLESS = True

class FeatureTrackingTest(Node):
    def __init__(self):
        super().__init__('feature_tracking_test')
        self.bridge = CvBridge()
        self.prev_gray = None
        self.prev_pts = None

        self.feature_params = dict(
            maxCorners=300,  # Match VINS config
            qualityLevel=0.01,
            minDistance=20,
            blockSize=7
        )

        self.lk_params = dict(
            winSize=(21, 21),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
        )

        self.img_sub = self.create_subscription(
            Image, CameraConfig.CAMERA_TOPIC, self.img_cb, 10)

        self.tracked_counts = []
        self.frame_count = 0

        print("\n" + "="*60)
        print("FEATURE TRACKING QUALITY TEST (Headless Mode)")
        print("="*60)
        print("Testing feature detection and tracking...")
        print("Press Ctrl+C to stop and see results")
        print("="*60 + "\n")

    def img_cb(self, msg):
        try:
            self.frame_count += 1
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

            if self.prev_gray is None:
                self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
                self.prev_gray = gray
                if self.prev_pts is not None:
                    print(f"Initial features detected: {len(self.prev_pts)}")
                return

            if self.prev_pts is None or len(self.prev_pts) < 50:
                self.prev_pts = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
                self.prev_gray = gray
                return

            next_pts, status, error = cv2.calcOpticalFlowPyrLK(
                self.prev_gray, gray, self.prev_pts, None, **self.lk_params)

            if next_pts is None:
                self.prev_gray = gray
                return

            good_new = next_pts[status == 1]
            good_old = self.prev_pts[status == 1]

            num_tracked = len(good_new)
            self.tracked_counts.append(num_tracked)

            # Print stats every 25 frames (~1 second at 25Hz)
            if len(self.tracked_counts) % 25 == 0:
                recent_mean = np.mean(self.tracked_counts[-25:])
                recent_min = np.min(self.tracked_counts[-25:])
                recent_max = np.max(self.tracked_counts[-25:])
                print(f"Frame {self.frame_count}: Tracked={num_tracked} | "
                      f"Recent avg={recent_mean:.1f} (min={recent_min}, max={recent_max})")

            self.prev_gray = gray
            self.prev_pts = good_new.reshape(-1, 1, 2)

        except Exception as e:
            self.get_logger().error(f'Error: {e}')

    def analyze_results(self):
        if len(self.tracked_counts) == 0:
            return

        counts = np.array(self.tracked_counts)

        mean_tracked = np.mean(counts)
        min_tracked = np.min(counts)
        pct_good = np.sum(counts >= 50) / len(counts) * 100

        print("\n" + "="*60)
        print("FEATURE TRACKING TEST RESULTS")
        print("="*60)
        print(f"Mean features tracked: {mean_tracked:.1f}")
        print(f"Min features tracked:  {min_tracked}")
        print(f"% frames with 50+ features: {pct_good:.1f}%")

        print("\nDIAGNOSIS:")

        if mean_tracked >= 100:
            print("✅ EXCELLENT: Very good feature tracking")
            print("   Plenty of features for robust VIO")
        elif mean_tracked >= 50:
            print("✅ GOOD: Adequate feature tracking")
            print("   Sufficient for VIO")
        elif mean_tracked >= 30:
            print("⚠️  MODERATE: Marginal feature tracking")
            print("   → Improve lighting")
            print("   → Add texture to environment")
            print("   → Reduce motion blur (lower exposure)")
        else:
            print("❌ FAIL: Insufficient features")
            print("   → Environment lacks texture")
            print("   → OR camera out of focus")
            print("   → OR moving too fast")
            print("   → OR poor lighting")

        if min_tracked < 20:
            print("\n⚠️  WARNING: Features dropped below 20")
            print("   → May lose tracking during fast motion")
            print("   → Increase max_cnt in VIO config")

        print("="*60 + "\n")

def main():
    rclpy.init()
    node = FeatureTrackingTest()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.analyze_results()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
