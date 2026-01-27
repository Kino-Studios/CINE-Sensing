# CINE-Sensing
<<<<<<< HEAD

**Cinematic Intelligent Navigation Engine - Sensing Module**

This repository contains the sensing and perception components for the CINE project, including camera integration, object detection, and data collection for cinematographic drone navigation.

## Configuration

Configuration files are available in multiple formats for cross-platform compatibility:

| Format | Path | Use Case |
|--------|------|----------|
| Python | `configs/user_params/constants.py` | Primary Python config (original) |
| Python | `configs/python/` | Alternative Python module |
| C++ | `configs/cpp/` | C++ header files |
| JSON | `configs/json/` | Language-agnostic configs |
| YAML | `configs/camera/`, `configs/gyroscope/` | ROS2 node parameters |

## Key Components

- **Object Detection**: YOLO-based bounding box detection with rule-of-thirds framing
- **Camera Integration**: ROS2 camera publisher with RPi Camera Module 3 support
- **IMU/Gyroscope**: Serial communication with Pixhawk flight controller
- **Data Collection**: Tools for collecting framing and trajectory data

## Related Repository

- [CINE](https://github.com/fishnos/CINE) - Main trajectory optimization and planning module
=======
>>>>>>> 8d5a5ed33209708afc2da3441ec786221012673c
