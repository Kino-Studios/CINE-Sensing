import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from geometry_msgs.msg import PolygonStamped, Point32
from cv_bridge import CvBridge
import cv2
import numpy as np
import csv
import sys
import os
from datetime import datetime
import threading

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

workspace_root = os.path.join(project_root, 'autocine_ws', 'install')
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

try:
    from configs.user_params.constants import (
        ModelDetectionConstants, 
        UserRequestedParameters,
        RuleOfThirdsConstants
    )
except ImportError:
    class ModelDetectionConstants:
        CAMERA_IMAGE_TOPIC = '/camera/image_raw'
        BOUNDING_BOX_TOPIC = '/object_detection/bounding_box'
        IMAGE_ENCODING = 'bgr8'
        NUM_BOUNDING_BOX_POINTS = 4
        MODEL_PATH = os.path.expanduser('~/yolo_model.pt')
    
    class UserRequestedParameters:
        USER_OBJECT_ID = 11
    
    class RuleOfThirdsConstants:
        FRAME_WIDTH = 1152
        FRAME_HEIGHT = 648
        GRID_LINE_1_X = 384
        GRID_LINE_2_X = 768
        GRID_LINE_1_Y = 216
        GRID_LINE_2_Y = 432
        CORE_ANCHOR_POINTS = [
            (384, 216), (768, 216),
            (384, 432), (768, 432)
        ]


class DataExtractionNode(Node):
    def __init__(self):
        super().__init__('data_extraction_node')
        self.bridge = CvBridge()
        self.data_records = []
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.image_subscriber = self.create_subscription(
            Image,
            ModelDetectionConstants.CAMERA_IMAGE_TOPIC,
            self.image_callback,
            qos_profile
        )
        
        self.bbox_subscriber = self.create_subscription(
            PolygonStamped,
            ModelDetectionConstants.BOUNDING_BOX_TOPIC,
            self.bbox_callback,
            qos_profile
        )
        
        self.current_image = None
        self.current_bbox = None
        self.image_lock = threading.Lock()
        
    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(
                msg, 
                desired_encoding=ModelDetectionConstants.IMAGE_ENCODING
            )
            with self.image_lock:
                self.current_image = cv_image
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')
    
    def bbox_callback(self, msg):
        try:
            if len(msg.polygon.points) >= 4:
                corners = []
                for point in msg.polygon.points[:4]:
                    corners.append([point.x, point.y])
                self.current_bbox = np.array(corners)
        except Exception as e:
            self.get_logger().error(f'Error processing bounding box: {str(e)}')
    
    def get_current_data(self):
        with self.image_lock:
            return self.current_image.copy() if self.current_image is not None else None, \
                   self.current_bbox.copy() if self.current_bbox is not None else None
    
    def capture_data_point(self, mode='rule_of_thirds'):
        image, bbox = self.get_current_data()
        
        if image is None:
            return False, "No image available"
        
        if bbox is None:
            return False, "No bounding box detected"
        
        height, width = image.shape[:2]
        scale_x = RuleOfThirdsConstants.FRAME_WIDTH / width
        scale_y = RuleOfThirdsConstants.FRAME_HEIGHT / height
        
        scaled_bbox = bbox.copy()
        scaled_bbox[:, 0] *= scale_x
        scaled_bbox[:, 1] *= scale_y
        
        bbox_center = np.mean(scaled_bbox, axis=0)
        
        min_dist = float('inf')
        nearest_anchor = None
        cluster_id = -1
        
        for idx, anchor in enumerate(RuleOfThirdsConstants.CORE_ANCHOR_POINTS):
            dist = np.sqrt((bbox_center[0] - anchor[0])**2 + (bbox_center[1] - anchor[1])**2)
            if dist < min_dist:
                min_dist = dist
                nearest_anchor = anchor
                cluster_id = idx
        
        alignment_tolerance = 50
        if mode == 'rule_of_thirds' and min_dist > alignment_tolerance:
            return False, f"Not aligned: {min_dist:.1f}px from grid (tolerance: {alignment_tolerance}px)"
        
        for i, corner in enumerate(scaled_bbox):
            record = {
                'data_type': mode,
                'cluster_id': cluster_id,
                'x_px': corner[0],
                'y_px': corner[1],
                'bbox_x1': scaled_bbox[0, 0],
                'bbox_y1': scaled_bbox[0, 1],
                'bbox_x2': scaled_bbox[1, 0],
                'bbox_y2': scaled_bbox[1, 1],
                'bbox_x3': scaled_bbox[2, 0],
                'bbox_y3': scaled_bbox[2, 1],
                'bbox_x4': scaled_bbox[3, 0],
                'bbox_y4': scaled_bbox[3, 1],
                'center_x': bbox_center[0],
                'center_y': bbox_center[1],
                'distance_to_anchor': min_dist,
                'timestamp': datetime.now().isoformat(),
            }
            self.data_records.append(record)
        
        return True, f"Captured 4 points (cluster {cluster_id}, distance: {min_dist:.1f}px)"
    
    def save_to_csv(self, csv_path):
        if not self.data_records:
            return False, "No data to save"
        
        try:
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.data_records[0].keys())
                writer.writeheader()
                writer.writerows(self.data_records)
            return True, f"Saved {len(self.data_records)} records to {csv_path}"
        except Exception as e:
            return False, f"Error saving: {str(e)}"


def main():
    os.environ['ROS_DOMAIN_ID'] = '0'
    rclpy.init()
    node = DataExtractionNode()
    
    def spin_ros():
        rclpy.spin(node)
    
    ros_thread = threading.Thread(target=spin_ros, daemon=True)
    ros_thread.start()
    
    print("\n" + "="*70)
    print("DATA EXTRACTION TOOL - CLI MODE")
    print("="*70)
    print("Commands:")
    print("  c <mode>  - Capture data point (mode: 'rule' or 'control', default: rule)")
    print("  s <path>  - Save to CSV (default: bounding_box_data.csv)")
    print("  i         - Show info")
    print("  q         - Quit")
    print("="*70 + "\n")
    
    try:
        while True:
            cmd = input(">>> ").strip().split()
            
            if not cmd:
                continue
            
            if cmd[0].lower() == 'c':
                mode = cmd[1].lower() if len(cmd) > 1 else 'rule'
                mode = 'rule_of_thirds' if mode == 'rule' else mode
                success, msg = node.capture_data_point(mode)
                print(f"{'✅' if success else '❌'} {msg}")
                
            elif cmd[0].lower() == 's':
                csv_path = cmd[1] if len(cmd) > 1 else 'bounding_box_data.csv'
                success, msg = node.save_to_csv(csv_path)
                print(f"{'✅' if success else '❌'} {msg}")
                
            elif cmd[0].lower() == 'i':
                rot = len([r for r in node.data_records if r.get('data_type') == 'rule_of_thirds'])
                ctrl = len([r for r in node.data_records if r.get('data_type') == 'control'])
                print(f"Total points: {len(node.data_records)} (Rule of Thirds: {rot}, Control: {ctrl})")
                
            elif cmd[0].lower() == 'q':
                break
            else:
                print("Unknown command")
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
