# CINE-Sensing

Sensing stack for the Cinematic Intelligent Navigation Engine. Runs on a Raspberry Pi 5 mounted to a drone and feeds localization + perception data to the [CINE trajectory planner](https://github.com/fishnos/CINE).

The stack combines:

- Visual-inertial odometry via VINS-Fusion (vendored, ARM-compatible ROS 2 port)
- YOLO object detection for subject tracking
- IMU bridge that re-publishes MAVROS data in the frame VINS expects
- MAVROS setpoint bridge for cinematography commands from CINE

---

## Repo layout

```
CINE-Sensing/
├── sensing_ws/src/
│   ├── camera_publisher/                  # ROS 2 node — RPi Camera Module 3 → /camera/image_raw
│   ├── imu_publisher/                     # ROS 2 nodes — IMU bridge, gyroscope, VIO relay
│   ├── yolo_detection/                    # ROS 2 node — YOLO bounding-box extractor
│   ├── setpoint_processor/                # ROS 2 node — cinematography setpoints → MAVROS
│   └── VINS-Fusion-ROS2-humble-arm/       # VIO pipeline (vendored third-party, do not edit)
├── calibration/                           # Camera calibration scripts + calib_data/
├── configs/
│   ├── json/          # Source of truth: camera.json, gyroscope.json, user_params.json, vins.json
│   ├── python/        # Typed Python loader + backwards-compat shim
│   ├── cpp/           # Generated C++ headers
│   └── gyroscope/     # ROS 2 YAML params for gyroscope_publisher
├── data_visualization/                    # Offline plot scripts (trajectory, stats, MLP curves)
├── datasets/                              # Not tracked by git; see datasets/README.md
├── docs/                                  # Decision documents and plans
├── tools/                                 # download_models.py and other utilities
└── VERSION
```

---

## Prerequisites

| Requirement  | Version                             |
| ------------ | ----------------------------------- |
| Ubuntu       | 24.04 LTS (Noble)                   |
| ROS 2        | Jazzy                               |
| Python       | 3.10+                               |
| Ceres Solver | 2.x (via `rosdep` / `apt`)          |
| Eigen3       | 3.x (via `apt`)                     |
| OpenCV       | 4.x (via `apt ros-jazzy-cv-bridge`) |

Install ROS 2 Jazzy per the [official guide](https://docs.ros.org/en/jazzy/Installation.html). Then:

```bash
# ROS deps (run from repo root)
rosdep install --from-paths sensing_ws/src --ignore-src -r -y

# Python deps (for training scripts, data_visualization, tools)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> ROS 2 runtime deps (`rclpy`, `sensor_msgs`, `cv_bridge`, etc.) come from the
> ROS install, not pip.

---

## Build

```bash
# From repo root
source /opt/ros/jazzy/setup.bash
cd sensing_ws
colcon build --symlink-install
cd ..
source sensing_ws/install/setup.bash
```

Or use the convenience wrapper (sets `ROS_DOMAIN_ID`, sources venv + ROS + workspace):

```bash
source source_env.sh
```

---

## Run

### 1. Environment variable (optional but recommended)

```bash
export CINE_SENSING_ROOT=/path/to/CINE-Sensing
```

If unset, launch files and nodes walk up from `__file__` to locate the repo root.

### 2. Camera

```bash
ros2 launch camera_publisher camera_launch.py
```

Parameters (camera ID, topic, frame ID) are read from `configs/json/camera.json` at
launch time via `configs/python`.

### 3. IMU / gyroscope

```bash
# Gyroscope serial publisher + VIO relay
ros2 launch imu_publisher imu_publisher_launch.py

# IMU axis-transform bridge only (publishes to /imu_bridge/data_raw)
ros2 launch imu_publisher imu_bridge_launch.py
```

The gyroscope node reads serial config from `configs/gyroscope/comms.yaml`. The
`imu_publisher_launch.py` file resolves the path via `CINE_SENSING_ROOT` or the
sentinel walk.

### 4. YOLO detection

```bash
ros2 run yolo_detection bb_extractor
```

Model weights must be present at the path in `configs/json/user_params.json`
(`MODEL_PATH`, relative to repo root). Download them first:

```bash
python3 tools/download_models.py
```

### 5. VINS-Fusion VIO (full stack)

VINS-Fusion is launched through a ROS 2 node wrapper (`run_vins.py`) that generates
a runtime config from `sensing_ws/src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/rpi_v3_mono_config.yaml`
with output paths substituted in-place. The generated file is gitignored.

```bash
# Full VIO stack (camera + IMU bridge + VINS)
ros2 launch sensing_ws/src/VINS-Fusion-ROS2-humble-arm/vins/launch/complete_vio.launch.py
```

Alternatively via the Python runner:

```bash
python3 sensing_ws/src/VINS-Fusion-ROS2-humble-arm/vins/run_vins.py
```

### 6. Setpoint processor

```bash
ros2 run setpoint_processor mavros_setpoints
```

Bridges cinematography pose setpoints from CINE over `/cine/setpoint` to MAVROS.

---

## Datasets and model weights

**Datasets** are not tracked in git. See `datasets/README.md` for contents and
download instructions (HomeObjects-3K, 412 MB).

**Model weights** (`homeobjects_yolo11n_trained.pt`) are attached to GitHub
releases and downloaded by:

```bash
python3 tools/download_models.py
```

The script reads the current `VERSION` file to resolve the correct release tag.

---

## Configuration

`configs/json/` is the single source of truth for shared parameters. Edit values
there; do not hard-code paths or constants in node source files.

| File               | Contents                                                       |
| ------------------ | -------------------------------------------------------------- |
| `camera.json`      | Camera topic, frame ID, device ID                              |
| `gyroscope.json`   | Serial port, baud rate                                         |
| `user_params.json` | YOLO model path, detection constants, rule-of-thirds constants |
| `vins.json`        | VINS-Fusion config path and VIO parameters                     |

`configs/python/__init__.py` exposes typed classes (`CameraConfig`, `GyroscopeConfig`,
`ModelDetectionConstants`, etc.) and resolves `MODEL_PATH` to an absolute path via
`CINE_SENSING_ROOT` or the sentinel walk. See `configs/README.md` for the full
contract.

---

## VIO troubleshooting

**IMU/VIO drift** — known open issue. See `docs/2026-06-13-vio-drift-decision.md`
for the full analysis: three independent change-types (IMU axis remap in
`imu_bridge.py`, MAVROS topic selection, and noise model retuning) each require
on-hardware static drift testing before any can be merged. The S5 refactor
already on `main` is representation-only and numerically identical to the prior code.
**Do not adopt any drift-fix variant without hardware validation.**

**Missing model weights** — run `python3 tools/download_models.py`. Requires the
correct GitHub release tag to exist; check `VERSION` matches a published release.

**Missing calibration** — run `python3 calibration/calibrate_camera.py` with
chessboard images in `calibration/images/`. Output written to
`calibration/calib_data/calibration.npz`.

**`CINE_SENSING_ROOT` unset** — launch files fall back to a sentinel walk. Set the
variable explicitly if you see path-resolution errors.

**ROS 2 build failures in VINS-Fusion** — Ceres and Eigen must be installed via
`rosdep`/`apt` before `colcon build`. The vendored VINS source requires a system
install; it does not bundle these libraries.

---

## Related

- [CINE](https://github.com/fishnos/CINE) — trajectory optimization and planning
