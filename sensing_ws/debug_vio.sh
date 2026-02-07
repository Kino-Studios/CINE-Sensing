source ~/CINE-Sensing/source_env.sh

echo "=== data diagnosis (ROS_DOMAIN_ID: $ROS_DOMAIN_ID) ==="

timeout 3s ros2 topic echo /mavros/state --once --field connected || echo "MAVROS State: No data (Timeout)"

timeout 5s ros2 topic hz /mavros/imu/data_raw --window 10 || echo "MAVROS IMU: No data"

timeout 5s ros2 topic hz /imu_bridge/data_raw --window 10 || echo "Bridge IMU: No data"

timeout 5s ros2 topic hz /camera/image_raw --window 10 || echo "Camera: No data"

timeout 5s ros2 topic hz /imu_propagate --window 10 || echo "VINS IMU Propagate: No data (Is VINS running? Is Bridge sending data?)"

timeout 5s ros2 topic hz /odometry --window 10 || echo "VINS Odometry: No data (VINS initialized? Moved drone?)"

timeout 2s ros2 topic list | grep path || echo "Path topic: Not found"
