PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export ROS_DOMAIN_ID=0
export PYTHONUNBUFFERED=1

if [ -d "$PROJECT_ROOT/venv" ]; then
    if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
        source "$PROJECT_ROOT/venv/bin/activate"
    fi
fi

if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
fi

if [ -f "$PROJECT_ROOT/sensing_ws/install/setup.bash" ]; then
    source "$PROJECT_ROOT/sensing_ws/install/setup.bash"
fi
