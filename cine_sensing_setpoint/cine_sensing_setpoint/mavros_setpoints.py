import rclpy
from geometry_msgs.msg import PoseStamped, TwistStamped, Vector3Stamped
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy


class SetpointPublisher(Node):
    def __init__(self):
        super().__init__("mavros_setpoints")

        mavros_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.mavros_position_pub = self.create_publisher(
            PoseStamped, "/mavros/setpoint_position/local", mavros_qos
        )

        self.mavros_velocity_pub = self.create_publisher(
            TwistStamped, "/mavros/setpoint_velocity/cmd_vel", mavros_qos
        )

        self.mavros_acceleration_pub = self.create_publisher(
            Vector3Stamped, "/mavros/setpoint_accel/accel", mavros_qos
        )

        self.mavros_attitude_pub = self.create_publisher(
            PoseStamped, "/mavros/setpoint_attitude/attitude", mavros_qos
        )

        self.mavros_attitude_velocity_pub = self.create_publisher(
            TwistStamped, "/mavros/setpoint_attitude/cmd_vel", mavros_qos
        )

        self.mavros_attitude_acceleration_pub = self.create_publisher(
            Vector3Stamped, "/mavros/setpoint_attitude/accel", mavros_qos
        )

        self.setpoint_translational_position_subscriber = self.create_subscription(
            PoseStamped,
            "/cinematography/translational_position_setpoints",
            self.translational_position_callback,
            mavros_qos,
        )

        self.setpoint_translational_velocity_subscriber = self.create_subscription(
            TwistStamped,
            "/cinematography/translational_velocity_setpoints",
            self.translational_velocity_callback,
            mavros_qos,
        )

        self.setpoint_translational_acceleration_subscriber = self.create_subscription(
            Vector3Stamped,
            "/cinematography/translational_acceleration_setpoints",
            self.translational_acceleration_callback,
            mavros_qos,
        )

        self.setpoint_attitude_position_subscriber = self.create_subscription(
            PoseStamped,
            "/cinematography/attitude_position_setpoints",
            self.attitude_position_callback,
            mavros_qos,
        )

        self.setpoint_attitude_velocity_subscriber = self.create_subscription(
            TwistStamped,
            "/cinematography/attitude_velocity_setpoints",
            self.attitude_velocity_callback,
            mavros_qos,
        )

        self.setpoint_attitude_acceleration_subscriber = self.create_subscription(
            Vector3Stamped,
            "/cinematography/attitude_acceleration_setpoints",
            self.attitude_acceleration_callback,
            mavros_qos,
        )

    def translational_position_callback(self, msg: PoseStamped):
        self.mavros_position_pub.publish(msg)

    def translational_velocity_callback(self, msg: TwistStamped):
        self.mavros_velocity_pub.publish(msg)

    def translational_acceleration_callback(self, msg: Vector3Stamped):
        self.mavros_acceleration_pub.publish(msg)

    def attitude_position_callback(self, msg: PoseStamped):
        self.mavros_attitude_pub.publish(msg)

    def attitude_velocity_callback(self, msg: TwistStamped):
        self.mavros_attitude_velocity_pub.publish(msg)

    def attitude_acceleration_callback(self, msg: Vector3Stamped):
        self.mavros_attitude_acceleration_pub.publish(msg)


def main():
    rclpy.init()
    node = SetpointPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
