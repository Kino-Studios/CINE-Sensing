export ROS_DOMAIN_ID=0
echo "Set ROS_DOMAIN_ID to: $ROS_DOMAIN_ID"

source /opt/ros/jazzy/setup.bash
source /home/fishnos/bspline-cinematography-generator-research/autocine_ws/install/setup.bash

echo "Starting MAVProxy..."
cd /home/fishnos/bspline-cinematography-generator-research
source venv/bin/activate
mavproxy.py --master=/dev/ttyAMA0,115200 --out=udp:0.0.0.0:14550 --mav20 --aircraft MyDrone &
MAVPROXY_PID=$!
echo "MAVProxy started with PID: $MAVPROXY_PID"
deactivate

sleep 5

echo "Starting MAVROS..."
source /opt/ros/jazzy/setup.bash
source /home/fishnos/bspline-cinematography-generator-research/autocine_ws/install/setup.bash
/home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/fc_data/launch/start_mavros.sh &
MAVROS_PID=$!
echo "MAVROS started with PID: $MAVROS_PID"

sleep 5

echo "Starting IMU bridge..."
python3 /home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/fc_data/launch/imu_bridge.py &
IMU_BRIDGE_PID=$!
echo "IMU bridge started with PID: $IMU_BRIDGE_PID"

sleep 2

echo "Starting camera publisher..."
python3 /home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/rpi_camera_publisher/rpi_camera_publisher/camera_publisher.py &
CAMERA_PID=$!
echo "Camera publisher started with PID: $CAMERA_PID"

echo "Waiting for camera and IMU to initialize..."
sleep 5

echo "Starting VINS node..."
/home/fishnos/bspline-cinematography-generator-research/autocine_ws/install/vins/lib/vins/vins_node /home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/rpi_v3_mono_config.yaml &
VINS_PID=$!
echo "VINS node started with PID: $VINS_PID"

sleep 3

echo "Starting loop fusion..."
/home/fishnos/bspline-cinematography-generator-research/autocine_ws/install/loop_fusion/lib/loop_fusion/loop_fusion_node /home/fishnos/bspline-cinematography-generator-research/autocine_ws/src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/rpi_v3_mono_config.yaml &
LOOP_PID=$!
echo "Loop fusion started with PID: $LOOP_PID"

echo "All components started!"
echo "MAVProxy PID: $MAVPROXY_PID"
echo "MAVROS PID: $MAVROS_PID"
echo "IMU Bridge PID: $IMU_BRIDGE_PID" 
echo "Camera PID: $CAMERA_PID"
echo "VINS PID: $VINS_PID"
echo "Loop Fusion PID: $LOOP_PID"

echo "Press Ctrl+C to stop all processes"

# Function to kill all processes
cleanup() {
    echo "Stopping all processes..."
    kill $MAVPROXY_PID $MAVROS_PID $IMU_BRIDGE_PID $CAMERA_PID $VINS_PID $LOOP_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT

wait