# CINE-Sensing

[![CI](https://github.com/Kino-Studios/CINE-Sensing/actions/workflows/ci.yml/badge.svg)](https://github.com/Kino-Studios/CINE-Sensing/actions/workflows/ci.yml)
[![License: GPL-3.0-only](https://img.shields.io/badge/license-GPL--3.0--only-blue.svg)](LICENSE)
[![ROS 2 Jazzy](https://img.shields.io/badge/ROS%202-Jazzy-22314E.svg)](https://docs.ros.org/en/jazzy/)

<p align="center">
  <img src="docs/media/drone.jpg" width="360" alt="The CINE drone: a 5-inch carbon frame carrying a Raspberry Pi 5 and camera in blue 3D-printed mounts">
  <br>
  <em>The CINE drone (second version).</em>
</p>

CINE-Sensing is the sensory portion of the CINE (the Cinematic Intelligent Navigation Engine) codebase. It runs on a Raspberry Pi 5 on the drone and turns the camera and the flight controller's motion sensor into three things
the planner needs: where the drone is, what the subject is, and where the subject sits in
the frame. The planning half of this study, along with the results and the paper, is in
[CINE](https://github.com/Kino-Studios/CINE).

## Status

| Part | State |
| --- | --- |
| Camera driver, motion-sensor bridge, flight-controller link | **Works on the drone.** |
| Subject detection (YOLO) | **Works on the drone.** Trained model measured on its validation set; see Results. |
| Depth from the camera | **Works**, on a separate GPU computer that talks to the Pi over ROS 2. |
| Position estimate (visual-inertial odometry) | **Runs on the drone but drifts.** The cause is not settled; see [Open issue: VIO drift](#open-issue-vio-drift). Until it is fixed, the drone cannot fly autonomously. |
| Camera calibration | **Two candidate calibrations disagree**, and which one is correct has not been evaluated on hardware; see [Profiles](#profiles). |

## Components

Visual-inertial odometry comes from
[VINS-Fusion](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion) (HKUST Aerial Robotics
Group), through a ROS 2 port, kept in `third_party/vins_fusion/` with every change listed
in its [`UPSTREAM.md`](third_party/vins_fusion/UPSTREAM.md). Its camera models are
[OpenVINS](https://github.com/rpng/open_vins)'s, detection uses
[Ultralytics YOLO](https://github.com/ultralytics/ultralytics), and MAVROS talks to the
flight controller. [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) lists all bundled
code. This repository adds:

- the ROS 2 nodes in the `cine_sensing_*` packages: the camera publisher, the bridge
  that hands the flight controller's motion data to VINS, the YOLO detector node, and the
  relay that passes CINE's position targets to the flight controller;
- a detector setup for YOLO11n fine-tuned on the HomeObjects-3K dataset (12 kinds of
  household object); the trained weights are not published;
- camera calibration scripts in `tools/calibration/`;
- a VIO test harness: record one flight's sensor data once, replay it through every
  configuration, and compare drift on identical input (`tools/vio_ab_run.sh`,
  `third_party/vins_fusion/vins/tests/`);
- the configuration system in `cine_sensing_config/`, including profiles that swap in
  one set of camera or tuning values without editing the base files.

## Hardware

| Part | Model |
| --- | --- |
| Frame | TBS Source One, 5-inch, carbon fibre |
| Flight controller | Matek H743-Mini, running ArduPilot |
| Motor controller (ESC) | SpeedyBee F405, 35 A |
| Motors and propellers | EMAX ECO II 2207 1700KV, three-blade propellers |
| Battery | 6S, 1300 mAh |
| Onboard computer | Raspberry Pi 5, 8 GB, in a 3D-printed mount |
| Camera | Raspberry Pi Camera Module 3, wide-angle |
| Depth computer (on the ground) | A PC with an NVIDIA GTX 1660 Ti on the same ROS 2 network |

### Build photos

<table>
  <tr>
    <td><img src="docs/media/parts.jpg" width="260" alt="Drone parts laid out on a table, including the Raspberry Pi 5"></td>
    <td><img src="docs/media/soldering.jpg" width="260" alt="Soldering the drone electronics at a workbench"></td>
    <td><img src="docs/media/frame.jpg" width="260" alt="Bare carbon frame with motors and the flight-controller stack mounted"></td>
  </tr>
  <tr>
    <td align="center"><em>Parts</em></td>
    <td align="center"><em>Soldering the electronics</em></td>
    <td align="center"><em>Frame, motors and flight controller</em></td>
  </tr>
  <tr>
    <td><img src="docs/media/pi-mount.jpg" width="260" alt="Raspberry Pi 5 with its cooler in an orange 3D-printed mount"></td>
    <td><img src="docs/media/drone-v1.jpg" width="260" alt="First assembled version of the drone"></td>
    <td><img src="docs/media/drone-v2.jpg" width="260" alt="Second version of the drone with blue printed parts and the camera on a raised stand"></td>
  </tr>
  <tr>
    <td align="center"><em>Pi 5 in a printed mount</em></td>
    <td align="center"><em>Version 1</em></td>
    <td align="center"><em>Version 2, camera raised</em></td>
  </tr>
</table>

### Design notes

- A large depth model takes seconds per frame on the Pi's CPU, so depth runs on a
  separate computer with a GTX 1660 Ti, which receives the Pi's images over ROS 2 and
  sends depth back. The VIO launch file initiates depth on the Pi only when asked
  (`use_depth:=true`).
- VINS-Fusion's camera library (camodocal) is licensed CC-BY-SA 2.0, which cannot be
  combined with GPL-3.0 code. It was replaced with OpenVINS's camera classes, and
  `third_party/vins_fusion/camera_models/tests/` checks the new code against values
  camodocal produced before it was removed.
- VINS-Fusion uses part of the Ceres solver that was removed in Ceres 2.2, the version
  Ubuntu 24.04 ships, so `tools/install_ceres_2_1.sh` builds 2.1 from source.
- No two test flights move the same way, and so the harness records the sensor data once
  and replays the same recording through every configuration.

<p align="center">
  <img src="docs/media/calibration.jpg" width="280" alt="Camera calibration target taped to a wall">
  <img src="docs/media/depth.jpg" width="440" alt="Depth Anything depth map from the drone camera, showing a person in a room">
  <br>
  <em>Left: a calibration target. Right: a depth map from the drone's camera, computed
  on the GPU computer.</em>
</p>

## Results

### Subject detection

YOLO11n fine-tuned on HomeObjects-3K (12 classes; 2,285 training
and 404 validation images), measured on the validation set:

| Precision | Recall | mAP50 | mAP50-95 |
| --- | --- | --- | --- |
| about 0.71 | 0.60 | 0.65 | 0.44 |

Precision is the share of detections that were right, recall the share of real objects
found; mAP50 and mAP50-95 are the standard detection scores at a loose and a strict
overlap threshold. The mean recall across the 12 classes is 67.7%.

<p align="center">
  <img src="docs/media/yolo-confusion.jpg" width="560" alt="Normalised confusion matrix for the 12 household object classes; the diagonal ranges from 0.48 for door to 0.79 for photo frame">
  <br>
  <em>How often each class was confused with each other class. Windows and doors score
  lowest; the bottom row shows objects the model missed entirely.</em>
</p>

### Framing on the real camera

On this hardware, with the drone on the ground and moved
by hand, CINE cut the subject's average distance from its rule-of-thirds target from
127.6 px to 32.5 px. The flight results are in
[CINE](https://github.com/Kino-Studios/CINE#results); they come from simulation.

## Pipeline

```mermaid
flowchart LR
    CAM["RPi Camera Module 3"]
    CP["camera_publisher<br/>/camera/image_raw (grey)<br/>/camera/image_color"]
    MAVROS["MAVROS<br/>(flight controller)"]
    IB["cine_sensing_imu<br/>imu_bridge<br/>/imu_bridge/data_raw"]
    VINS["VINS-Fusion VIO<br/>(pose estimate)"]
    YOLO["cine_sensing_yolo<br/>bb_extractor<br/>(bounding boxes)"]
    DEPTH["cine_depth<br/>(GPU computer)"]
    SP["cine_sensing_setpoint<br/>mavros_setpoints"]
    CINE["CINE planner<br/>(sibling repo)"]

    CAM --> CP
    CP -->|grey image| VINS
    CP -->|grey image| DEPTH
    MAVROS -->|IMU raw| IB
    IB -->|remapped IMU| VINS
    CP -->|colour image| YOLO
    VINS -->|pose| CINE
    YOLO -->|detections| CINE
    DEPTH -->|depth| CINE
    CINE -->|setpoints| SP
    SP -->|pose setpoints| MAVROS
```

## Supported platform

| | |
| --- | --- |
| OS / ROS | Ubuntu 24.04, ROS 2 Jazzy |
| Computer | Raspberry Pi 5 |
| Camera | Raspberry Pi Camera Module 3, published at 1152x648 |
| Flight controller | ArduPilot over MAVROS (`apm.launch`, serial `/dev/ttyAMA0` at 921600 baud; see `cine_sensing_imu/launch/start_mavros.sh`) |
| Depth (optional) | Any machine on the same ROS 2 network with the CINE repository's `cine_depth`; a CUDA GPU is recommended |

## Install

**Requires:** Ubuntu 24.04 and ROS 2 Jazzy. VINS-Fusion needs Ceres Solver 2.1, which the
script below builds from source, because it uses an API that Ceres 2.2 (the Ubuntu 24.04
package) removed; see [`third_party/vins_fusion/UPSTREAM.md`](third_party/vins_fusion/UPSTREAM.md).

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

`tools/download_assets.py` fetches the files kept out of git from the GitHub Release
matching `VERSION`: the loop-closure vocabulary `brief_k10L6.bin`, the `global_fusion`
RViz meshes, and the camera-calibration images. It checks each file's SHA-256 and refuses
to overwrite a file that does not match. `--only <name>` fetches one file.

The trained HomeObjects-3K weights are not published. Out of the box the YOLO detector
loads the stock `yolo11n.pt` (COCO classes), which Ultralytics downloads on first run, and
keeps class 56 (chair). To use your own weights, put them in `cine_sensing_yolo/models/`
before building and set `MODEL_PATH` and `USER_OBJECT_ID` in
`cine_sensing_config/config/user_params.json`.

`source_env.sh` activates `CINE-Sensing/venv` when present, sources ROS 2 Jazzy and
`~/cine_ws/install/setup.bash` (the workspace two levels above the repository, or
`$CINE_SENSING_WS`) and defaults `ROS_DOMAIN_ID` to 0.

## Run

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
# (IMU axis remap in imu_bridge; unvalidated, see the open issue below), use_depth:=false
# (true also starts cine_depth on this machine; it must be installed in the workspace)

# Setpoint processor (bridges CINE setpoints to MAVROS)
ros2 run cine_sensing_setpoint mavros_setpoints
```

Depth normally runs on the GPU computer rather than the Pi: with both machines on the same
`ROS_DOMAIN_ID`, start `ros2 launch cine_depth depth_publisher.launch.py` there (see the
[CINE README](https://github.com/Kino-Studios/CINE#mlp-correction-and-depth-anything-3)).

## Configuration

`cine_sensing_config/config/` holds the shared parameters (`camera.json`, `gyroscope.json`,
`user_params.json`, `vins.json`). Edit values there; do not hard-code paths or constants in
node source files. Nodes read the installed copy, so rebuild (or use `--symlink-install`)
after editing. The VINS YAML file is generated from `vins.json` on every VIO launch, so
edits to the generated file are lost.

### Profiles

A profile is a directory `cine_sensing_config/config/profiles/<name>/` holding a
`profile.json` and only the files it overrides. When a profile is active, each file it
holds replaces the base file of the same name as a whole (keys are not merged); every
other file comes from the base. Select one with the `profile:=<name>` launch argument
of `complete_vio.launch.py` and `replay_vio.launch.py`, or the `CINE_SENSING_PROFILE`
environment variable. With no profile, VINS reads the camera intrinsics in
`third_party/vins_fusion/config/rpi_camera_v3/cam0_wide.yaml`, as before profiles existed.

| Profile | Overrides | Status |
| --- | --- | --- |
| `rpi_v3_wide` | `vins_camera.json`: the `cam0_wide.yaml` intrinsics (fx 751) | uncalibrated-candidate |
| `rpi_v3_fullfov` | `vins_camera.json`: the 2025-10-31 checkerboard calibration in `tools/calibration/camera_calibration.yaml`, scaled from the full sensor resolution to 1152x648 (fx 497.6) | calibrated |
| `rpi_v3_tune_maxcnt250` | `vins.json`: hand-tuned feature tracking (max_cnt 250, min_dist 15, equalize 1, F_threshold 1.5, min_parallax 8) and a fixed time offset (estimate_td 0) | uncalibrated-candidate |

Which camera intrinsics are correct is untested. The two camera profiles disagree by
about 1.5x in focal length; which one matches the camera as it is actually driven at
1152x648 has not been checked on hardware. None of the profiles has been compared with
the base configuration on a recorded bag either; use `tools/vio_ab_run.sh` (below) for
that before adopting one.

To add a profile, create the directory, write a `profile.json` with `status`
(`calibrated` or `uncalibrated-candidate`), `source`, `notes` and, when known,
`reprojection_error_px`, and copy in only the files you change, complete. Camera values go
in `vins_camera.json`, using the keys of the VINS camera YAML (`model_type`,
`camera_name`, `image_width`, `image_height`, `distortion_parameters`,
`projection_parameters`); the generator writes them beside the generated config and
points VINS at them. Rebuild so the new files are installed.

## VIO testing

Drift is compared by recording one rosbag and replaying it for every configuration under
test. Live flights are never compared with each other, because different motion on each
run makes the numbers incomparable.

### Recording the bag once, on the Pi

1. Start the camera, the IMU bridge, and MAVROS, but not VINS. Check that all three topics
   publish: `ros2 topic hz /camera/image_raw /imu_bridge/data_raw /mavros/imu/data_raw`.
2. Put the rig on a rigid surface and run `bash tools/vio_record_bag.sh datasets/vio_bags/canonical`.
3. Hold it completely still for about 35 s (a 30 s drift window plus VINS start-up), then
   move it by hand in a slow figure-8 for about 20 s, and stop with `Ctrl-C`. The figure-8
   is what tells a mirrored IMU axis mapping apart from a rotated one.
4. `ros2 bag info datasets/vio_bags/canonical` should list all three topics over about 55 s.
   `datasets/` is ignored by git; keep the bag outside the repository.

### Comparing a configuration

Set the values in `vins.json` (or pick a profile), run
`bash tools/vio_ab_run.sh <label> [bag] [duration_s] [profile]` from the repository root
with the workspace sourced, and read the new row in `vins_output/drift_results.csv`; the
row records the profile.
A final drift under 0.2 m over 30 s counts as good and under 0.05 m as excellent; mean
velocity while static should stay under 0.1 m/s.

The scripts in `third_party/vins_fusion/vins/tests/` are the diagnostics behind these runs:

| Script | Checks |
| --- | --- |
| `static_drift_test.py` | Drift while the rig is static; writes the CSV row |
| `imu_noise_analyzer.py` | Measured IMU noise against the noise values in the VINS config |
| `feature_quality_test.py`, `feature_tracking_visual_test.py` | Feature counts and tracking quality |
| `solver_convergence_monitor.py` | Solver failures, iteration counts, and timing |
| `timing_test.py` | Camera and IMU time synchronisation |
| `position_monitor.py` | Position over time |

## Open issue: VIO drift

VINS drifts on this hardware, and the cause is not settled. Three candidate fixes exist:
a different IMU axis mapping in `imu_bridge.py`, a different MAVROS IMU topic, and retuned
noise values. None has been validated on hardware, and so none is adopted. Any fix should
first pass the bag comparison in [VIO testing](#vio-testing).

## Troubleshooting

**Missing vocabulary or meshes:** run `python3 tools/download_assets.py`, then rebuild so the files are installed. Check `VERSION` matches a published release.

**IMU/VIO drift:** see the open-issue section above.

## Packages

| Package | Path | What it does |
| --- | --- | --- |
| `cine_sensing_camera` | `cine_sensing_camera/` | Publishes Raspberry Pi Camera Module 3 frames: greyscale on `/camera/image_raw`, colour on `/camera/image_color` |
| `cine_sensing_imu` | `cine_sensing_imu/` | Republishes MAVROS IMU data for VINS, gyroscope publisher, VIO pose relay |
| `cine_sensing_yolo` | `cine_sensing_yolo/` | YOLO detector on the colour image, publishing the tracked subject's bounding box |
| `cine_sensing_setpoint` | `cine_sensing_setpoint/` | Forwards CINE setpoints to MAVROS |
| `cine_sensing_config` | `cine_sensing_config/` | Shared JSON configuration, profiles, and its Python loader |
| `vins`, `loop_fusion`, `global_fusion`, `camera_models` | `third_party/vins_fusion/` | VINS-Fusion, modified; the VIO launch files live in `vins/launch/` |

`tools/` holds the asset downloader, the Ceres install script, the formatter, the VIO
A/B and bag-recording scripts, and the camera calibration scripts (`tools/calibration/`).

## Contributing

Issues and pull requests are welcome. Contributions are accepted under GPL-3.0-only, the
licence of this repository.

```bash
pip install pre-commit && pre-commit install   # ruff, whitespace convention, hygiene hooks
pytest                                          # pure-Python tests, no ROS needed
cd ~/cine_ws && colcon build && colcon test && colcon test-result --verbose
```

Python style is ruff (line length 100, single quotes) plus `python3 tools/format.py`, which
adds the repository's whitespace convention. Code under `third_party/` keeps its upstream
style and is excluded from the hooks; record any change to it in
`third_party/vins_fusion/UPSTREAM.md`.

## Citation

If you use CINE-Sensing in research, cite it with the metadata in
[`CITATION.cff`](CITATION.cff). [`references.bib`](references.bib) lists the work it builds
on.

## Licence

GPL-3.0-only; see [`LICENSE`](LICENSE). Third-party code and data, their licences, and
what is downloaded rather than shipped are listed in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Acknowledgements

[VINS-Fusion](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion) (HKUST Aerial
Robotics Group) and its ROS 2 port, [OpenVINS](https://github.com/rpng/open_vins) for the
camera model classes, [DBoW2](https://github.com/dorian3d/DBoW2) for loop-closure place
recognition, [Ceres Solver](http://ceres-solver.org/), and
[Ultralytics YOLO](https://github.com/ultralytics/ultralytics).

## Related

- [CINE](https://github.com/Kino-Studios/CINE): trajectory planning, the simulation
  results and the paper
