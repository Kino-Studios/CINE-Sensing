"""Backwards-compatible shim for the legacy `configs.python.constants` path.

The single source of truth for runtime configuration is the JSON data in
`configs/json/`, loaded by `configs/python/__init__.py`. This module previously
hardcoded the same values, which duplicated the JSON. It now re-exports the
JSON-backed classes so existing `from configs.python.constants import ...`
callers keep working without a second copy of the values.

Prefer importing from the package directly: `from configs.python import ...`.
"""

from configs.python import (
    ModelDetectionConstants,
    RuleOfThirdsConstants,
    UserRequestedParameters,
)

__all__ = [
    "ModelDetectionConstants",
    "RuleOfThirdsConstants",
    "UserRequestedParameters",
]
