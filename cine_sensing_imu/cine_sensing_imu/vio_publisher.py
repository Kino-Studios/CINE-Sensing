import rclpy
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from tf2_ros import TransformBroadcaster


class VIOPublisher(Node):
    def __init__(self):
        super().__init__('vio_publisher')

        vins_pub_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # VINS-Fusion's estimator node has no namespace, and so its relative "odometry"
        # topic is /odometry. VINS reads its IMU from the IMU bridge, not from this node.
        self.vins_odom_subscription = self.create_subscription(
            Odometry, '/odometry', self.vins_odom_callback, vins_pub_qos
        )

        self.pose_publisher = self.create_publisher(PoseStamped, '/vio/pose', vins_pub_qos)

        self.odometry_publisher = self.create_publisher(Odometry, '/vio/odometry', vins_pub_qos)

        self.tf_broadcaster = TransformBroadcaster(self)

    def vins_odom_callback(self, msg: Odometry):
        vio_odom_msg = Odometry()
        vio_odom_msg.header.stamp = msg.header.stamp
        vio_odom_msg.header.frame_id = 'map'
        vio_odom_msg.child_frame_id = 'base_link'
        vio_odom_msg.pose = msg.pose
        vio_odom_msg.twist = msg.twist

        self.odometry_publisher.publish(vio_odom_msg)

        pose_msg = PoseStamped()
        pose_msg.header = vio_odom_msg.header
        pose_msg.pose = msg.pose.pose

        self.pose_publisher.publish(pose_msg)

        transform = TransformStamped()
        transform.header.stamp = msg.header.stamp
        transform.header.frame_id = 'map'
        transform.child_frame_id = 'base_link'
        transform.transform.translation.x = msg.pose.pose.position.x
        transform.transform.translation.y = msg.pose.pose.position.y
        transform.transform.translation.z = msg.pose.pose.position.z
        transform.transform.rotation = msg.pose.pose.orientation

        self.tf_broadcaster.sendTransform(transform)


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
