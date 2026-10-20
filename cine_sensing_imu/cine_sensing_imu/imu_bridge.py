import logging

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import Imu

# Exceptions raised on the rclpy shutdown path when the context is already torn
# down (e.g. a second shutdown after Ctrl-C, or shutdown triggered externally).
# These are the only ones we expect to swallow at process exit; anything else
# should propagate. Imported defensively because the set varies across distros.
_SHUTDOWN_EXC = []
try:
    from rclpy.executors import ExternalShutdownException

    _SHUTDOWN_EXC.append(ExternalShutdownException)
except ImportError:
    pass
try:
    from rclpy.handle import InvalidHandle

    _SHUTDOWN_EXC.append(InvalidHandle)
except ImportError:
    pass
try:
    from rclpy._rclpy_pybind11 import RCLError

    _SHUTDOWN_EXC.append(RCLError)
except ImportError:
    pass
SHUTDOWN_EXCEPTIONS = tuple(_SHUTDOWN_EXC) if _SHUTDOWN_EXC else (RuntimeError,)

# Axis remap from the raw MAVROS IMU frame into the frame VINS-Fusion expects.
#
# Derivation of each axis (sensor input -> VINS output):
#   VINS x  <- sensor  y   (the two horizontal axes are swapped)
#   VINS y  <- sensor  x
#   VINS z  <- sensor -z   (vertical axis is flipped)
#
# As a rotation/reflection matrix R (out = R @ in) this is:
#   [ 0  1  0 ]   row 0: take +in.y -> out.x
#   [ 1  0  0 ]   row 1: take +in.x -> out.y
#   [ 0  0 -1 ]   row 2: take -in.z -> out.z
#
# This reproduces the previous inline swap/negate EXACTLY (it is a pure
# permutation-with-sign, so no floating-point arithmetic is introduced and the
# numeric output is byte-identical to the old statements). The same R is applied
# to both the linear acceleration and angular velocity vectors.
#
# IMPORTANT: whether THIS mapping is the physically correct one is an open
# hardware question (see docs/2026-06-13-vio-drift-decision.md). This refactor
# intentionally preserves the existing mapping unchanged; do not "fix" signs or
# axis order here without on-drone validation.
#
# In a production system this transform belongs in URDF/TF2, not in the bridge.
R_IMU_TO_VINS = np.array(
    [
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 0.0, -1.0],
    ]
)


class IMUBridge(Node):
    def __init__(self):
        super().__init__('imu_bridge')

        self.get_logger().info('bridge started')

        self.declare_parameter('use_transform', False)
        self.use_transform = self.get_parameter('use_transform').value

        self.mavros_imu_sub = self.create_subscription(
            Imu, '/mavros/imu/data_raw', self.imu_callback, qos_profile_sensor_data
        )

        vins_qos = QoSProfile(
            depth=200, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.VOLATILE
        )

        self.vins_imu_pub = self.create_publisher(Imu, '/imu_bridge/data_raw', vins_qos)

        self.msg_count = 0

    def imu_callback(self, msg):
        self.msg_count += 1
        if self.msg_count % 100 == 1:
            self.get_logger().info(f'Received IMU message #{self.msg_count}')

        if self.use_transform:
            in_accel_x = msg.linear_acceleration.x
            in_accel_y = msg.linear_acceleration.y

            accel = R_IMU_TO_VINS @ np.array(
                [
                    msg.linear_acceleration.x,
                    msg.linear_acceleration.y,
                    msg.linear_acceleration.z,
                ]
            )
            gyro = R_IMU_TO_VINS @ np.array(
                [
                    msg.angular_velocity.x,
                    msg.angular_velocity.y,
                    msg.angular_velocity.z,
                ]
            )

            msg.linear_acceleration.x = accel[0]
            msg.linear_acceleration.y = accel[1]
            msg.linear_acceleration.z = accel[2]

            msg.angular_velocity.x = gyro[0]
            msg.angular_velocity.y = gyro[1]
            msg.angular_velocity.z = gyro[2]

            self.get_logger().info(
                f'transform applied: accel {in_accel_x:.2f},{in_accel_y:.2f} -> {msg.linear_acceleration.x:.2f},{msg.linear_acceleration.y:.2f}',
                once=True,
            )

        msg.header.frame_id = 'imu'

        self.vins_imu_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    try:
        imu_bridge = IMUBridge()
        rclpy.spin(imu_bridge)
    except KeyboardInterrupt:
        pass
    finally:
        if 'imu_bridge' in locals():
            imu_bridge.destroy_node()
        try:
            rclpy.shutdown()
        except SHUTDOWN_EXCEPTIONS as exc:
            logging.getLogger('imu_bridge').debug('rclpy already shut down: %s', exc)


if __name__ == '__main__':
    main()
