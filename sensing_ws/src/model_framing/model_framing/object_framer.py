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
from ultralytics.utils.plotting import Annotator
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from configs.python import ModelDetectionConstants, UserRequestedParameters

class BoundingBoxPublisher(Node):
    def __init__(self):
        super().__init__('object_framer')

        self.bridge = CvBridge()
        self.shutdown_event = Event()

        model_path = os.path.expanduser(ModelDetectionConstants.MODEL_PATH)
        self.model = YOLO(model_path)

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
            qos_profile
        )

        self.bounding_box_publisher = self.create_publisher(
            PolygonStamped,
            ModelDetectionConstants.BOUNDING_BOX_TOPIC,
            qos_profile
        )

        self.dimensions_publisher = self.create_publisher(
            PolygonStamped,
            '/object_detection/dimensions',
            qos_profile
        )

        self.center_point_publisher = self.create_publisher(
            PolygonStamped,
            '/object_detection/center_point',
            qos_profile
        )

    def _bounding_box_capture_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding=ModelDetectionConstants.IMAGE_ENCODING)

            results = self.model(cv_image, classes=[UserRequestedParameters.USER_OBJECT_ID])

            if len(results) == 0 or results[0].boxes is None or len(results[0].boxes) == 0:
                return

            boxes = results[0].boxes
            xyxy = boxes.xyxy[0]

            if hasattr(xyxy, 'cpu'):
                xyxy = xyxy.cpu().numpy()
            else:
                xyxy = np.array(xyxy)

            x1, y1, x2, y2 = xyxy
            corners = np.array([
                [x1, y1],
                [x2, y1],
                [x2, y2],
                [x1, y2]
            ])

            width, height, area = Annotator.get_bbox_dimension([x1, y1, x2, y2])

            polygon_msg = PolygonStamped()
            polygon_msg.header = Header()
            polygon_msg.header.stamp = msg.header.stamp
            polygon_msg.header.frame_id = msg.header.frame_id

            dimensions_msg = PolygonStamped()
            dimensions_msg.header = Header()
            dimensions_msg.header.stamp = msg.header.stamp
            dimensions_msg.header.frame_id = msg.header.frame_id

            for i in range(ModelDetectionConstants.NUM_BOUNDING_BOX_POINTS):
                point = Point32()
                point.x = float(corners[i, 0])
                point.y = float(corners[i, 1])
                point.z = 0.0
                polygon_msg.polygon.points.append(point)

            dim_point = Point32()
            dim_point.x = float(width)
            dim_point.y = float(height)
            dim_point.z = float(area)
            dimensions_msg.polygon.points.append(dim_point)

            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0

            center_msg = PolygonStamped()
            center_msg.header = Header()
            center_msg.header.stamp = msg.header.stamp
            center_msg.header.frame_id = msg.header.frame_id

            center_point = Point32()
            center_point.x = float(center_x)
            center_point.y = float(center_y)
            center_point.z = 0.0
            center_msg.polygon.points.append(center_point)

            self.bounding_box_publisher.publish(polygon_msg)
            self.dimensions_publisher.publish(dimensions_msg)
            self.center_point_publisher.publish(center_msg)
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
