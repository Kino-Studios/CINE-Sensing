if ! command -v ros2 >/dev/null 2>&1; then
  echo 'ros2 not found: source /opt/ros/jazzy/setup.bash and your workspace install/setup.bash first.' >&2
  exit 1
fi

echo "=== data diagnosis (ROS_DOMAIN_ID: $ROS_DOMAIN_ID) ==="

timeout 3s ros2 topic echo /mavros/state --once --field connected || echo "MAVROS State: No data (Timeout)"

timeout 5s ros2 topic hz /mavros/imu/data_raw --window 10 || echo "MAVROS IMU: No data"

timeout 5s ros2 topic hz /imu_bridge/data_raw --window 10 || echo "Bridge IMU: No data"

timeout 5s ros2 topic hz /camera/image_raw --window 10 || echo "Camera: No data"

timeout 5s ros2 topic hz /imu_propagate --window 10 || echo "VINS IMU Propagate: No data (Is VINS running? Is Bridge sending data?)"

timeout 5s ros2 topic hz /odometry --window 10 || echo "VINS Odometry: No data (VINS initialized? Moved drone?)"

timeout 2s ros2 topic list | grep path || echo "Path topic: Not found"
