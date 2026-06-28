"""Complete VIO launch file.

Resolves sensing_ws root via CINE_SENSING_ROOT env var (preferred) or by
walking up from __file__ as a fallback.  Generates the VINS config next to
the original (targeted text substitution of the two output path lines only)
so no absolute paths are baked into source files AND the VINS C++ side still
resolves cam0_calib relative to the config's own directory.
"""

import os
import pathlib
import re

from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction

# Deterministic name for the generated sibling config (gitignored build artifact,
# overwritten each run — no /tmp accumulation).
_GENERATED_CONFIG_NAME = "rpi_v3_mono_config.generated.yaml"


def _sensing_ws_root() -> pathlib.Path:
    """Return absolute path to sensing_ws/.

    Priority:
    1. CINE_SENSING_ROOT env var → <root>/sensing_ws
    2. Sentinel walk from __file__: this file is inside sensing_ws/src/...
    """
    root_env = os.environ.get("CINE_SENSING_ROOT", "")
    if root_env:
        return pathlib.Path(root_env) / "sensing_ws"

    # .../sensing_ws/src/VINS-Fusion-ROS2-humble-arm/vins/launch_complete_vio.py
    # parents: [0]=vins  [1]=VINS-Fusion...  [2]=src  [3]=sensing_ws
    return pathlib.Path(__file__).resolve().parents[3]


def _generate_config(original_config: pathlib.Path, output_dir: pathlib.Path) -> str:
    """Write a sibling config with only the two output-path values resolved.

    Reads the original as raw text and substitutes ONLY the values of the
    `output_path:` and `pose_graph_save_path:` lines.  Every other byte — the
    %YAML:1.0 header, the cv::Mat body_T_cam0 block, float formatting — is
    preserved verbatim so OpenCV's cv::FileStorage parses it identically.

    The generated file lands in the original's own directory, so the VINS C++
    side resolves `cam0_calib` (e.g. cam0_wide.yaml) relative to that directory
    and finds the sibling intrinsics file.
    """
    raw = original_config.read_text()

    vins_out = str(output_dir) + "/"
    pose_graph_out = str(output_dir / "pose_graph") + "/"

    # Substitute only the value after the key, preserving any trailing comment.
    def _sub(text: str, key: str, value: str) -> str:
        pattern = re.compile(
            rf'^(?P<indent>\s*{re.escape(key)}\s*:\s*)"[^"]*"(?P<rest>.*)$',
            re.MULTILINE,
        )
        return pattern.sub(lambda m: f'{m.group("indent")}"{value}"{m.group("rest")}', text)

    patched = _sub(raw, "output_path", vins_out)
    patched = _sub(patched, "pose_graph_save_path", pose_graph_out)

    os.makedirs(vins_out, exist_ok=True)
    os.makedirs(pose_graph_out, exist_ok=True)

    generated = original_config.with_name(_GENERATED_CONFIG_NAME)
    generated.write_text(patched)
    return str(generated)


def generate_launch_description() -> LaunchDescription:
    sensing_ws = _sensing_ws_root()
    vins_src = sensing_ws / "src" / "VINS-Fusion-ROS2-humble-arm"

    original_config = vins_src / "config" / "rpi_camera_v3" / "rpi_v3_mono_config.yaml"

    root_env = os.environ.get("CINE_SENSING_ROOT", "")
    if root_env:
        output_dir = pathlib.Path(root_env) / "vins_output"
    else:
        output_dir = pathlib.Path.home() / ".ros" / "vins_output"

    config_path = _generate_config(original_config, output_dir)

    vins_install = str(sensing_ws / "install" / "vins" / "lib" / "vins" / "vins_node")
    loop_install = str(
        sensing_ws / "install" / "loop_fusion" / "lib" / "loop_fusion" / "loop_fusion_node"
    )

    imu_src = sensing_ws / "src" / "imu_publisher" / "launch"
    camera_src = sensing_ws / "src" / "camera_publisher" / "camera_publisher"

    return LaunchDescription([
        ExecuteProcess(
            cmd=["bash", str(imu_src / "start_mavros.sh")],
            output="screen",
        ),

        ExecuteProcess(
            cmd=["python3", str(imu_src / "imu_bridge.py")],
            output="screen",
        ),

        ExecuteProcess(
            cmd=["python3", str(camera_src / "camera_publisher.py")],
            output="screen",
        ),

        TimerAction(
            period=5.0,
            actions=[
                ExecuteProcess(
                    cmd=[vins_install, config_path],
                    output="screen",
                ),
            ],
        ),

        TimerAction(
            period=5.0,
            actions=[
                ExecuteProcess(
                    cmd=[loop_install, config_path],
                    output="screen",
                ),
            ],
        ),
    ])
