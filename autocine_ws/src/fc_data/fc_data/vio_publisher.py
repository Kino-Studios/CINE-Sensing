import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy
from sensor_msgs.msg import Imu, Image
from geometry_msgs.msg import Vector3Stamped, PoseStamped
from nav_msgs.msg import Odometry
import tf2_ros
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
import numpy as np

class VIOPublisher(Node):
    def __init__(self):
        super().__init__('vio_publisher')
        
        sensor_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.imu_subscription = self.create_subscription(
            Imu,
            'mavros/imu/data',
            self.imu_callback,
            sensor_qos
        )
        
        self.vins_odom_subscription = self.create_subscription(
            Odometry,
            '/vins_estimator/odometry',
            self.vins_odom_callback,
            sensor_qos
        )
        
        self.vins_imu_publisher = self.create_publisher(
            Imu,
            '/imu_bridge/data_raw',
            sensor_qos
        )
        
        self.pose_publisher = self.create_publisher(
            PoseStamped,
            '/vio/pose',
            sensor_qos
        )
        
        self.odometry_publisher = self.create_publisher(
            Odometry,
            '/vio/odometry',
            sensor_qos
        )
        
        self.tf_broadcaster = TransformBroadcaster(self)
    
        self.last_imu_time = None
        self.last_image_time = None
        
        self.get_logger().info('VIO Publisher initialized for VINS-Fusion integration')

    def imu_callback(self, msg: Imu):
        vins_imu_msg = Imu()
        vins_imu_msg.header = msg.header
        vins_imu_msg.header.frame_id = "imu"
        vins_imu_msg.linear_acceleration = msg.linear_acceleration
        vins_imu_msg.angular_velocity = msg.angular_velocity
        vins_imu_msg.orientation = msg.orientation
        vins_imu_msg.linear_acceleration_covariance = msg.linear_acceleration_covariance
        vins_imu_msg.angular_velocity_covariance = msg.angular_velocity_covariance
        vins_imu_msg.orientation_covariance = msg.orientation_covariance
        
        self.vins_imu_publisher.publish(vins_imu_msg)
        self.last_imu_time = msg.header.stamp

    def vins_odom_callback(self, msg: Odometry):
        vio_odom_msg = Odometry()
        vio_odom_msg.header.stamp = msg.header.stamp
        vio_odom_msg.header.frame_id = "map"
        vio_odom_msg.child_frame_id = "base_link"
        vio_odom_msg.pose = msg.pose
        vio_odom_msg.twist = msg.twist
        
        self.odometry_publisher.publish(vio_odom_msg)
        
        pose_msg = PoseStamped()
        pose_msg.header = vio_odom_msg.header
        pose_msg.pose = msg.pose.pose
        self.pose_publisher.publish(pose_msg)
        
        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = "map"
        t.child_frame_id = "base_link"
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation
        
        self.tf_broadcaster.sendTransform(t)
        
        if msg.header.stamp.sec % 5 == 0:
            pos = msg.pose.pose.position
            self.get_logger().info(f'VIO Position: x={pos.x:.3f}, y={pos.y:.3f}, z={pos.z:.3f}')

def main(args=None):
    rclpy.init(args=args)
    node = VIOPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()