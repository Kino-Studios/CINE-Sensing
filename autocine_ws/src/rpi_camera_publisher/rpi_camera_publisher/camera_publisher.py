#!/usr/bin/env python3
"""
ROS2 Camera Publisher Node for Raspberry Pi Camera Module 3

This node captures images from the Raspberry Pi camera and publishes them
as ROS2 sensor_msgs/Image topics for consumption by other nodes.

Author: Your Name
License: MIT
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import TransformStamped
from cv_bridge import CvBridge
import cv2
import numpy as np
from threading import Thread, Event
import time
import yaml
import os


class CameraPublisher(Node):
    """ROS2 node for publishing camera images from Raspberry Pi Camera Module 3."""
    
    def __init__(self):
        super().__init__('camera_publisher')
        
        self.bridge = CvBridge()
        
        self.capture_thread = None
        self.shutdown_event = Event()
        
        self._declare_parameters()
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.image_publisher = self.create_publisher(
            Image, 
            self.get_parameter('camera_topic').value, 
            qos_profile
        )
        
        self.camera_info_publisher = self.create_publisher(
            CameraInfo,
            self.get_parameter('camera_info_topic').value,
            qos_profile
        )
        
        self.camera = None
        self._setup_camera()
        
        self.camera_info_msg = self._create_camera_info()
        
        self._start_capture_thread()
        
        self.get_logger().info("Camera Publisher Node initialized successfully")
    
    def _declare_parameters(self):
        """Declare ROS2 parameters with default values."""
        self.declare_parameter('camera_id', 0)
        self.declare_parameter('image_width', 1920)
        self.declare_parameter('image_height', 1080)
        self.declare_parameter('fps', 30.0)
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('camera_info_topic', '/camera/camera_info')
        self.declare_parameter('camera_frame_id', 'camera_optical_frame')
        self.declare_parameter('publish_rate', 30.0)
        self.declare_parameter('buffer_size', 1)
        
        self.declare_parameter('camera_matrix', 
                             [1000.0, 0.0, 960.0, 0.0, 1000.0, 540.0, 0.0, 0.0, 1.0])
        self.declare_parameter('distortion_coefficients', 
                             [0.1, -0.2, 0.0, 0.0, 0.0])
    
    def _setup_camera(self):
        """Initialize the camera with specified parameters."""
        try:
            camera_id = self.get_parameter('camera_id').value
            width = self.get_parameter('image_width').value
            height = self.get_parameter('image_height').value
            fps = self.get_parameter('fps').value
            
            self.camera = cv2.VideoCapture(camera_id, cv2.CAP_V4L2)
            
            if not self.camera.isOpened():
                self.get_logger().error(f"Failed to open camera {camera_id}")
                return False
            
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.camera.set(cv2.CAP_PROP_FPS, fps)
            
            buffer_size = self.get_parameter('buffer_size').value
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)
            
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            self.get_logger().info(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps} FPS")
            
            return True
            
        except Exception as e:
            self.get_logger().error(f"Error setting up camera: {str(e)}")
            return False
    
    def _create_camera_info(self):
        """Create CameraInfo message from parameters."""
        camera_info = CameraInfo()
        camera_info.header.frame_id = self.get_parameter('camera_frame_id').value
        
        camera_info.width = self.get_parameter('image_width').value
        camera_info.height = self.get_parameter('image_height').value
        
        camera_matrix = self.get_parameter('camera_matrix').value
        camera_info.k = camera_matrix
        
        distortion = self.get_parameter('distortion_coefficients').value
        camera_info.d = distortion
        camera_info.distortion_model = "plumb_bob"
        
        camera_info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        
        camera_info.p = [
            camera_matrix[0], 0.0, camera_matrix[2], 0.0,  # fx, 0, cx, 0
            0.0, camera_matrix[4], camera_matrix[5], 0.0,  # 0, fy, cy, 0
            0.0, 0.0, 1.0, 0.0                             # 0, 0, 1, 0
        ]
        
        return camera_info
    
    def _start_capture_thread(self):
        """Start the camera capture thread."""
        if self.camera is not None and self.camera.isOpened():
            self.capture_thread = Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            self.get_logger().info("Camera capture thread started")
    
    def _capture_loop(self):
        """Main capture loop running in separate thread."""
        publish_rate = self.get_parameter('publish_rate').value
        frame_time = 1.0 / publish_rate
        
        while not self.shutdown_event.is_set() and rclpy.ok():
            start_time = time.time()
            
            try:
                ret, frame = self.camera.read()
                
                if ret and frame is not None:
                    timestamp = self.get_clock().now()

                    image_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
                    image_msg.header.stamp = timestamp.to_msg()
                    image_msg.header.frame_id = self.get_parameter('camera_frame_id').value
                    
                    self.camera_info_msg.header.stamp = timestamp.to_msg()
                    
                    self.image_publisher.publish(image_msg)
                    self.camera_info_publisher.publish(self.camera_info_msg)
                    
                else:
                    self.get_logger().warn("Failed to capture frame")
                    
            except Exception as e:
                self.get_logger().error(f"Error in capture loop: {str(e)}")
            
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def destroy_node(self):
        """Clean shutdown of the node."""
        self.get_logger().info("Shutting down camera publisher...")
        
        self.shutdown_event.set()
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        
        if self.camera:
            self.camera.release()
        
        super().destroy_node()

def main(args=None):
    """Main entry point for the camera publisher node."""
    rclpy.init(args=args)
    
    try:
        camera_publisher = CameraPublisher()
        rclpy.spin(camera_publisher)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'camera_publisher' in locals():
            camera_publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()