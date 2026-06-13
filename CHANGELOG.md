# Changelog

All notable changes to this project will be documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-06-13

### Added

- `docs/2026-06-13-vio-drift-decision.md` — decision document consolidating ~11
  drift-related branches into three orthogonal change-types (IMU axis remap,
  MAVROS topic selection, noise retuning). Documents which variants need
  hardware validation before adoption.
- `configs/` directory: consolidated JSON source of truth (`camera.json`,
  `gyroscope.json`, `user_params.json`, `vins.json`), typed Python loader
  (`configs/python/__init__.py`), C++ headers, gyroscope YAML params, and
  `configs/README.md` contract document.
- `tools/download_models.py` — downloads YOLO weights from the matching GitHub
  release tag, derived from `VERSION`.
- `datasets/README.md` — documents HomeObjects-3K contents and download options.
- `ruff.toml` — linter and formatter config (line-length 100, py310, VINS-Fusion
  excluded).
- `CHANGELOG.md` (this file).

### Changed

- Package renames: `rpi_camera_publisher` → `camera_publisher`,
  `fc_data` → `imu_publisher`, `model_framing` → `yolo_detection`.
  All entry points, topics, and import paths updated accordingly.
- Config paths made portable: all nodes resolve paths via `CINE_SENSING_ROOT`
  env var or a sentinel walk; no hardcoded absolute paths remain in source.
- `imu_bridge.py` (S5): representation-only refactor separating axis-transform
  logic from the bridge node. Numerically identical to prior code; the actual
  axis-remap decision is deferred to hardware validation (see decision doc).
- `imu_publisher_launch.py`: config path resolved via `CINE_SENSING_ROOT` /
  sentinel walk; no install-time copy required.
- `run_vins.py` / `launch_complete_vio.py`: runtime config generation via
  targeted text substitution; generated file gitignored.
- `requirements.txt`: all deps bounded to `>=X,<NEXT_MAJOR`; ROS 2 runtime
  deps documented as rosdep-provided (not pip).
- `calibrate_camera.py`: converted error and warning prints in ROS nodes and
  calibration scripts to `logging`; interactive CLI progress output left as
  print. Module docstring and import order cleaned up.
- All data_visualization and calibration/tools scripts gained `#!/usr/bin/env python3`
  shebangs.
- Codebase formatted with `ruff format` + `ruff check --fix` (34 files
  reformatted, 44 lint fixes applied).

### Fixed

- `numpy.load` calls hardened with `allow_pickle=False` (security fix, S1).
- Critical path and config bugs preventing package build and node startup (S2).
- VINS-Fusion config output paths were hardcoded; now substituted at runtime (S3).

### Notes

- VINS-Fusion (`sensing_ws/src/VINS-Fusion-ROS2-humble-arm/`) is vendored
  upstream; its C++/Python source is unmodified. Only the active rpi_camera_v3
  config file was changed — portable output-path handling and a documented
  extrinsics-provenance comment (no calibration values altered).

---

## [1.0.0] - 2026-05 (reconstructed)

Initial stable release. Established ROS 2 Jazzy workspace with camera publisher,
IMU/gyroscope publisher, YOLO detection node, setpoint processor, and vendored
VINS-Fusion VIO pipeline. First successful colcon build and YOLO training run on
HomeObjects-3K dataset with Comet ML logging.
