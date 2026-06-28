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
`sensing_ws/src/VINS-Fusion-ROS2-humble-arm/vins/tests/unit` passes.
