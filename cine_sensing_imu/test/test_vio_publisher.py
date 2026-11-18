import pytest

rclpy = pytest.importorskip('rclpy')

from cine_sensing_imu.vio_publisher import VIOPublisher  # noqa: E402
from geometry_msgs.msg import PoseStamped  # noqa: E402
from nav_msgs.msg import Odometry  # noqa: E402

MAXIMUM_SPINS = 50
NO_POSE_MESSAGE = 'no pose on /mavros/vision_pose/pose after 50 spins'


@pytest.fixture
def start_vio_node():
    nodes = []

    def start(ros_arguments):
        rclpy.init(args=ros_arguments)
        vio_node = VIOPublisher()
        probe_node = rclpy.create_node('vio_publisher_probe')
        nodes.extend([vio_node, probe_node])

        return vio_node, probe_node

    yield start

    for node in nodes:
        node.destroy_node()

    rclpy.shutdown()


def publish_one_odometry_and_collect_autopilot_poses(vio_node, probe_node):
    received_poses = []
    probe_node.create_subscription(
        PoseStamped,
        '/mavros/vision_pose/pose',
        received_poses.append,
        10,
    )
    odometry_publisher = probe_node.create_publisher(Odometry, '/odometry', 10)
    odometry = Odometry()
    odometry.pose.pose.position.x = 1.5
    odometry.pose.pose.position.y = -2.0
    odometry.pose.pose.position.z = 0.25

    for _ in range(MAXIMUM_SPINS):
        odometry_publisher.publish(odometry)
        rclpy.spin_once(vio_node, timeout_sec=0.05)
        rclpy.spin_once(probe_node, timeout_sec=0.05)

        if received_poses:
            break

    return received_poses


def test_vio_publisher_forwards_pose_to_autopilot_when_enabled(start_vio_node):
    vio_node, probe_node = start_vio_node(['--ros-args', '-p', 'forward_to_autopilot:=true'])

    received_poses = publish_one_odometry_and_collect_autopilot_poses(vio_node, probe_node)

    assert received_poses, NO_POSE_MESSAGE
    assert received_poses[0].pose.position.x == 1.5


def test_vio_publisher_sends_nothing_to_autopilot_by_default(start_vio_node):
    vio_node, probe_node = start_vio_node([])

    received_poses = publish_one_odometry_and_collect_autopilot_poses(vio_node, probe_node)

    assert received_poses == []
