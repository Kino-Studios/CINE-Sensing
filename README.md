# CINE-Sensing

[![CI](https://github.com/Kino-Studios/CINE-Sensing/actions/workflows/ci.yml/badge.svg)](https://github.com/Kino-Studios/CINE-Sensing/actions/workflows/ci.yml)
[![License: GPL-3.0-only](https://img.shields.io/badge/license-GPL--3.0--only-blue.svg)](LICENSE)
[![ROS 2 Jazzy](https://img.shields.io/badge/ROS%202-Jazzy-22314E.svg)](https://docs.ros.org/en/jazzy/)

CINE-Sensing is the sensory portion of the CINE (the Cinematic Intelligent Navigation Engine) codebase. It runs on a Raspberry Pi 5 on the drone and turns the camera and the flight controller's motion sensor into three things
the planner needs: where the drone is, what the subject is, and where the subject sits in
the frame. The planning half of this study, along with the results and the paper, is in
[CINE](https://github.com/Kino-Studios/CINE).

If you use CINE-Sensing in research, please cite it with [`CITATION.cff`](CITATION.cff);
[`references.bib`](references.bib) lists the work it builds on.

On the drone, the camera driver, the motion-sensor bridge, the flight-controller link, and
the YOLO subject detector all work. Depth works as well, although it runs on a separate
GPU computer that talks to the Pi over ROS 2. The position estimate (visual-inertial
odometry) is the part still unfinished: it runs on the drone but drifts, and until the
cause is found ([open issue](docs/vio-testing.md#open-issue-vio-drift)), the drone cannot
fly autonomously. Calibration is unsettled too, since two candidate camera calibrations
disagree and which of them is correct has not been tested on hardware
([profiles](docs/configuration.md#profiles)).

## 1. Hardware

The drone carries a Raspberry Pi 5 with a Raspberry Pi Camera Module 3 (published at
1152x648) and an ArduPilot flight controller, which the Pi reaches through MAVROS over
serial (`/dev/ttyAMA0` at 921600 baud; see `cine_sensing_imu/launch/start_mavros.sh`).
The full parts list is in [docs/hardware.md](docs/hardware.md).

## 2. Prerequisites

The Pi runs Ubuntu 24.04 and ROS 2 Jazzy. VINS-Fusion also needs Ceres Solver 2.1 because
it uses an API that Ceres 2.2 (the Ubuntu 24.04 package) removed; the build steps below
compile 2.1 from source, and [`third_party/vins_fusion/UPSTREAM.md`](third_party/vins_fusion/UPSTREAM.md)
has the details.

## 3. Build

```bash
mkdir -p ~/cine_ws/src && cd ~/cine_ws/src
git clone https://github.com/Kino-Studios/CINE-Sensing.git
CINE-Sensing/tools/install_ceres_2_1.sh
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths . -yi --rosdistro jazzy
# Data MAVROS needs; rosdep cannot fetch it. sudo drops /opt/ros from PATH, hence the full path.
sudo "$(ros2 pkg prefix mavros)/lib/mavros/install_geographiclib_datasets.sh"
# Ubuntu 24.04 refuses pip installs into the system Python, and so the pip-only packages
# go in a venv that can still see the ROS Python packages. source_env.sh activates it.
python3 -m venv --system-site-packages CINE-Sensing/venv
CINE-Sensing/venv/bin/pip install -r CINE-Sensing/requirements.txt
python3 CINE-Sensing/tools/download_assets.py
cd ~/cine_ws && colcon build --symlink-install
source ~/cine_ws/src/CINE-Sensing/source_env.sh
```

The asset script, `tools/download_assets.py`, fetches the files kept out of git from the
GitHub Release matching `VERSION`: the loop-closure vocabulary `brief_k10L6.bin`, the
`global_fusion` RViz meshes, and the camera-calibration images. It checks each file's
SHA-256 and refuses to overwrite a file that does not match; `--only <name>` fetches a
single file.

The trained HomeObjects-3K weights are not published. Out of the box, the YOLO detector
therefore loads the stock `yolo11n.pt` (COCO classes), which Ultralytics downloads on its
first run, and keeps detections of class 56 (chair). To use your own weights, put them in
`cine_sensing_yolo/models/` before building, then set `MODEL_PATH` and `USER_OBJECT_ID` in
`cine_sensing_config/config/user_params.json`.

Each new terminal needs `source_env.sh`, which activates `CINE-Sensing/venv` when present,
sources ROS 2 Jazzy and `~/cine_ws/install/setup.bash` (the workspace two levels above the
repository, or `$CINE_SENSING_WS`), and defaults `ROS_DOMAIN_ID` to 0.

## 4. Run on the drone

```bash
# Camera: greyscale on /camera/image_raw (for VINS), colour on /camera/image_color (for YOLO)
ros2 launch cine_sensing_camera camera.launch.py

# IMU bridge: republishes /mavros/imu/data_raw on /imu_bridge/data_raw for VINS
# (axis remap only with use_transform:=true, off by default and unvalidated)
ros2 launch cine_sensing_imu imu_bridge.launch.py

# Gyroscope rates from MAVROS + VIO relay (VINS /odometry to /vio/pose, /vio/odometry, TF)
ros2 launch cine_sensing_imu imu_publisher.launch.py

# YOLO bounding-box extractor
ros2 run cine_sensing_yolo bb_extractor

# Full VIO stack (MAVROS + IMU bridge + camera + VINS + loop fusion)
ros2 launch vins complete_vio.launch.py
ros2 launch vins complete_vio.launch.py profile:=rpi_v3_tune_maxcnt250   # with a profile
# Options: vins_start_delay:=5.0 (seconds before VINS starts), use_transform:=false
# (IMU axis remap in imu_bridge; unvalidated, see docs/vio-testing.md), use_depth:=false
# (true also starts cine_depth on this machine; it must be installed in the workspace)

# Setpoint processor (bridges CINE setpoints to MAVROS)
ros2 run cine_sensing_setpoint mavros_setpoints
```

Depth normally runs on the GPU computer rather than on the Pi. With both machines on the
same `ROS_DOMAIN_ID`, start `ros2 launch cine_depth depth_publisher.launch.py` on the GPU
computer (see
[Depth Anything 3 in CINE](https://github.com/Kino-Studios/CINE/blob/main/docs/mlp-and-depth.md#depth-anything-3)).

Parameters live in `cine_sensing_config/config/`, and
[docs/configuration.md](docs/configuration.md) explains both them and the profiles that
override them. To record a bag and compare drift between two settings, follow
[docs/vio-testing.md](docs/vio-testing.md).

## 5. Results

YOLO11n, fine-tuned on HomeObjects-3K (12 household object classes), scored as follows on
that dataset's 404-image validation set:

| Precision | Recall | mAP50 | mAP50-95 |
| --- | --- | --- | --- |
| about 0.71 | 0.60 | 0.65 | 0.44 |

On the real camera, with the drone on the ground and moved by hand, CINE cut the subject's
average distance from its rule-of-thirds target from 127.6 px to 32.5 px. What these
scores mean, along with the confusion matrix and the remaining details, is in
[docs/results.md](docs/results.md).

## 6. Code layout

| Package | What it does |
| --- | --- |
| `cine_sensing_camera` | Publishes Raspberry Pi Camera Module 3 frames: greyscale on `/camera/image_raw`, colour on `/camera/image_color` |
| `cine_sensing_imu` | Republishes MAVROS IMU data for VINS, gyroscope publisher, VIO pose relay |
| `cine_sensing_yolo` | YOLO detector on the colour image, publishing the tracked subject's bounding box |
| `cine_sensing_setpoint` | Forwards CINE setpoints to MAVROS |
| `cine_sensing_config` | Shared JSON configuration, profiles, and its Python loader |
| `third_party/vins_fusion/` (`vins`, `loop_fusion`, `global_fusion`, `camera_models`) | VINS-Fusion, modified; the VIO launch files live in `vins/launch/` |

Alongside these packages, `tools/` holds the asset downloader, the Ceres install script,
the formatter, the VIO A/B and bag-recording scripts, and the camera calibration scripts
(`tools/calibration/`). How the pieces connect, and why some of them are built the way
they are, is in [docs/how-it-works.md](docs/how-it-works.md).

## 7. Troubleshooting

If the vocabulary or meshes are missing, run `python3 tools/download_assets.py`, rebuild so
the files are installed, and check that `VERSION` matches a published release. Drift in
the position estimate is a known problem, described in the
[open issue](docs/vio-testing.md#open-issue-vio-drift).

For anything else, please open an issue. Pull requests are welcome too, and
[CONTRIBUTING.md](CONTRIBUTING.md) lists the checks to run before sending one.

## 8. Acknowledgements

The position estimate is built on [VINS-Fusion](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion)
(HKUST Aerial Robotics Group) and its ROS 2 port. For the rest, the camera model classes
come from [OpenVINS](https://github.com/rpng/open_vins), loop-closure place recognition
comes from [DBoW2](https://github.com/dorian3d/DBoW2), and the optimiser is
[Ceres Solver](http://ceres-solver.org/); detection uses
[Ultralytics YOLO](https://github.com/ultralytics/ultralytics).

## 9. Licence

CINE-Sensing is licensed GPL-3.0-only (see [`LICENSE`](LICENSE)).
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) lists the third-party code and data,
their licences, and what is downloaded rather than shipped.
