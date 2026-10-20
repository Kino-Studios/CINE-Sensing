#!/usr/bin/env bash
# Run one labeled VIO config against the canonical bag and append a results row.
#
# Usage: bash tools/vio_ab_run.sh <label> [bag_path] [duration_s] [profile]
#
# The VINS config is generated from cine_sensing_config/config/vins.json, or from the
# files of <profile> under cine_sensing_config/config/profiles/ when one is given. Edit
# those JSON files, never the generated YAML: it is rewritten on every launch and
# carries a DO-NOT-EDIT banner. The profile is recorded in the CSV row.
#
# Run from the repository root with the workspace sourced (install/setup.bash).
set -euo pipefail

LABEL="${1:?usage: vio_ab_run.sh <label> [bag] [duration] [profile]}"
BAG="${2:-datasets/vio_bags/canonical}"
DUR="${3:-30}"
PROFILE="${4:-${CINE_SENSING_PROFILE:-}}"
RESULTS="vins_output/drift_results.csv"

DRIFT_TEST="third_party/vins_fusion/vins/tests/static_drift_test.py"

echo "[$LABEL] launching deterministic replay against $BAG (profile: ${PROFILE:-base}) ..."
ros2 launch vins replay_vio.launch.py bag:="$BAG" profile:="$PROFILE" &
LAUNCH_PID=$!

# Give VINS time to initialize before the static-drift window starts.
sleep 5
python3 "$DRIFT_TEST" --label "$LABEL" --duration "$DUR" --results-csv "$RESULTS" \
  --profile "$PROFILE"

kill "$LAUNCH_PID" 2>/dev/null || true
wait "$LAUNCH_PID" 2>/dev/null || true
echo "[$LABEL] done. Results appended to $RESULTS"
