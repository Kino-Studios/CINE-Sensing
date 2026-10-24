import os
from threading import Event

import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Point32, PolygonStamped
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import Header
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator

from cine_sensing_config import ModelDetectionConstants, UserRequestedParameters


class BoundingBoxPublisher(Node):
    def __init__(self):
        super().__init__('bb_extractor')

        self.bridge = CvBridge()
        self.shutdown_event = Event()

        model_path = os.path.expanduser(ModelDetectionConstants.MODEL_PATH)
        self.detection_model = YOLO(model_path)

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.image_subscriber = self.create_subscription(
            Image,
            ModelDetectionConstants.CAMERA_IMAGE_TOPIC,
            self._bounding_box_capture_callback,
            qos_profile,
        )

        self.bounding_box_publisher = self.create_publisher(
            PolygonStamped, ModelDetectionConstants.BOUNDING_BOX_TOPIC, qos_profile
        )

        self.dimensions_publisher = self.create_publisher(
            PolygonStamped, '/object_detection/dimensions', qos_profile
        )

        self.center_point_publisher = self.create_publisher(
            PolygonStamped, '/object_detection/center_point', qos_profile
        )

    def _bounding_box_capture_callback(self, image_message):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(
                image_message, desired_encoding=ModelDetectionConstants.IMAGE_ENCODING
            )

            inference_results = self.detection_model(
                cv_image,
                classes=[UserRequestedParameters.USER_OBJECT_ID],
                conf=ModelDetectionConstants.CONFIDENCE_THRESHOLD,
                iou=ModelDetectionConstants.IOU_THRESHOLD,
            )

            if (
                len(inference_results) == 0
                or inference_results[0].boxes is None
                or len(inference_results[0].boxes) == 0
            ):
                return

            bounding_boxes = inference_results[0].boxes
            xyxy_tensors = bounding_boxes.xyxy[0]

            if hasattr(xyxy_tensors, 'cpu'):
                xyxy_numpy = xyxy_tensors.cpu().numpy()
            else:
                xyxy_numpy = np.array(xyxy_tensors)

            x1, y1, x2, y2 = xyxy_numpy
            corners = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])

            width, height, area = Annotator.get_bbox_dimension([x1, y1, x2, y2])

            polygon_message = PolygonStamped()
            polygon_message.header = Header()
            polygon_message.header.stamp = image_message.header.stamp
            polygon_message.header.frame_id = image_message.header.frame_id

            dimensions_message = PolygonStamped()
            dimensions_message.header = Header()
            dimensions_message.header.stamp = image_message.header.stamp
            dimensions_message.header.frame_id = image_message.header.frame_id

            for index in range(ModelDetectionConstants.NUM_BOUNDING_BOX_POINTS):
                corner_point = Point32()
                corner_point.x = float(corners[index, 0])
                corner_point.y = float(corners[index, 1])
                corner_point.z = 0.0
                polygon_message.polygon.points.append(corner_point)

            dimension_point = Point32()
            dimension_point.x = float(width)
            dimension_point.y = float(height)
            dimension_point.z = float(area)
            dimensions_message.polygon.points.append(dimension_point)

            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0

            center_message = PolygonStamped()
            center_message.header = Header()
            center_message.header.stamp = image_message.header.stamp
            center_message.header.frame_id = image_message.header.frame_id

            center_point = Point32()
            center_point.x = float(center_x)
            center_point.y = float(center_y)
            center_point.z = 0.0
            center_message.polygon.points.append(center_point)

            self.bounding_box_publisher.publish(polygon_message)
            self.dimensions_publisher.publish(dimensions_message)
            self.center_point_publisher.publish(center_message)
        except Exception as error_message:
            self.get_logger().error(f'Error processing image: {str(error_message)}')

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
