# Canonical VIO Bag — Recording Protocol

Record **once**. Every config under test replays this exact bag, so the camera + IMU
stream is identical every run and the drift numbers are actually comparable. Live
flight is never A/B'd — different motion each run makes metrics meaningless.

## Steps (on the Pi)

1. Start sensors only — **do not** start `vins_node` yet:
   - `ros2 launch cine_sensing_camera camera.launch.py`
   - `ros2 launch cine_sensing_imu imu_bridge.launch.py`
   - MAVROS up and publishing `/mavros/imu/data_raw`
2. Confirm all three topics publish:
   `ros2 topic hz /camera/image_raw /imu_bridge/data_raw /mavros/imu/data_raw`
3. Place the rig on a rigid, static surface.
4. Start recording: `bash tools/vio_record_bag.sh datasets/vio_bags/canonical`
5. Hold **completely still for ~35 s** (the static-drift window is 30 s; the extra
   covers VINS initialization).
6. Then do a slow, controlled hand-held **figure-8 for ~20 s**. This motion segment is
   what distinguishes a reflection from a rotation in the future IMU-remap A/B — keep
   it in the same bag.
7. `Ctrl-C` to stop.

## Result

- Bag at `datasets/vio_bags/canonical/` (mcap). This is the fixture for the replay
  harness (`tools/vio_ab_run.sh`).
- `datasets/vio_bags/` is gitignored (large binary). Keep the bag on the Pi; do not
  commit it. If you need a shared copy, store it outside git.

## Verify

`ros2 bag info datasets/vio_bags/canonical` should report all three topics with
non-zero message counts and ~55 s duration.
