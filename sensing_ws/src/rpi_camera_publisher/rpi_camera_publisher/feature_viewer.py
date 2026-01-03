import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import threading


class FeatureViewer(Node):
    def __init__(self):
        super().__init__('feature_viewer')
        
        self.bridge = CvBridge()
        self.latest_image = None
        self.image_lock = threading.Lock()
        
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.image_subscription = self.create_subscription(
            Image,
            'image_track',
            self._image_callback,
            qos_profile
        )
        
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()
        
    def _image_callback(self, msg: Image):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            with self.image_lock:
                self.latest_image = cv_image
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
    
    def _display_loop(self):
        window_name = "VINS Feature Tracking"
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
        
        while rclpy.ok():
            with self.image_lock:
                if self.latest_image is not None:
                    cv2.imshow(window_name, self.latest_image)
            
            key = cv2.waitKey(5) & 0xFF
            if key == ord('q'):
                break
        
        cv2.destroyAllWindows()


def main():
    rclpy.init()
    node = FeatureViewer()
    
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
