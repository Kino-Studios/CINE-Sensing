#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np
from threading import Thread, Event
import time
import subprocess
import tempfile
import os

class ImprovedCameraPublisher(Node):
    def __init__(self):
        super().__init__('improved_camera_publisher')
        
        self.bridge = CvBridge()
        self.shutdown_event = Event()
        
        self.camera_method = self._detect_camera_method()
            
        self.get_logger().info(f"Using camera method: {self.camera_method}")
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.image_publisher = self.create_publisher(Image, '/camera/image_raw', qos_profile)
        
        # start publishing
        if self.camera_method == 'opencv':
            self._start_opencv_capture()
        elif self.camera_method == 'libcamera':
            self._start_libcamera_capture()
    
    def _detect_camera_method(self):
        for cam_id in [0, 1, 2]:
            try:
                cap = cv2.VideoCapture(cam_id)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self.camera_id = cam_id
                        cap.release()
                        return 'opencv'
                cap.release()
            except:
                pass
        
        try:
            result = subprocess.run(['rpicam-hello', '--list-cameras'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'Available cameras' in result.stdout:
                return 'libcamera'
        except:
            pass
        
        return 'none'
    
    def _start_opencv_capture(self):
        self.camera = cv2.VideoCapture(self.camera_id)
        if self.camera.isOpened():
            self.capture_thread = Thread(target=self._opencv_capture_loop, daemon=True)
            self.capture_thread.start()
    
    def _start_libcamera_capture(self):
        self.capture_thread = Thread(target=self._libcamera_capture_loop, daemon=True)
        self.capture_thread.start()
    
    def _opencv_capture_loop(self):
        while not self.shutdown_event.is_set() and rclpy.ok():
            ret, frame = self.camera.read()
            if ret:
                self._publish_frame(frame)
            time.sleep(1/30.0)  # 30 FPS
    
    def _libcamera_capture_loop(self):
        while not self.shutdown_event.is_set() and rclpy.ok():
            try:
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                    tmp_filename = tmp_file.name
                
                result = subprocess.run([
                    'rpicam-still', 
                    '-o', tmp_filename, 
                    '-t', '100',
                    '--immediate',
                    '--width', '1152',
                    '--height', '648'
                ], capture_output=True, timeout=2)
                
                if result.returncode == 0 and os.path.exists(tmp_filename):
                    frame = cv2.imread(tmp_filename)
                    if frame is not None:
                        self._publish_frame(frame)
                
                if os.path.exists(tmp_filename):
                    os.unlink(tmp_filename)
                    
            except Exception as e:
                self.get_logger().error(f"libcamera error: {e}")
            
            time.sleep(1/10.0)
    
    def _publish_frame(self, frame):
        try:
            msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'camera'
            
            self.image_publisher.publish(msg)
            self.get_logger().info(f'Published image: {frame.shape[1]}x{frame.shape[0]}')
            
        except Exception as e:
            self.get_logger().error(f"Failed to publish frame: {e}")
    
    def destroy_node(self):
        self.shutdown_event.set()
        
        if hasattr(self, 'capture_thread') and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        
        if hasattr(self, 'camera') and self.camera:
            self.camera.release()
        
        super().destroy_node()

def main():
    rclpy.init()
    node = ImprovedCameraPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()