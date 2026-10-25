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

## Style

Python style is ruff (line length 100, single quotes) plus `python3 tools/format.py`, which
adds the repository's whitespace convention. Parameters live in
`cine_sensing_config/config/`; do not hard-code paths or constants in node source files.

## Third-party code

Code under `third_party/` keeps its upstream style and is excluded from the hooks; record
any change to it in `third_party/vins_fusion/UPSTREAM.md`.
