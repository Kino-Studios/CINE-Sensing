PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
fi

if [ -f "$PROJECT_ROOT/sensing_ws/install/setup.bash" ]; then
    source "$PROJECT_ROOT/sensing_ws/install/setup.bash"
fi

if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
    export PATH="$PROJECT_ROOT/venv/bin:$PATH"
fi
