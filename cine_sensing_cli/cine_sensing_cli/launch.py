import typer

from cine_sensing_cli.common import (
    DryRunFlag,
    JsonFlag,
    execute,
    get_environment,
    require_root,
    require_ros2,
    validate_profile,
)

app = typer.Typer(no_args_is_help=True, help='Start a CINE-Sensing subsystem in the foreground.')


def _launch(
    context: typer.Context, command: list[str], dry_run: bool, as_json: bool, profile: str = ''
) -> None:
    environment = get_environment(context)
    root = require_root(environment)
    validate_profile(root, profile)
    if not dry_run:
        require_ros2(environment)
    execute(environment, command, dry_run, as_json)


@app.command()
def camera(context: typer.Context, dry_run: DryRunFlag = False, as_json: JsonFlag = False) -> None:
    """Start the camera node."""
    _launch(
        context, ['ros2', 'launch', 'cine_sensing_camera', 'camera.launch.py'], dry_run, as_json
    )


@app.command()
def imu(context: typer.Context, dry_run: DryRunFlag = False, as_json: JsonFlag = False) -> None:
    """Start the IMU bridge."""
    _launch(
        context, ['ros2', 'launch', 'cine_sensing_imu', 'imu_bridge.launch.py'], dry_run, as_json
    )


@app.command()
def mavros(context: typer.Context, dry_run: DryRunFlag = False, as_json: JsonFlag = False) -> None:
    """Start MAVROS through the repository script."""
    _launch(context, ['bash', 'cine_sensing_imu/launch/start_mavros.sh'], dry_run, as_json)


@app.command()
def vio(
    context: typer.Context,
    profile: str = typer.Option(
        '', help='Config profile under cine_sensing_config/config/profiles.'
    ),
    dry_run: DryRunFlag = False,
    as_json: JsonFlag = False,
) -> None:
    """Start the VINS visual-inertial odometry."""
    command = ['ros2', 'launch', 'vins', 'complete_vio.launch.py']
    if profile:
        command.append(f'profile:={profile}')
    _launch(context, command, dry_run, as_json, profile)
