# VIO testing

Drift is compared by recording one rosbag and replaying it for every configuration under
test. Live flights are never compared with each other, because different motion on each
run makes the numbers incomparable.

## Recording the bag once, on the Pi

1. Start the camera, the IMU bridge, and MAVROS, but not VINS. Check that all three topics
   publish: `ros2 topic hz /camera/image_raw /imu_bridge/data_raw /mavros/imu/data_raw`.
2. Put the rig on a rigid surface and run `bash tools/vio_record_bag.sh datasets/vio_bags/canonical`.
3. Hold it completely still for about 35 s (a 30 s drift window plus VINS start-up), then
   move it by hand in a slow figure-8 for about 20 s, and stop with `Ctrl-C`. The figure-8
   is what tells a mirrored IMU axis mapping apart from a rotated one.
4. `ros2 bag info datasets/vio_bags/canonical` should list all three topics over about 55 s.
   `datasets/` is ignored by git; keep the bag outside the repository.

## Comparing a configuration

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
first pass the bag comparison in this page.
