#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torchvision.transforms import Compose, Normalize
import sys
import os

sys.path.append('/home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/Depth-Anything')

from depth_anything.dpt import DepthAnything
from depth_anything.util.transform import Resize, NormalizeImage, PrepareForNet

class DepthPublisherNode(Node):
    def __init__(self):
        super().__init__('depth_publisher_node')
        
        self.bridge = CvBridge()
        
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
        
        self.depth_colored_publisher = self.create_publisher(
            Image,
            '/depth/image_colored',
            10
        )
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.get_logger().info(f'Using device: {self.device}')
        
        model_configs = {
            'vits': {'encoder': 'vits', 'features': 64, 'out_channels': [48, 96, 192, 384]},
            'vitb': {'encoder': 'vitb', 'features': 128, 'out_channels': [96, 192, 384, 768]},
            'vitl': {'encoder': 'vitl', 'features': 256, 'out_channels': [256, 512, 1024, 1024]}
        }
        
        encoder = 'vits'
        self.model = DepthAnything(model_configs[encoder])
        self.model.load_state_dict(torch.load(f'/home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/Depth-Anything/checkpoints/depth_anything_{encoder}14.pth', map_location='cpu'))
        self.model = self.model.to(self.device).eval()
        
        self.transform = Compose([
            Resize(
                width=518,
                height=518,
                resize_target=False,
                keep_aspect_ratio=True,
                ensure_multiple_of=14,
                resize_method='lower_bound',
                image_interpolation_method=cv2.INTER_CUBIC,
            ),
            NormalizeImage(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            PrepareForNet(),
        ])
        
        self.get_logger().info('Depth Publisher Node initialized successfully')

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            depth_map = self.estimate_depth(cv_image)
            
            depth_msg = self.create_depth_message(depth_map, msg.header)
            self.depth_publisher.publish(depth_msg)
            
            depth_colored = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_map, alpha=255.0/depth_map.max()), 
                cv2.COLORMAP_JET
            )
            depth_colored_msg = self.bridge.cv2_to_imgmsg(depth_colored, encoding='bgr8')
            depth_colored_msg.header = msg.header
            self.depth_colored_publisher.publish(depth_colored_msg)
            
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')

    def estimate_depth(self, image):
        h, w = image.shape[:2]
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) / 255.0
        image = self.transform({'image': image})['image']
        image = torch.from_numpy(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            depth = self.model(image)
            depth = F.interpolate(depth[None], (h, w), mode='bilinear', align_corners=False)[0, 0]
            depth = (depth - depth.min()) / (depth.max() - depth.min()) * 255.0
            depth = depth.cpu().numpy().astype(np.uint8)
        
        return depth

    def create_depth_message(self, depth_map, header):
        depth_msg = self.bridge.cv2_to_imgmsg(depth_map, encoding='mono8')
        depth_msg.header = header
        return depth_msg

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