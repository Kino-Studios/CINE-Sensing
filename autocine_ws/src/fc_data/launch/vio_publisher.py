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
            reliability=QoSReliabilityPolicy.RELIABLE,
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
        
        self.image_subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            sensor_qos
        )
        
        self.vins_imu_publisher = self.create_publisher(
            Imu,
            '/vins/imu',
            sensor_qos
        )
        
        self.vins_image_publisher = self.create_publisher(
            Image,
            '/vins/image',
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
        
        if self.last_imu_time and (self.last_imu_time.sec % 5 == 0):
            self.get_logger().info(f'IMU: angular_vel=[{msg.angular_velocity.x:.3f}, {msg.angular_velocity.y:.3f}, {msg.angular_velocity.z:.3f}], linear_acc=[{msg.linear_acceleration.x:.3f}, {msg.linear_acceleration.y:.3f}, {msg.linear_acceleration.z:.3f}]')

    def image_callback(self, msg: Image):
        vins_image_msg = Image()
        vins_image_msg.header = msg.header
        vins_image_msg.header.frame_id = "camera"
        vins_image_msg.height = msg.height
        vins_image_msg.width = msg.width
        vins_image_msg.encoding = msg.encoding
        vins_image_msg.is_bigendian = msg.is_bigendian
        vins_image_msg.step = msg.step
        vins_image_msg.data = msg.data
        
        self.vins_image_publisher.publish(vins_image_msg)
        self.last_image_time = msg.header.stamp

    def publish_vio_pose(self, pose, timestamp):
        pose_msg = PoseStamped()
        pose_msg.header.stamp = timestamp
        pose_msg.header.frame_id = "map"
        pose_msg.pose = pose
        
        self.pose_publisher.publish(pose_msg)
        
        t = TransformStamped()
        t.header.stamp = timestamp
        t.header.frame_id = "map"
        t.child_frame_id = "base_link"
        t.transform.translation.x = pose.position.x
        t.transform.translation.y = pose.position.y
        t.transform.translation.z = pose.position.z
        t.transform.rotation = pose.orientation
        
        self.tf_broadcaster.sendTransform(t)

    def publish_vio_odometry(self, pose, twist, timestamp):
        odom_msg = Odometry()
        odom_msg.header.stamp = timestamp
        odom_msg.header.frame_id = "map"
        odom_msg.child_frame_id = "base_link"
        odom_msg.pose.pose = pose
        odom_msg.twist.twist = twist
        
        self.odometry_publisher.publish(odom_msg)

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
