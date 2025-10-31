#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

class DepthVisualizerNode(Node):
    def __init__(self):
        super().__init__('depth_visualizer_node')
        
        self.bridge = CvBridge()
        
        self.depth_subscription = self.create_subscription(
            Image,
            '/depth/image_raw',
            self.depth_callback,
            10
        )
        
        self.depth_colored_subscription = self.create_subscription(
            Image,
            '/depth/image_colored',
            self.depth_colored_callback,
            10
        )
        
        self.get_logger().info('Depth Visualizer Node initialized')

    def depth_callback(self, msg):
        try:
            depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='mono8')
            
            depth_stats = {
                'min': np.min(depth_image),
                'max': np.max(depth_image),
                'mean': np.mean(depth_image),
                'std': np.std(depth_image)
            }
            
            self.get_logger().info(f'Depth stats - Min: {depth_stats["min"]:.2f}, Max: {depth_stats["max"]:.2f}, Mean: {depth_stats["mean"]:.2f}, Std: {depth_stats["std"]:.2f}')
            
        except Exception as e:
            self.get_logger().error(f'Error processing depth image: {str(e)}')

    def depth_colored_callback(self, msg):
        try:
            depth_colored = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            cv2.imshow('Depth Map (Colored)', depth_colored)
            cv2.waitKey(1)
            
        except Exception as e:
            self.get_logger().error(f'Error displaying colored depth: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = DepthVisualizerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()