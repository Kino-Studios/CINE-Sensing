import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Vector3Stamped
from geometry_msgs.msg import TwistStamped

class GyroscopePublisher(Node):
    def __init__(self):
        super().__init__('gyroscope_publish')

        sensor_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.subscriber = self.create_subscription(
            Imu,
            'mavros/imu/data',
            self.imu_callback,
            sensor_qos
        )
        self.vector_publisher = self.create_publisher(Vector3Stamped, 'gyroscope/data', sensor_qos)
        self.twist_publisher = self.create_publisher(TwistStamped, 'gyroscope/twist', sensor_qos)


    # called by subscriber to publish gyroscope data
    def imu_callback(self, msg: Imu):
        position_msg = Vector3Stamped()
        position_msg.header = msg.header
        position_msg.vector.x = msg.vector.x
        position_msg.vector.y = msg.vector.y
        position_msg.vector.z = msg.vector.z

        twist_msg = TwistStamped()
        twist_msg.header = msg.header
        twist_msg.twist.angular.x = msg.twist.angular.x
        twist_msg.twist.angular.y = msg.twist.angular.y
        twist_msg.twist.angular.z = msg.twist.angular.z
        twist_msg.twist.linear.x = msg.twist.linear.x
        twist_msg.twist.linear.y = msg.twist.linear.y
        twist_msg.twist.linear.z = msg.twist.linear.z

        self.vector_publisher.publish(position_msg)
        self.twist_publisher.publish(twist_msg)