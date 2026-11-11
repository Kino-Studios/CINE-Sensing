import json
import textwrap
from pathlib import Path

import typer

from cine_sensing_cli.common import JsonFlag, get_environment, require_root, validate_profile

app = typer.Typer(no_args_is_help=True, help='Inspect the cine_sensing_config parameter files.')


def _config_directory(root: Path) -> Path:
    return root / 'cine_sensing_config' / 'config'


def _read_json_files(directory: Path) -> dict[str, dict]:
    return {path.stem: json.loads(path.read_text()) for path in sorted(directory.glob('*.json'))}


def resolved_config(root: Path, profile: str) -> dict[str, dict]:
    """Base config files, each replaced whole by the profile's file of the same name."""
    config_directory = _config_directory(root)
    config = _read_json_files(config_directory)
    if profile:
        config.update(_read_json_files(config_directory / 'profiles' / profile))

    return dict(sorted(config.items()))


@app.command()
def profiles(context: typer.Context, as_json: JsonFlag = False) -> None:
    """List the available config profiles."""
    root = require_root(get_environment(context))
    profiles_directory = _config_directory(root) / 'profiles'
    names = sorted(path.name for path in profiles_directory.iterdir() if path.is_dir())
    if as_json:
        typer.echo(json.dumps({'profiles': names}))
    else:
        for name in names:
            typer.echo(name)


@app.command()
def show(
    context: typer.Context,
    profile: str = typer.Option(
        '', help='Profile to resolve; defaults to $CINE_SENSING_PROFILE, else the base config.'
    ),
    as_json: JsonFlag = False,
) -> None:
    """Print the config files as the nodes would load them."""
    environment = get_environment(context)
    root = require_root(environment)
    profile = validate_profile(
        root, profile or environment.variables.get('CINE_SENSING_PROFILE', '')
    )
    config = resolved_config(root, profile)
    if as_json:
        typer.echo(json.dumps({'profile': profile, 'config': config}))

        return
    for name, content in config.items():
        typer.echo(name)
        typer.echo(textwrap.indent(json.dumps(content, indent=2), '  '))
