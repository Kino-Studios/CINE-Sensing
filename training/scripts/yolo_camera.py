#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import os
import sys

sys.path.append('/home/fishnos/CINE-Sensing/venv/lib/python3.12/site-packages')

from ultralytics import YOLO

class YOLODetectionNode(Node):
    def __init__(self):
        super().__init__('yolo_detection_node')

        self.bridge = CvBridge()

        self.image_subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        try:
            model_path = "/home/fishnos/CINE-Sensing/training/checkpoints/pre-export/homeobjects_yolo11n_trained.pt"
            self.model = YOLO(model_path)
            self.get_logger().info(f'Loaded YOLO model from {model_path}')
        except Exception as e:
            self.get_logger().error(f'Failed to load model: {str(e)}')
            return

        self.frame_count = 0
        self.get_logger().info('YOLO Detection Node initialized - waiting for camera images')

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

            self.frame_count += 1
            if self.frame_count % 10 == 0:
                self.get_logger().info(f'Processing frame {self.frame_count}')

            results = self.model(cv_image)

            detections = results[0].boxes
            if detections is not None and len(detections) > 0:
                self.get_logger().info(f'Frame {self.frame_count}: Detected {len(detections)} objects')

                for i, detection in enumerate(detections):
                    class_id = int(detection.cls[0])
                    confidence = float(detection.conf[0])
                    class_name = self.model.names[class_id]
                    self.get_logger().info(f'  Object {i+1}: {class_name} ({confidence:.2f})')
            else:
                if self.frame_count % 30 == 0:
                    self.get_logger().info(f'Frame {self.frame_count}: No objects detected')

        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')

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

if __name__ == '__main__':
    main()
