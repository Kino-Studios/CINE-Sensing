import json
from dataclasses import replace

from cine_sensing_cli.common import ROS2_MISSING_MESSAGE, CapturedOutput
from cine_sensing_cli.doctor import parse_average_rate

HEALTHY_RATE = CapturedOutput(returncode=124, stdout='average rate: 29.987\n\tmin: 0.033s\n')
RATE_TOPICS = [
    '/mavros/imu/data_raw',
    '/imu_bridge/data_raw',
    '/camera/image_raw',
    '/imu_propagate',
    '/odometry',
]


def healthy_captures() -> dict[tuple[str, ...], CapturedOutput]:
    captures = {
        ('ros2', 'topic', 'echo', '/mavros/state'): CapturedOutput(returncode=0, stdout='True\n')
    }
    for topic in RATE_TOPICS:
        captures[('ros2', 'topic', 'hz', topic)] = HEALTHY_RATE

    return captures


def test_parse_average_rate_reads_the_last_reading():
    text = 'average rate: 10.000\n\tmin: 0.1s\naverage rate: 29.987\n\tmin: 0.03s\n'

    assert parse_average_rate(text) == 29.987


def test_parse_average_rate_without_messages_is_none():
    assert parse_average_rate('') is None


def test_doctor_all_healthy_exits_0(invoke, runner):
    runner.captures.update(healthy_captures())

    result = invoke('doctor', '--json')

    checks = json.loads(result.stdout)['checks']
    assert result.exit_code == 0
    assert len(checks) == 8
    assert all(check['passed'] for check in checks)


def test_doctor_silent_camera_fails_only_that_check(invoke, runner):
    runner.captures.update(healthy_captures())
    runner.captures[('ros2', 'topic', 'hz', '/camera/image_raw')] = CapturedOutput(
        returncode=124, stdout=''
    )

    result = invoke('doctor', '--json')

    checks = {check['name']: check for check in json.loads(result.stdout)['checks']}
    assert result.exit_code == 1
    assert checks['/camera/image_raw rate']['passed'] is False
    assert checks['/camera/image_raw rate']['detail'] == 'no messages'
    assert checks['/odometry rate']['passed'] is True
    assert checks['MAVROS connected']['passed'] is True


def test_doctor_prints_one_line_per_check_in_human_form(invoke, runner):
    runner.captures.update(healthy_captures())

    result = invoke('doctor')

    assert 'PASS  /camera/image_raw rate  29.99 Hz' in result.stdout.splitlines()


def test_doctor_without_ros2_exits_3_and_reports_one_check(invoke, environment):
    without_ros2 = type(environment)(
        repository_root=environment.repository_root,
        runner=environment.runner,
        which=lambda name: None,
        variables={},
    )

    result = invoke('doctor', '--json', environment=without_ros2)

    checks = json.loads(result.stdout)['checks']
    assert result.exit_code == 3
    assert [check['name'] for check in checks] == ['ros2']
    assert checks[0]['passed'] is False
    assert checks[0]['detail'] == ROS2_MISSING_MESSAGE


def test_doctor_accepts_lowercase_true_from_mavros(invoke, runner):
    runner.captures.update(healthy_captures())
    runner.captures[('ros2', 'topic', 'echo', '/mavros/state')] = CapturedOutput(
        returncode=0, stdout='true\n'
    )

    result = invoke('doctor', '--json')

    checks = {check['name']: check for check in json.loads(result.stdout)['checks']}
    assert checks['MAVROS connected']['passed'] is True


def test_doctor_fails_mavros_when_the_state_is_false(invoke, runner):
    runner.captures.update(healthy_captures())
    runner.captures[('ros2', 'topic', 'echo', '/mavros/state')] = CapturedOutput(
        returncode=0, stdout='false\n'
    )

    result = invoke('doctor', '--json')

    checks = {check['name']: check for check in json.loads(result.stdout)['checks']}
    assert result.exit_code == 1
    assert checks['MAVROS connected']['passed'] is False


def test_doctor_runs_without_a_repository_root(invoke, runner, environment):
    runner.captures.update(healthy_captures())
    without_root = replace(environment, repository_root=None)

    result = invoke('doctor', '--json', environment=without_root)

    assert result.exit_code == 0
    assert len(json.loads(result.stdout)['checks']) == 8


def test_doctor_reports_unset_domain_id_as_zero(invoke, runner):
    runner.captures.update(healthy_captures())

    result = invoke('doctor', '--json')

    checks = {check['name']: check for check in json.loads(result.stdout)['checks']}
    assert checks['ROS_DOMAIN_ID']['detail'] == 'unset (0)'


def test_doctor_reports_the_domain_id_when_set(invoke, runner, environment):
    runner.captures.update(healthy_captures())
    with_domain = replace(environment, variables={'ROS_DOMAIN_ID': '42'})

    result = invoke('doctor', '--json', environment=with_domain)

    checks = {check['name']: check for check in json.loads(result.stdout)['checks']}
    assert checks['ROS_DOMAIN_ID']['detail'] == '42'
