#!/usr/bin/env bash
if ! command -v ros2 >/dev/null 2>&1; then
  echo 'ros2 not found: source /opt/ros/jazzy/setup.bash and your workspace install/setup.bash first.' >&2
  exit 1
fi

PORT=/dev/ttyAMA0
BAUD=921600

ros2 launch mavros apm.launch \
  fcu_url:=serial://$PORT:$BAUD \
  gcs_url:=udp://@ \
  system_id:=255 tgt_system:=1 tgt_component:=1 \
  use_sim_time:=false \
  plugin_allowlist:=[] \
  plugin_denylist:=[time_sync]
