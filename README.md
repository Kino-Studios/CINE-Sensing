# CINE-Sensing

**Cinematic Intelligent Navigation Engine - Sensing Module**

This repository contains the sensing and perception components for the CINE project, including camera integration, object detection, and data collection for cinematographic drone navigation.

## Repository Structure

```
CINE-Sensing/
├── sensing_ws/src/
│   ├── camera_publisher/      # ROS2 camera node (RPi Camera Module 3)
│   ├── imu_publisher/         # ROS2 IMU/gyroscope node (Pixhawk FC)
│   ├── object_detection/      # ROS2 YOLO-based bounding box detection node
│   ├── setpoint_processor/    # ROS2 MAVROS setpoint bridge
│   └── VINS-Fusion-ROS2-humble-arm/  # VIO pipeline (third-party)
├── calibration/               # Camera calibration scripts and data
├── configs/                   # Multi-format configuration files
├── datasets/                  # Training datasets
├── docs/                      # Documentation and plans
├── tools/                     # Utility scripts
└── vins_output/               # VIO output
```

## Configuration

Configuration files are available in multiple formats for cross-platform compatibility:

| Format | Path                          | Use Case                  |
| ------ | ----------------------------- | ------------------------- |
| Python | `configs/python/constants.py` | Primary Python config     |
| Python | `configs/python/__init__.py`  | JSON-backed Python module |
| C++    | `configs/cpp/`                | C++ header files          |
| JSON   | `configs/json/`               | Language-agnostic configs |
| YAML   | `configs/gyroscope/`          | ROS2 node parameters      |

## Key Components

- **Object Detection**: YOLO-based bounding box detection (`object_detection` package)
- **Camera Integration**: ROS2 camera publisher (`camera_publisher` package)
- **IMU/Gyroscope**: Serial communication with Pixhawk flight controller (`imu_publisher` package)
- **Setpoint Bridge**: Cinematography setpoints to MAVROS (`setpoint_processor` package)

## Related Repository

- [CINE](https://github.com/fishnos/CINE) - Main trajectory optimization and planning module
