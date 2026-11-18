#!/usr/bin/env bash
if ! command -v ros2 >/dev/null 2>&1; then
  echo 'ros2 not found: source /opt/ros/jazzy/setup.bash and your workspace install/setup.bash first.' >&2
  exit 1
fi

FCU_URL="${FCU_URL:-serial:///dev/ttyAMA0:921600}"
USE_SIM_TIME="${USE_SIM_TIME:-false}"

ros2 launch mavros apm.launch \
  fcu_url:="$FCU_URL" \
  gcs_url:=udp://@ \
  system_id:=255 tgt_system:=1 tgt_component:=1 \
  use_sim_time:="$USE_SIM_TIME" \
  plugin_allowlist:=[] \
  plugin_denylist:=[time_sync]
