export ROS_DOMAIN_ID=0
PORT=/dev/ttyAMA0
BAUD=115200

source /opt/ros/jazzy/setup.bash

ros2 launch mavros apm.launch \
  fcu_url:=serial://$PORT:$BAUD \
  gcs_url:=udp://@ \
  system_id:=255 tgt_system:=1 tgt_component:=1 \
  use_sim_time:=false