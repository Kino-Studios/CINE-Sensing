import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import subprocess
import numpy as np
import tempfile
import os

class DepthPublisherNode(Node):
    def __init__(self):
        super().__init__('depth_publisher_node')
        
        self.bridge = CvBridge()
        self.depth_anything_path = '/home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/Depth-Anything'
        self.output_dir = os.path.expanduser('~/tmp/depth_outputs')
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.image_subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )
        
        self.depth_publisher = self.create_publisher(
            Image,
            '/depth/image_raw',
            10
        )

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmpfile:
                filepath = tmpfile.name
                cv2.imwrite(filepath, cv_image)
            
            try:
                result = subprocess.run([
                    'python3',
                    os.path.join(self.depth_anything_path, 'run.py'),
                    '--encoder', 'vits',
                    '--img-path', filepath,
                    '--pred-only',
                    '--outdir', self.output_dir,
                    '--grayscale'
                ], cwd=self.depth_anything_path, capture_output=True, timeout=30)
                
                depth_files = sorted([f for f in os.listdir(self.output_dir) if f.endswith('.png')])
                if depth_files:
                    depth_path = os.path.join(self.output_dir, depth_files[-1])
                    depth_image = cv2.imread(depth_path, cv2.IMREAD_GRAYSCALE)
                    
                    if depth_image is not None:
                        depth_msg = self.bridge.cv2_to_imgmsg(depth_image, encoding='mono8')
                        depth_msg.header = msg.header
                        depth_msg.header.frame_id = 'depth_camera'
                        self.depth_publisher.publish(depth_msg)
                        self.get_logger().info('Published depth image')
                    
                    os.remove(depth_path)
                    
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = DepthPublisherNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()