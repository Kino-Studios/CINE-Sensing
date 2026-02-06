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

import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from configs.python import CameraConfig

class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')

        self.declare_parameters(
            '',
            [
                ('camera_id', CameraConfig.CAMERA_ID),
                ('image_width', CameraConfig.IMAGE_WIDTH),
                ('image_height', CameraConfig.IMAGE_HEIGHT),
                ('fps', CameraConfig.FPS),
                ('camera_topic', CameraConfig.CAMERA_TOPIC),
                ('frame_id', CameraConfig.CAMERA_FRAME_ID),
                ('save_latest_frame', False),
                ('libcamera_shutter', CameraConfig.EXPOSURE_TIME_US), # Using exposure time as shutter
                ('libcamera_gain', CameraConfig.ANALOG_GAIN), # Using analog gain
            ],
        )

        self.camera_id = self.get_parameter('camera_id').get_parameter_value().integer_value
        self.image_width = self.get_parameter('image_width').get_parameter_value().integer_value
        self.image_height = self.get_parameter('image_height').get_parameter_value().integer_value
        self.fps = float(self.get_parameter('fps').get_parameter_value().double_value)
        self.camera_topic = self.get_parameter('camera_topic').get_parameter_value().string_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        self.save_latest_frame = self.get_parameter('save_latest_frame').get_parameter_value().bool_value
        self.libcamera_shutter = self.get_parameter('libcamera_shutter').get_parameter_value().integer_value
        self.libcamera_gain = float(self.get_parameter('libcamera_gain').get_parameter_value().double_value)

        self.bridge = CvBridge()
        self.shutdown_event = Event()

        self.camera_method = self._detect_camera_method()

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.image_publisher = self.create_publisher(
            Image,
            self.camera_topic,
            qos_profile
        )

        # start publishing
        if self.camera_method == 'opencv':
            self._start_opencv_capture()
        elif self.camera_method == 'libcamera':
            self._start_libcamera_capture()

    def _detect_camera_method(self):
        try:
            result = subprocess.run(['rpicam-hello', '--list-cameras'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'Available cameras' in result.stdout:
                return 'libcamera'
        except Exception:
            pass

        candidate_ids = [self.camera_id] + [cid for cid in [0, 1, 2] if cid != self.camera_id]
        for cam_id in candidate_ids:
            try:
                cap = cv2.VideoCapture(cam_id)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self.camera_id = cam_id
                        cap.release()
                        return 'opencv'
                cap.release()
            except Exception:
                pass

        return 'none'

    def _start_opencv_capture(self):
        self.camera = cv2.VideoCapture(self.camera_id)
        if self.camera.isOpened():
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.image_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.image_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.capture_thread = Thread(target=self._opencv_capture_loop, daemon=True)
            self.capture_thread.start()

    def _start_libcamera_capture(self):
        self.capture_thread = Thread(target=self._libcamera_capture_loop, daemon=True)
        self.capture_thread.start()

    def _opencv_capture_loop(self):
        frame_period = 1.0 / self.fps
        next_frame_time = time.time()

        while not self.shutdown_event.is_set() and rclpy.ok():
            ret, frame = self.camera.read()
            capture_time = self.get_clock().now()

            if ret and frame is not None:
                self._publish_frame(frame, capture_time)

            next_frame_time += frame_period
            current_time = time.time()
            sleep_time = next_frame_time - current_time

            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                next_frame_time = current_time + frame_period

    def _libcamera_capture_loop(self):
        try:
            process = subprocess.Popen([
                'rpicam-vid',
                '--codec', 'mjpeg',
                '--width', str(self.image_width),
                '--height', str(self.image_height),
                '--framerate', str(int(self.fps)),
                '--timeout', '0',
                '--nopreview',
                '--shutter', str(self.libcamera_shutter),
                '--gain', str(self.libcamera_gain),
                '--awb', 'auto',
                '--quality', '90',
                '--output', '-',
            ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)

            self.get_logger().info("libcamera capture at " + str(self.fps) + " Hz")

            buffer = b""
            while not self.shutdown_event.is_set() and rclpy.ok():
                chunk = process.stdout.read(4096)
                if not chunk:
                    break
                buffer += chunk

                while True:
                    soi = buffer.find(b'\xff\xd8')
                    eoi = buffer.find(b'\xff\xd9', soi + 2)
                    if soi != -1 and eoi != -1:
                        capture_time = self.get_clock().now()

                        jpg = buffer[soi:eoi + 2]
                        buffer = buffer[eoi + 2:]

                        np_arr = np.frombuffer(jpg, dtype=np.uint8)
                        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                        if frame is not None:
                            self._publish_frame(frame, capture_time)
                    else:
                        break

        finally:
            if 'process' in locals():
                process.terminate()
                try:
                    process.wait(timeout=2)
                except:
                    process.kill()

    def _publish_frame(self, frame, timestamp):
        try:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            msg = self.bridge.cv2_to_imgmsg(gray_frame, encoding='mono8')

            msg.header.stamp = timestamp.to_msg()
            msg.header.frame_id = self.frame_id

            self.image_publisher.publish(msg)

            if self.save_latest_frame:
                cv2.imwrite('latest_frame.png', frame)

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
    node = CameraPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()
