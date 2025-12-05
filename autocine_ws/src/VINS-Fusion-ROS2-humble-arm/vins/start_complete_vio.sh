export ROS_DOMAIN_ID=0
echo "Set ROS_DOMAIN_ID to: $ROS_DOMAIN_ID"

source /opt/ros/jazzy/setup.bash
source /home/fishnos/bspline-cinematography-generator-research/autocine_ws/install/setup.bash

/home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/fc_data/launch/start_mavros.sh &
MAVROS_PID=$!
echo "MAVROS started with PID: $MAVROS_PID"

sleep 5

python3 /home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/fc_data/launch/imu_bridge.py &
IMU_BRIDGE_PID=$!
echo "IMU bridge started with PID: $IMU_BRIDGE_PID"

sleep 2

python3 /home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/rpi_camera_publisher/rpi_camera_publisher/camera_publisher.py &
CAMERA_PID=$!
echo "Camera publisher started with PID: $CAMERA_PID"

sleep 2

/home/fishnos/bspline-cinematography-generator-research/autocine_ws/install/vins/lib/vins/vins_node /home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/rpi_v3_mono_config.yaml &
VINS_PID=$!
echo "VINS node started with PID: $VINS_PID"

sleep 3

/home/fishnos/bspline-cinematography-generator-research/autocine_ws/install/loop_fusion/lib/loop_fusion/loop_fusion_node /home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/rpi_v3_mono_config.yaml &
LOOP_PID=$!
echo "Loop fusion started with PID: $LOOP_PID"

cleanup() {
    kill $MAVPROXY_PID $MAVROS_PID $IMU_BRIDGE_PID $CAMERA_PID $VINS_PID $LOOP_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT

wait