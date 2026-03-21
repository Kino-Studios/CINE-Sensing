source ~/CINE-Sensing/source_env.sh

PORT=/dev/ttyAMA0
BAUD=921600

ros2 launch mavros apm.launch \
  fcu_url:=serial://$PORT:$BAUD \
  gcs_url:=udp://@ \
  system_id:=255 tgt_system:=1 tgt_component:=1 \
  use_sim_time:=false \
  plugin_allowlist:=[] \
  plugin_denylist:=[time_sync]
