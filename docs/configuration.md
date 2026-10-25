# Configuration

`cine_sensing_config/config/` holds the shared parameters (`camera.json`, `gyroscope.json`,
`user_params.json`, `vins.json`). Edit values there; do not hard-code paths or constants in
node source files. Nodes read the installed copy, so rebuild (or use `--symlink-install`)
after editing. The VINS YAML file is generated from `vins.json` on every VIO launch, so
edits to the generated file are lost.

## Profiles

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

Which camera intrinsics are correct is untested. The two camera profiles disagree by about
1.5x in focal length; which one matches the camera as it is actually driven at 1152x648
has not been checked on hardware. None of the profiles has been compared with the base
configuration on a recorded bag either; use `tools/vio_ab_run.sh` ([VIO testing](vio-
testing.md)) for that before adopting one.

To add a profile, create the directory, write a `profile.json` with `status`
(`calibrated` or `uncalibrated-candidate`), `source`, `notes` and, when known,
`reprojection_error_px`, and copy in only the files you change, complete. Camera values go
in `vins_camera.json`, using the keys of the VINS camera YAML (`model_type`,
`camera_name`, `image_width`, `image_height`, `distortion_parameters`,
`projection_parameters`); the generator writes them beside the generated config and
points VINS at them. Rebuild so the new files are installed.
