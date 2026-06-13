from geometry_msgs.msg import TwistStamped, Vector3Stamped
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
        self.vector_publisher = self.create_publisher(Vector3Stamped, "gyroscope/data", sensor_qos)
        self.twist_publisher = self.create_publisher(TwistStamped, "gyroscope/twist", sensor_qos)

    # called by subscriber to publish gyroscope data for VINS
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
