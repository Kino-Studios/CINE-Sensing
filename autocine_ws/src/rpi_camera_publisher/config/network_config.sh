# Network Configuration for ROS2 Multi-Machine Setup
# Raspberry Pi Camera to Omen 15 Communication

# ROS2 Domain Configuration
# Both machines must use the same ROS_DOMAIN_ID
export ROS_DOMAIN_ID=42

# Network Discovery Configuration
# For better performance over WiFi/Ethernet
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

# FastRTPS Configuration for better network performance
export FASTRTPS_DEFAULT_PROFILES_FILE=/path/to/fastrtps_profile.xml

# Optional: Set specific network interface (replace with your interface)
# export ROS_LOCALHOST_ONLY=0
# export RMW_IMPLEMENTATION=rmw_cyclonedx_cpp

# Raspberry Pi specific settings (run on RPi)
# export ROS_HOSTNAME=$(hostname -I | awk '{print $1}')  # Get first IP

# Omen 15 specific settings (run on Omen 15)
# export ROS_HOSTNAME=$(hostname -I | awk '{print $1}')  # Get first IP

# Quality of Service Settings
# These can be adjusted based on your network conditions
export RMW_QOS_RELIABILITY_POLICY=RELIABLE
export RMW_QOS_DURABILITY_POLICY=VOLATILE
export RMW_QOS_HISTORY_POLICY=KEEP_LAST
export RMW_QOS_DEPTH=10

# Debugging - Enable if you need to troubleshoot
# export RCUTILS_LOGGING_SEVERITY=DEBUG
# export RCUTILS_COLORIZED_OUTPUT=1