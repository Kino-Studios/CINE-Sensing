import os
import subprocess
from pathlib import Path

START_MAVROS_SCRIPT = Path(__file__).resolve().parents[1] / 'launch' / 'start_mavros.sh'


def run_start_mavros(tmp_path, environment):
    fake_ros2 = tmp_path / 'ros2'
    arguments_file = tmp_path / 'arguments.txt'
    fake_ros2.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > {arguments_file}\n')
    fake_ros2.chmod(0o755)
    process_environment = {
        'PATH': f'{tmp_path}:{os.environ["PATH"]}',
        **environment,
    }

    subprocess.run(['bash', str(START_MAVROS_SCRIPT)], env=process_environment, check=True)

    return arguments_file.read_text().splitlines()


def test_start_mavros_defaults_to_the_pi_serial_port(tmp_path):
    arguments = run_start_mavros(tmp_path, environment={})

    assert 'fcu_url:=serial:///dev/ttyAMA0:921600' in arguments
    assert 'use_sim_time:=false' in arguments


def test_start_mavros_takes_fcu_url_from_the_environment(tmp_path):
    arguments = run_start_mavros(tmp_path, environment={'FCU_URL': 'tcp://127.0.0.1:5760'})

    assert 'fcu_url:=tcp://127.0.0.1:5760' in arguments


def test_start_mavros_takes_the_clock_from_the_environment(tmp_path):
    arguments = run_start_mavros(tmp_path, environment={'USE_SIM_TIME': 'true'})

    assert 'use_sim_time:=true' in arguments


def test_start_mavros_keeps_time_sync_disabled(tmp_path):
    arguments = run_start_mavros(tmp_path, environment={})

    assert 'plugin_denylist:=[time_sync]' in arguments
