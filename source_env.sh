# Source this file (`source source_env.sh`); do not execute it.
#
# Sets the ROS environment for CINE-Sensing: ROS 2 Jazzy, then the colcon workspace
# that holds this repository. The workspace is found from CINE_SENSING_WS when set,
# otherwise as the directory two levels above this file (<ws>/src/CINE-Sensing).

CINE_SENSING_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CINE_SENSING_WS="${CINE_SENSING_WS:-$(cd "$CINE_SENSING_REPO/../.." && pwd)}"

export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"
export PYTHONUNBUFFERED=1

# Optional virtual environment for the pip-only Python packages (requirements.txt).
if [ -f "$CINE_SENSING_REPO/venv/bin/activate" ]; then
    source "$CINE_SENSING_REPO/venv/bin/activate"
fi

if [ -f /opt/ros/jazzy/setup.bash ]; then
    source /opt/ros/jazzy/setup.bash
else
    echo "source_env.sh: /opt/ros/jazzy/setup.bash not found; install ROS 2 Jazzy first." >&2
fi

if [ -f "$CINE_SENSING_WS/install/setup.bash" ]; then
    source "$CINE_SENSING_WS/install/setup.bash"
else
    echo "source_env.sh: $CINE_SENSING_WS/install/setup.bash not found; run colcon build in $CINE_SENSING_WS." >&2
fi
