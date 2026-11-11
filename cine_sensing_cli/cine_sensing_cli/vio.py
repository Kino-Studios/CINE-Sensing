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

CANONICAL_BAG = 'datasets/vio_bags/canonical'

app = typer.Typer(
    no_args_is_help=True, help='Record VIO test bags and compare VIO configs on them.'
)


def _run_script(
    context: typer.Context,
    command: list[str],
    dry_run: bool,
    as_json: bool,
    profile: str = '',
    interrupt_is_normal_stop: bool = False,
) -> None:
    environment = get_environment(context)
    root = require_root(environment)
    validate_profile(root, profile)
    if not dry_run:
        require_ros2(environment)
    execute(environment, command, dry_run, as_json, interrupt_is_normal_stop)


@app.command()
def record(
    context: typer.Context,
    out: str = typer.Option(CANONICAL_BAG, help='Directory to record the bag into.'),
    dry_run: DryRunFlag = False,
    as_json: JsonFlag = False,
) -> None:
    """Record a VIO test bag with the sensor stack running."""
    command = ['bash', 'tools/vio_record_bag.sh', out]
    _run_script(context, command, dry_run, as_json, interrupt_is_normal_stop=True)


@app.command()
def compare(
    context: typer.Context,
    label: str,
    bag: str = typer.Option(CANONICAL_BAG, help='Bag to replay through VINS.'),
    duration: int = typer.Option(30, help='Seconds of static drift to measure.'),
    profile: str = typer.Option('', help='Config profile to test under cine_sensing_config.'),
    dry_run: DryRunFlag = False,
    as_json: JsonFlag = False,
) -> None:
    """Replay a bag through one labeled VINS config and record its drift."""
    command = ['bash', 'tools/vio_ab_run.sh', label, bag, str(duration), profile]
    _run_script(context, command, dry_run, as_json, profile)
