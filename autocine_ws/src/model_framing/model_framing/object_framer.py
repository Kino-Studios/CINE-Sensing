import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
from geometry_msgs.msg import PolygonStamped, Point32
from std_msgs.msg import Header
import cv2
import numpy as np
from ultralytics import YOLO
from threading import Event
from pathlib import Path
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from configs.user_params.constants import ModelDetectionConstants, UserRequestedParameters

class BoundingBoxPublisher(Node):
    def __init__(self):
        super().__init__('object_framer.py')
        
        self.bridge = CvBridge()
        self.shutdown_event = Event()
        self.model = YOLO(ModelDetectionConstants.MODEL_PATH)
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.image_subscriber = self.create_subscription(
            Image,
            ModelDetectionConstants.CAMERA_IMAGE_TOPIC,
            self._bounding_box_capture_callback,
            qos_profile,
            10
        )

        self.bounding_box_publisher = self.create_publisher(
            PolygonStamped,
            ModelDetectionConstants.BOUNDING_BOX_TOPIC,
            qos_profile,
            10
        )
    
    def _bounding_box_capture_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding=ModelDetectionConstants.IMAGE_ENCODING)
            
            results = self.model(cv_image, classes=[UserRequestedParameters.USER_OBJECT_ID])
            
            if len(results) == 0 or results[0].obb is None or len(results[0].obb) == 0:
                return
            
            obb = results[0].obb
            obb_coords = obb.xyxyxyxy[0]
            
            if hasattr(obb_coords, 'cpu'):
                obb_coords = obb_coords.cpu().numpy()
            else:
                obb_coords = np.array(obb_coords)
            
            if obb_coords.ndim == 1:
                obb_coords = obb_coords.reshape(4, 2)
            elif obb_coords.ndim == 3:
                obb_coords = obb_coords[0]
            
            polygon_msg = PolygonStamped()
            polygon_msg.header = Header()
            polygon_msg.header.stamp = msg.header.stamp
            polygon_msg.header.frame_id = msg.header.frame_id
            
            for i in range(ModelDetectionConstants.NUM_BOUNDING_BOX_POINTS):
                point = Point32()
                point.x = float(obb_coords[i, 0])
                point.y = float(obb_coords[i, 1])
                point.z = 0.0
                polygon_msg.polygon.points.append(point)
            
            self.bounding_box_publisher.publish(polygon_msg)
            
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')
    
    def destroy_node(self):
        self.shutdown_event.set()
        
        super().destroy_node()

def main():
    rclpy.init()
    node = BoundingBoxPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()