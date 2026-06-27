#!/usr/bin/env bash
# Record the canonical VIO test bag. Run on the Pi with the full sensor stack live
# (camera_publisher + imu_bridge + MAVROS) BEFORE starting vins_node. Record ONCE;
# every config under test replays this same bag so drift metrics are comparable.
#
# Usage: bash tools/vio_record_bag.sh [output_dir]
set -euo pipefail

OUT="${1:-datasets/vio_bags/canonical}"
mkdir -p "$(dirname "$OUT")"

echo "Recording to: $OUT  (Ctrl-C to stop)"
echo "Topics: /camera/image_raw /imu_bridge/data_raw /mavros/imu/data_raw"
echo "Protocol: hold STILL ~35s, then a slow figure-8 ~20s. See docs/vio_testing/RECORDING_PROTOCOL.md"

# /mavros/imu/data_raw is recorded too so a future IMU-remap A/B can replay through
# imu_bridge without re-recording. Baseline replay uses /imu_bridge/data_raw directly.
ros2 bag record \
  --storage mcap \
  -o "$OUT" \
  /camera/image_raw \
  /imu_bridge/data_raw \
  /mavros/imu/data_raw
