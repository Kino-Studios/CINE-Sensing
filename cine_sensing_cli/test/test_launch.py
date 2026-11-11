import json
import subprocess
from dataclasses import replace

from cine_sensing_cli.common import SubprocessRunner

SOURCING_MESSAGE = (
    'ros2 not found: source /opt/ros/jazzy/setup.bash and <workspace>/install/setup.bash first'
)


def test_launch_vio_dry_run_prints_the_launch_command(invoke, runner):
    result = invoke('launch', 'vio', '--profile', 'rpi_v3_wide', '--dry-run')

    assert result.exit_code == 0
    assert result.stdout == 'ros2 launch vins complete_vio.launch.py profile:=rpi_v3_wide\n'
    assert runner.commands == []


def test_launch_camera_runs_from_the_repository_root(invoke, runner, repository_root):
    invoke('launch', 'camera')

    assert runner.commands == [
        (['ros2', 'launch', 'cine_sensing_camera', 'camera.launch.py'], repository_root)
    ]


def test_launch_imu_starts_the_bridge(invoke, runner):
    invoke('launch', 'imu')

    assert runner.commands[0][0] == ['ros2', 'launch', 'cine_sensing_imu', 'imu_bridge.launch.py']


def test_launch_mavros_runs_the_start_script(invoke, runner):
    invoke('launch', 'mavros')

    assert runner.commands[0][0] == ['bash', 'cine_sensing_imu/launch/start_mavros.sh']


def test_launch_without_ros2_exits_3_with_the_sourcing_message(invoke, runner, environment):
    without_ros2 = replace(environment, which=lambda name: None)

    result = invoke('launch', 'camera', environment=without_ros2)

    assert result.exit_code == 3
    assert SOURCING_MESSAGE in result.stderr
    assert runner.commands == []


def test_launch_vio_with_unknown_profile_exits_2_and_lists_profiles(invoke, runner):
    result = invoke('launch', 'vio', '--profile', 'nope')

    assert result.exit_code == 2
    assert 'rpi_v3_wide' in result.output
    assert runner.commands == []


def test_failed_launch_with_json_reports_the_exit_code(invoke, runner):
    runner.exit_code = 4

    result = invoke('launch', 'camera', '--json')

    assert result.exit_code == 4
    assert json.loads(result.stdout) == {
        'command': ['ros2', 'launch', 'cine_sensing_camera', 'camera.launch.py'],
        'exit_code': 4,
    }


def test_interrupted_launch_exits_130_without_traceback(invoke, runner):
    runner.exit_code = 130

    result = invoke('launch', 'camera')

    assert result.exit_code == 130
    assert 'Traceback' not in result.output


def test_missing_repository_root_exits_3(invoke, runner, environment):
    without_root = replace(environment, repository_root=None)

    result = invoke('launch', 'camera', environment=without_root)

    assert result.exit_code == 3
    assert 'pipx install --editable' in result.stderr
    assert runner.commands == []


def test_json_launch_sends_child_stdout_to_stderr(invoke, runner):
    invoke('launch', 'camera', '--json')

    assert runner.stdout_redirections == [True]


def test_plain_launch_keeps_child_stdout_on_stdout(invoke, runner):
    invoke('launch', 'camera')

    assert runner.stdout_redirections == [False]


class InterruptedOncePopen:
    instances = []

    def __init__(self, command, cwd, stdout=None):
        self.wait_calls = 0
        self.killed = False
        InterruptedOncePopen.instances.append(self)

    def wait(self):
        self.wait_calls += 1
        if self.wait_calls == 1:
            raise KeyboardInterrupt

        return -2

    def kill(self):
        self.killed = True


class InterruptedTwicePopen(InterruptedOncePopen):
    def wait(self):
        self.wait_calls += 1
        if self.wait_calls <= 2:
            raise KeyboardInterrupt

        return -9


class InterruptedOnceThenCleanExitPopen(InterruptedOncePopen):
    def wait(self):
        self.wait_calls += 1
        if self.wait_calls == 1:
            raise KeyboardInterrupt

        return 0


def test_interrupted_run_waits_for_the_child_then_returns_130(monkeypatch, tmp_path):
    InterruptedOncePopen.instances = []
    monkeypatch.setattr(subprocess, 'Popen', InterruptedOncePopen)

    exit_code = SubprocessRunner().run(['ros2', 'launch'], tmp_path)

    child = InterruptedOncePopen.instances[0]
    assert (exit_code, child.wait_calls, child.killed) == (130, 2, False)


def test_second_interrupt_kills_the_child_and_returns_130(monkeypatch, tmp_path):
    InterruptedOncePopen.instances = []
    monkeypatch.setattr(subprocess, 'Popen', InterruptedTwicePopen)

    exit_code = SubprocessRunner().run(['ros2', 'launch'], tmp_path)

    child = InterruptedOncePopen.instances[0]
    assert (exit_code, child.killed) == (130, True)


def test_interrupted_normal_stop_returns_the_childs_exit_code(monkeypatch, tmp_path):
    InterruptedOncePopen.instances = []
    monkeypatch.setattr(subprocess, 'Popen', InterruptedOnceThenCleanExitPopen)

    exit_code = SubprocessRunner().run(['ros2', 'bag'], tmp_path, interrupt_is_normal_stop=True)

    assert exit_code == 0


def test_second_interrupt_during_normal_stop_returns_130(monkeypatch, tmp_path):
    InterruptedOncePopen.instances = []
    monkeypatch.setattr(subprocess, 'Popen', InterruptedTwicePopen)

    exit_code = SubprocessRunner().run(['ros2', 'bag'], tmp_path, interrupt_is_normal_stop=True)

    child = InterruptedOncePopen.instances[0]
    assert (exit_code, child.killed) == (130, True)


def test_capture_runs_the_child_unbuffered_so_a_timeout_keeps_its_output(monkeypatch, tmp_path):
    recorded = {}

    def fake_run(command, **keywords):
        recorded.update(keywords)

        return subprocess.CompletedProcess(command, 0, stdout='')

    monkeypatch.setattr(subprocess, 'run', fake_run)

    SubprocessRunner().capture(['ros2', 'topic', 'hz', '/odometry'], tmp_path, 5)

    assert recorded['env']['PYTHONUNBUFFERED'] == '1'
