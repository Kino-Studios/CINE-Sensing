"""
ROS2 Camera Subscriber Node for receiving and displaying images

This node subscribes to camera images published by the Raspberry Pi
and displays them or saves them to disk.

Author: Your Name
License: MIT
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np
import os
from datetime import datetime
import threading


class CameraSubscriber(Node):
    """ROS2 node for subscribing to camera images."""
    
    def __init__(self):
        super().__init__('camera_subscriber')
        
        self.bridge = CvBridge()
        
        self.latest_image = None
        self.image_lock = threading.Lock()
        
        self._declare_parameters()
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.image_subscriber = self.create_subscription(
            Image,
            self.get_parameter('camera_topic').value,
            self.image_callback,
            qos_profile
        )
        
        self.camera_info_subscriber = self.create_subscription(
            CameraInfo,
            self.get_parameter('camera_info_topic').value,
            self.camera_info_callback,
            qos_profile
        )
        
        self.save_images = self.get_parameter('save_images').value
        if self.save_images:
            self.save_directory = self.get_parameter('save_directory').value
            os.makedirs(self.save_directory, exist_ok=True)
            self.image_counter = 0
        
        self.display_images = self.get_parameter('display_images').value
        
        self.images_received = 0
        self.last_fps_time = self.get_clock().now()
        
        self.fps_timer = self.create_timer(5.0, self.report_fps)
        
        self.get_logger().info("Camera Subscriber Node initialized successfully")
        self.get_logger().info(f"Subscribing to: {self.get_parameter('camera_topic').value}")
        self.get_logger().info(f"Display images: {self.display_images}")
        self.get_logger().info(f"Save images: {self.save_images}")
    
    def _declare_parameters(self):
        """Declare ROS2 parameters with default values."""
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('camera_info_topic', '/camera/camera_info')
        self.declare_parameter('display_images', True)
        self.declare_parameter('save_images', False)
        self.declare_parameter('save_directory', './saved_images')
        self.declare_parameter('save_format', 'jpg')
        self.declare_parameter('display_window_name', 'Camera Feed')
        self.declare_parameter('max_display_size', 800)
    
    def image_callback(self, msg):
        """Callback for receiving image messages."""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            with self.image_lock:
                self.latest_image = cv_image.copy()
            
            self.images_received += 1
            
            if self.display_images:
                self._display_image(cv_image)
            
            if self.save_images:
                self._save_image(cv_image, msg.header.stamp)
                
        except Exception as e:
            self.get_logger().error(f"Error processing image: {str(e)}")
    
    def camera_info_callback(self, msg):
        """Callback for receiving camera info messages."""
        pass
    
    def _display_image(self, image):
        """Display the image using OpenCV."""
        try:
            max_size = self.get_parameter('max_display_size').value
            height, width = image.shape[:2]
            
            if width > max_size or height > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * max_size / width)
                else:
                    new_height = max_size
                    new_width = int(width * max_size / height)
                
                display_image = cv2.resize(image, (new_width, new_height))
            else:
                display_image = image
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            info_text = f"Images: {self.images_received} | Time: {timestamp}"
            
            cv2.putText(display_image, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            window_name = self.get_parameter('display_window_name').value
            cv2.imshow(window_name, display_image)
            cv2.waitKey(1)
            
        except Exception as e:
            self.get_logger().error(f"Error displaying image: {str(e)}")
    
    def _save_image(self, image, timestamp):
        """Save the image to disk."""
        try:
            save_dir = self.get_parameter('save_directory').value
            save_format = self.get_parameter('save_format').value
            
            timestamp_ns = timestamp.sec * 1000000000 + timestamp.nanosec
            filename = f"image_{timestamp_ns:019d}_{self.image_counter:06d}.{save_format}"
            filepath = os.path.join(save_dir, filename)
            
            cv2.imwrite(filepath, image)
            self.image_counter += 1
            
            if self.image_counter % 100 == 0:
                self.get_logger().info(f"Saved {self.image_counter} images to {save_dir}")
                
        except Exception as e:
            self.get_logger().error(f"Error saving image: {str(e)}")
    
    def report_fps(self):
        """Report FPS statistics."""
        current_time = self.get_clock().now()
        time_diff = (current_time - self.last_fps_time).nanoseconds / 1e9
        
        if time_diff > 0:
            fps = self.images_received / time_diff
            self.get_logger().info(f"Receiving images at {fps:.2f} FPS (Total: {self.images_received})")
        
        self.images_received = 0
        self.last_fps_time = current_time
    
    def get_latest_image(self):
        """Get the latest received image (thread-safe)."""
        with self.image_lock:
            return self.latest_image.copy() if self.latest_image is not None else None
    
    def destroy_node(self):
        """Clean shutdown of the node."""
        self.get_logger().info("Shutting down camera subscriber...")
        
        cv2.destroyAllWindows()
        
        super().destroy_node()

def main(args=None):
    """Main entry point for the camera subscriber node."""
    rclpy.init(args=args)
    
    try:
        camera_subscriber = CameraSubscriber()
        rclpy.spin(camera_subscriber)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'camera_subscriber' in locals():
            camera_subscriber.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()