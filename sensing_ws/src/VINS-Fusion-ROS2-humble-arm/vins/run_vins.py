"""ROS 2 node wrapper that launches VINS-Fusion subprocesses.

Resolves all paths at runtime via CINE_SENSING_ROOT env var (preferred) or
by walking up from __file__.  Generates the VINS config next to the original
(targeted text substitution of the two output path lines only) so the VINS
C++ side still resolves cam0_calib relative to the config's own directory.
"""

import os
import pathlib
import re
import signal
import subprocess
import sys

import rclpy
from rclpy.node import Node

# Deterministic name for the generated sibling config (gitignored build artifact,
# overwritten each run — no /tmp accumulation).
_GENERATED_CONFIG_NAME = "rpi_v3_mono_config.generated.yaml"


def _vins_src_root() -> pathlib.Path:
    """Return path to sensing_ws/src/VINS-Fusion-ROS2-humble-arm/.

    Priority:
    1. CINE_SENSING_ROOT env var
    2. Sentinel walk: this file is at .../sensing_ws/src/VINS-.../vins/run_vins.py
       parents[0]=vins  parents[1]=VINS-...  parents[2]=src  parents[3]=sensing_ws
    """
    root_env = os.environ.get("CINE_SENSING_ROOT", "")
    if root_env:
        return (
            pathlib.Path(root_env)
            / "sensing_ws"
            / "src"
            / "VINS-Fusion-ROS2-humble-arm"
        )

    return pathlib.Path(__file__).resolve().parents[1]


def _output_dir() -> pathlib.Path:
    """Return the runtime output directory.

    Priority:
    1. CINE_SENSING_ROOT/vins_output
    2. ~/.ros/vins_output
    """
    root_env = os.environ.get("CINE_SENSING_ROOT", "")
    if root_env:
        return pathlib.Path(root_env) / "vins_output"

    return pathlib.Path.home() / ".ros" / "vins_output"


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


class VINSRunner(Node):
    def __init__(self) -> None:
        super().__init__("vins_runner")
        self.vins_process: subprocess.Popen | None = None
        self.loop_process: subprocess.Popen | None = None
        self.imu_bridge_process: subprocess.Popen | None = None
        self.mavros_process: subprocess.Popen | None = None

        self._start_vins()

    def _start_vins(self) -> None:
        vins_src = _vins_src_root()
        out_dir = _output_dir()

        original_config = (
            vins_src / "config" / "rpi_camera_v3" / "rpi_v3_mono_config.yaml"
        )
        config_path = _generate_config(original_config, out_dir)
        self.get_logger().info(f"Using generated VINS config: {config_path}")
        self.get_logger().info(f"VINS output dir: {out_dir}")

        vins_cmd = ["ros2", "run", "vins", "vins_node", config_path]
        mavros_cmd = ["ros2", "launch", "mavros", "px4.launch.py"]
        imu_bridge_cmd = ["imu_bridge", "--ros-args", "-p", "use_transform:=true"]
        loop_cmd = ["ros2", "run", "loop_fusion", "loop_fusion_node", config_path]

        env = os.environ.copy()
        env["ROS_DOMAIN_ID"] = "0"

        try:
            self.vins_process = subprocess.Popen(vins_cmd, env=env)
            self.mavros_process = subprocess.Popen(mavros_cmd, env=env)
            self.imu_bridge_process = subprocess.Popen(imu_bridge_cmd, env=env)
            self.loop_process = subprocess.Popen(loop_cmd, env=env)
            self.get_logger().info("VINS-Fusion started")
        except Exception as exc:
            self.get_logger().error(f"Failed to start VINS: {exc}")

    def shutdown(self) -> None:
        for proc in (self.vins_process, self.imu_bridge_process, self.loop_process):
            if proc is not None:
                proc.terminate()


def main(args: list | None = None) -> None:
    rclpy.init(args=args)
    runner = VINSRunner()

    def _signal_handler(sig: int, frame: object) -> None:
        runner.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)

    try:
        rclpy.spin(runner)
    except KeyboardInterrupt:
        pass
    finally:
        runner.shutdown()
        runner.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
