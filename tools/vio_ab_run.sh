#!/usr/bin/env bash
# Run one labeled VIO config against the canonical bag and append a results row.
#
# Usage: bash tools/vio_ab_run.sh <label> [bag_path] [duration_s]
#
# Set the config in configs/json/vins.json BEFORE running (it is the single source of
# truth). NEVER hand-edit the generated rpi_v3_mono_config.yaml — it is regenerated on
# every launch and carries a DO-NOT-EDIT banner.
set -euo pipefail

LABEL="${1:?usage: vio_ab_run.sh <label> [bag] [duration]}"
BAG="${2:-datasets/vio_bags/canonical}"
DUR="${3:-30}"
RESULTS="vins_output/drift_results.csv"

REPLAY_LAUNCH="sensing_ws/src/VINS-Fusion-ROS2-humble-arm/vins/launch/replay_vio.launch.py"
DRIFT_TEST="sensing_ws/src/VINS-Fusion-ROS2-humble-arm/vins/tests/static_drift_test.py"

echo "[$LABEL] launching deterministic replay against $BAG ..."
ros2 launch "$REPLAY_LAUNCH" bag:="$BAG" &
LAUNCH_PID=$!

# Give VINS time to initialize before the static-drift window starts.
sleep 5
python3 "$DRIFT_TEST" --label "$LABEL" --duration "$DUR" --results-csv "$RESULTS"

kill "$LAUNCH_PID" 2>/dev/null || true
wait "$LAUNCH_PID" 2>/dev/null || true
echo "[$LABEL] done. Results appended to $RESULTS"
