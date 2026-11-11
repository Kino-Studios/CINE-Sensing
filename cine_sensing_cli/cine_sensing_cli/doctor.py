import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import typer

from cine_sensing_cli.common import (
    ROS2_MISSING_MESSAGE,
    ExitCode,
    JsonFlag,
    get_environment,
)

MAVROS_TIMEOUT_SECONDS = 3
RATE_TIMEOUT_SECONDS = 5
RATE_TOPICS = (
    '/mavros/imu/data_raw',
    '/imu_bridge/data_raw',
    '/camera/image_raw',
    '/imu_propagate',
    '/odometry',
)
AVERAGE_RATE_PATTERN = re.compile(r'average rate:\s*([0-9]+(?:\.[0-9]+)?)')


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def parse_average_rate(text: str) -> float | None:
    readings = AVERAGE_RATE_PATTERN.findall(text)
    if not readings:
        return None

    return float(readings[-1])


def _format_check(check: Check) -> str:
    status = 'PASS' if check.passed else 'FAIL'

    return f'{status}  {check.name}  {check.detail}'


def doctor(context: typer.Context, as_json: JsonFlag = False) -> None:
    """Check that the ROS 2 data paths the VIO pipeline needs are alive."""
    environment = get_environment(context)
    ros2_path = environment.which('ros2')
    working_directory = Path.cwd()
    checks: list[Check] = []
    if ros2_path is None:
        checks.append(Check('ros2', False, ROS2_MISSING_MESSAGE))
        exit_code = ExitCode.ENVIRONMENT
    else:
        checks.append(Check('ros2', True, ros2_path))
        domain_id = environment.variables.get('ROS_DOMAIN_ID')
        checks.append(Check('ROS_DOMAIN_ID', True, domain_id or 'unset (0)'))
        state = environment.runner.capture(
            ['ros2', 'topic', 'echo', '/mavros/state', '--once', '--field', 'connected'],
            working_directory,
            MAVROS_TIMEOUT_SECONDS,
        )
        connected = 'true' in state.stdout.lower()
        checks.append(
            Check('MAVROS connected', connected, 'connected' if connected else 'not connected')
        )
        for topic in RATE_TOPICS:
            captured = environment.runner.capture(
                ['ros2', 'topic', 'hz', topic, '--window', '10'],
                working_directory,
                RATE_TIMEOUT_SECONDS,
            )
            rate = parse_average_rate(captured.stdout)
            detail = 'no messages' if rate is None else f'{rate:.2f} Hz'
            checks.append(Check(f'{topic} rate', rate is not None, detail))
        exit_code = ExitCode.OK if all(check.passed for check in checks) else ExitCode.FAILED
    if as_json:
        typer.echo(json.dumps({'checks': [asdict(check) for check in checks]}))
    else:
        for check in checks:
            typer.echo(_format_check(check))

    raise typer.Exit(exit_code)
