#!/usr/bin/env python3

import os
import sys

import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from ultralytics import YOLO

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from configs.python import ModelDetectionConstants


class YOLODetectionNode(Node):
    def __init__(self):
        super().__init__("yolo_detection_node")

        self.bridge = CvBridge()

        self.image_subscription = self.create_subscription(
            Image, ModelDetectionConstants.CAMERA_IMAGE_TOPIC, self.image_callback, 10
        )

        try:
            model_path = ModelDetectionConstants.MODEL_PATH
            self.model = YOLO(model_path)
            self.get_logger().info(f"Loaded YOLO model from {model_path}")
        except Exception as e:
            self.get_logger().error(f"Failed to load model: {str(e)}")
            return

        self.frame_count = 0
        self.get_logger().info("YOLO Detection Node initialized")

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

            self.frame_count += 1
            if self.frame_count % 10 == 0:
                self.get_logger().info(f"Processing frame {self.frame_count}")

            results = self.model(cv_image)

            detections = results[0].boxes
            if detections is not None and len(detections) > 0:
                self.get_logger().info(
                    f"Frame {self.frame_count}: Detected {len(detections)} objects"
                )

                for i, detection in enumerate(detections):
                    class_id = int(detection.cls[0])
                    confidence = float(detection.conf[0])
                    class_name = self.model.names[class_id]
                    self.get_logger().info(f"  Object {i + 1}: {class_name} ({confidence:.2f})")
            else:
                if self.frame_count % 30 == 0:
                    self.get_logger().info(f"Frame {self.frame_count}: No objects detected")

        except Exception as e:
            self.get_logger().error(f"Error processing image: {str(e)}")


def main(args=None):
    rclpy.init(args=args)
    node = YOLODetectionNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
