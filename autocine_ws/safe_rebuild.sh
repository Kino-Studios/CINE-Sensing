#!/bin/bash
# Safe ROS2 package rebuild script for Raspberry Pi
# Prevents memory overload by limiting parallelism and using sequential builds

set -e

echo "=== Safe ROS2 Package Rebuild ==="
echo "This will rebuild all ROS2 packages with RPi-safe settings"
echo ""

# Source ROS2
source /opt/ros/jazzy/setup.bash

# Move to workspace
cd /home/fishnos/CINE-Sensing/autocine_ws

# Check memory
echo "Current memory status:"
free -h
echo ""

# Build dependencies first (Eigen3 and Ceres)
echo "Step 1/3: Building Eigen3..."
colcon build --packages-select Eigen3 \
    --cmake-args -DCMAKE_BUILD_TYPE=Release \
    --parallel-workers 2 \
    --executor sequential

echo ""
echo "Step 2/3: Building Ceres solver (this will take 5-10 minutes)..."
colcon build --packages-select ceres-solver \
    --cmake-args -DCMAKE_BUILD_TYPE=Release -DCXSPARSE=OFF \
    --parallel-workers 2 \
    --executor sequential

# Build VINS packages
echo ""
echo "Step 3/3: Building camera models and VINS packages..."
colcon build --packages-select camera_models loop_fusion global_fusion vins \
    --cmake-args -DCMAKE_BUILD_TYPE=Release \
    --parallel-workers 1 \
    --executor sequential

# Build Python packages
echo ""
echo "Building Python packages..."
colcon build --packages-select fc_data model_framing rpi_camera_publisher setpoint_processor \
    --parallel-workers 2

echo ""
echo "=== Build Complete! ==="
echo "Source the workspace with: source install/setup.bash"
free -h
