from geometry_msgs.msg import TwistStamped, Vector3Stamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import Imu


class GyroscopePublisher(Node):
    def __init__(self):
        super().__init__("gyroscope_publish")

        sensor_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.subscriber = self.create_subscription(
            Imu, "mavros/imu/data", self.imu_callback, sensor_qos
        )
        self.subscriber = self.create_subscription(
            Odometry, "vins_estimator/odometry", self.vio_callback, sensor_qos
        )
        self.vector_publisher = self.create_publisher(Vector3Stamped, "gyroscope/data", sensor_qos)
        self.twist_publisher = self.create_publisher(TwistStamped, "gyroscope/twist", sensor_qos)

    def imu_callback(self, msg: Imu):
        gyro_msg = Vector3Stamped()
        gyro_msg.header = msg.header
        gyro_msg.vector.x = msg.angular_velocity.x
        gyro_msg.vector.y = msg.angular_velocity.y
        gyro_msg.vector.z = msg.angular_velocity.z

        twist_msg = TwistStamped()
        twist_msg.header = msg.header
        twist_msg.twist.angular.x = msg.angular_velocity.x
        twist_msg.twist.angular.y = msg.angular_velocity.y
        twist_msg.twist.angular.z = msg.angular_velocity.z
        twist_msg.twist.linear.x = msg.linear_acceleration.x
        twist_msg.twist.linear.y = msg.linear_acceleration.y
        twist_msg.twist.linear.z = msg.linear_acceleration.z

        self.vector_publisher.publish(gyro_msg)
        self.twist_publisher.publish(twist_msg)

    def vio_callback(self, msg: Odometry):
        vio_pose_msg = Odometry()
        vio_pose_msg.header = msg.header
        vio_pose_msg.pose.position.x = msg.pose.position.x
        vio_pose_msg.pose.position.y = msg.pose.position.y
        vio_pose_msg.pose.position.z = msg.pose.position.z
        vio_pose_msg.pose.orientation.x = msg.pose.orientation.x
        vio_pose_msg.pose.orientation.y = msg.pose.orientation.y
        vio_pose_msg.pose.orientation.z = msg.pose.orientation.z
        vio_pose_msg.pose.orientation.w = msg.pose.orientation.w
        vio_pose_msg.twist.linear.x = msg.twist.linear.x
        vio_pose_msg.twist.linear.y = msg.twist.linear.y
        vio_pose_msg.twist.linear.z = msg.twist.linear.z
