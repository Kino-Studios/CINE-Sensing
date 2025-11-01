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
import shutil

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
        
        self.get_logger().info("Improved Camera Publisher started!")
    
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
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.capture_thread = Thread(target=self._opencv_capture_loop, daemon=True)
            self.capture_thread.start()
    
    def _start_libcamera_capture(self):
        self.capture_thread = Thread(target=self._libcamera_capture_loop, daemon=True)
        self.capture_thread.start()
    
    def _opencv_capture_loop(self):
        frame_period = 1.0 / 30.0
        next_frame_time = time.time()
        
        while not self.shutdown_event.is_set() and rclpy.ok():
            ret, frame = self.camera.read()
            if ret and frame is not None:
                self._publish_frame(frame)
            
            next_frame_time += frame_period
            current_time = time.time()
            sleep_time = next_frame_time - current_time
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                next_frame_time = current_time + frame_period
    
    def _libcamera_capture_loop(self):
        frame_period = 1.0 / 30.0
        next_frame_time = time.time()
        subprocess_timeout = max(1.0, frame_period + 0.5)
        
        temp_dir = tempfile.mkdtemp()
        frame_pattern = os.path.join(temp_dir, 'frame%05d.jpg')
        
        try:
            while not self.shutdown_event.is_set() and rclpy.ok():
                try:
                    existing_frames = set(os.listdir(temp_dir)) if os.path.exists(temp_dir) else set()
                    
                    result = subprocess.run([
                        'rpicam-vid',
                        '-t', '1',
                        '--codec', 'mjpeg',
                        '--framerate', '30',
                        '--width', '1152',
                        '--height', '648',
                        '--segment', '1',
                        '--output', frame_pattern,
                        '--nopreview'
                    ], capture_output=True, timeout=subprocess_timeout)
                    
                    if result.returncode == 0:
                        current_frames = set(os.listdir(temp_dir)) if os.path.exists(temp_dir) else set()
                        new_frames = current_frames - existing_frames
                        
                        if new_frames:
                            latest_frame = os.path.join(temp_dir, sorted(new_frames)[0])
                            frame = cv2.imread(latest_frame)
                            if frame is not None:
                                self._publish_frame(frame)
                            
                            try:
                                os.unlink(latest_frame)
                            except:
                                pass
                    
                except subprocess.TimeoutExpired:
                    self.get_logger().error(f"libcamera subprocess timed out after {subprocess_timeout}s")
                except Exception as e:
                    self.get_logger().error(f"libcamera error: {e}")
                
                next_frame_time += frame_period
                current_time = time.time()
                sleep_time = next_frame_time - current_time
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    next_frame_time = current_time + frame_period
        
        finally:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
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