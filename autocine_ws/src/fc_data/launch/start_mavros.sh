export ROS_DOMAIN_ID=0
source /opt/ros/jazzy/setup.bash
source ~/bspline-cinematography-generator-research/autocine_ws/install/setup.bash

ros2 launch mavros apm.launch \
  fcu_url:=serial:///dev/ttyAMA0:115200 \
  gcs_url:=udp://@ \
  system_id:=255 tgt_system:=1 tgt_component:=1 \
  use_sim_time:=false