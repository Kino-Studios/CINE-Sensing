# CINE-Sensing — Agent Instructions

## Formatting (run after every iteration)

After any change to Python files, run the repository formatter before considering the
work done:

```bash
python3 tools/format.py            # formats all tracked python in the repo
# or target specific files:
python3 tools/format.py path/to/changed_file.py
```

`tools/format.py` enforces the approved whitespace convention that ruff cannot:
a blank line before every `return`/`raise` that is not first in its block, no blank
line directly after a `def`/`class` header, and single blank lines inside bodies. It
also runs `ruff` (quotes, commas, line length, imports) when ruff is on PATH. The pass
is idempotent and behavior-preserving.

The remaining convention rules are review-time judgment, not automated:

- **Sparse comments** — remove banner/"what" comments; keep non-obvious "why" comments.
- **Descriptive names** — no one-letter locals (`e`→`exc`, `f`→`file_handle`); never
  rename public API, ROS topics, params, dict keys, or `self.` attributes.

Verify every touched file still compiles (`python3 -m py_compile <file>`) and that
`third_party/vins_fusion/vins/tests/unit` passes.

## Checks (what CI runs)

Run from the repository root:

```bash
pytest                              # config loader, profiles, tools, VINS unit tests
python3 tools/format.py --check     # exits 1 and writes nothing if a file would change
ruff check .
pre-commit run --all-files          # the above plus whitespace/YAML/codespell hooks
```

`pyproject.toml` sets the pytest import paths, so bare `pytest` works as is; tests
never edit the import path themselves.

## Layout and configuration

- `cine_sensing_config/config/*.json` is the single source of truth for parameters.
  A profile in `cine_sensing_config/config/profiles/<name>/` overrides whole files;
  choose it with `CINE_SENSING_PROFILE=<name>` or `profile:=<name>` on the VIO launches.
- The VINS YAML is generated at launch by
  `third_party/vins_fusion/vins/launch/generate_vins_config.py`; never edit it by hand.
- Data files kept out of git: `python3 tools/download_assets.py`.
- Ceres 2.1 (VINS-Fusion needs it; Ubuntu 24.04 ships 2.2): `tools/install_ceres_2_1.sh`.
- Changes under `third_party/vins_fusion/` are recorded in its `UPSTREAM.md`.
