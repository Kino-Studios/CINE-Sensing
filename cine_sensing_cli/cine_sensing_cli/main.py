import typer

from cine_sensing_cli import assets, config, contract, doctor, launch, vio
from cine_sensing_cli.common import default_environment

app = typer.Typer(no_args_is_help=True, help='Run the CINE-Sensing launch files and tools.')
app.add_typer(assets.app, name='assets')
app.add_typer(config.app, name='config')
app.add_typer(contract.app, name='contract')
app.command('doctor')(doctor.doctor)
app.add_typer(launch.app, name='launch')
app.add_typer(vio.app, name='vio')


@app.callback()
def main(context: typer.Context) -> None:
    if context.obj is None:
        context.obj = default_environment()
