# Contributing to CINE-Sensing

Questions and bug reports go in
[GitHub issues](https://github.com/Kino-Studios/CINE-Sensing/issues). Pull requests are
welcome too, and contributions are accepted under GPL-3.0-only, the licence of this
repository.

## Checks

Run these before opening a pull request; CI runs the pre-commit hooks, `pytest`, and a
colcon build and test of the ROS packages.

```bash
pip install pre-commit && pre-commit install   # ruff, whitespace convention, hygiene hooks
pytest                                          # pure-Python tests, no ROS needed
cd ~/cine_ws && colcon build && colcon test && colcon test-result --verbose
```

## Command-line tool

The `cine-sensing` command (package `cine_sensing_cli`) runs the launch, VIO, config,
contract, assets and doctor steps on the drone's Raspberry Pi. Install it from the
repository root with pipx, not plain `pip`, because Ubuntu 24.04 refuses `pip` into the
system Python (`sudo apt install pipx` if pipx is missing):

```bash
pipx install --editable ./cine_sensing_cli
pipx inject cine-sensing-cli ../CINE-Interfaces/cine_interfaces   # needed by `contract check`
cine-sensing --help                                               # lists every command
```

The editable install means `git pull` updates the tool without reinstalling it. The
`inject` line adds the CINE-Interfaces package to the same environment, so `contract check`
can import it.

## Topics shared with CINE

Topics that cross the Wi-Fi link to the ground PC are listed in the contract in
[CINE-Interfaces](https://github.com/Kino-Studios/CINE-Interfaces), and
`tools/test_interface_contract.py` fails when this repository drifts from it. Install
the checker next to this checkout before running `pytest`:

```bash
git clone https://github.com/Kino-Studios/CINE-Interfaces ../CINE-Interfaces
pip install -e ../CINE-Interfaces/cine_interfaces
```

To rename or retype one of those topics, edit `contract.json` in CINE-Interfaces first,
then change the code here and in CINE, and move the commit pinned in `interfaces.repos`
and `.github/workflows/ci.yml` forward.

## Style

Python style is ruff (line length 100, single quotes) plus `python3 tools/format.py`, which
adds the repository's whitespace convention. Parameters live in
`cine_sensing_config/config/`; do not hard-code paths or constants in node source files.

## Third-party code

Code under `third_party/` keeps its upstream style and is excluded from the hooks; record
any change to it in `third_party/vins_fusion/UPSTREAM.md`.
