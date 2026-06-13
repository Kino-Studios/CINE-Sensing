# CINE-Sensing Configuration

This directory holds the project's configuration. There is **one source of
truth** for shared parameter data, plus deliberately-separate hardware layers.
Read this before adding a config value so it lands in the right place.

## Source of truth: `configs/json/`

All shared parameter data lives here as plain JSON. Edit values **here only**.

| File               | Holds                                                    | Top-level key                                                                 |
| ------------------ | -------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `user_params.json` | Detection constants, user request params, rule-of-thirds | `ModelDetectionConstants`, `UserRequestedParameters`, `RuleOfThirdsConstants` |
| `camera.json`      | Camera publisher parameters                              | `camera_publisher.ros__parameters`                                            |
| `gyroscope.json`   | Gyroscope data publisher serial parameters               | `gyroscope_data_publisher.ros__parameters`                                    |
| `vins.json`        | VINS-Fusion VIO configuration                            | `vins_config`                                                                 |

`MODEL_PATH` in `user_params.json` is stored **relative to the repo root**.
Runtime code resolves it to an absolute path via the `CINE_SENSING_ROOT`
environment variable, or by walking up to the repo root if that is unset. Do
not hardcode absolute paths in the JSON.

## Python loader: `configs/python/`

- `__init__.py` — the loader. Reads the JSON files above and exposes them as
  typed classes (`ModelDetectionConstants`, `CameraConfig`, `GyroscopeConfig`,
  `VinsConfig`, `RuleOfThirdsConstants`, `UserRequestedParameters`). It also
  resolves `MODEL_PATH` to an absolute path. **Import from here:**
  `from configs.python import CameraConfig`.
- `constants.py` — a thin backwards-compatibility shim that re-exports a subset
  of the loader classes for the legacy `from configs.python.constants import ...`
  call site. It no longer holds any values of its own. Prefer importing from
  `configs.python` directly; this shim may be removed once the last caller
  migrates.

The loader does **not** duplicate values. It only reads the JSON.

## Hardware layers (intentionally separate, not duplicates)

- `configs/gyroscope/comms.yaml` — gyroscope serial-link YAML consumed directly
  by the `imu_publisher` gyroscope launch path (resolved at launch time via
  `CINE_SENSING_ROOT` / repo-root walk). This is a distinct hardware-comms file
  and is **not** the same as the MAVROS `comms.yaml` that lives inside
  `imu_publisher/config/`. Kept separate on purpose: it is a device wiring
  concern, not shared application data.

## C++ headers: `configs/cpp/`

`config_loader.hpp` plus the `*_config.hpp` accessors are a C++ convenience
surface whose own docstrings declare the JSON files as the single source of
truth. They provide compile-time _default_ mirrors only and are intended to be
backed by `config_loader.hpp` reading the JSON at runtime.

> **Status note:** these headers currently have no compiling consumer in the
> tree (no `.cpp` includes them, no `CMakeLists.txt` references them). Some of
> their hardcoded defaults have drifted from the JSON (see "Known value drift"
> below) and should be reconciled or the headers removed when a C++ consumer is
> introduced. They were left in place rather than silently retuned.

## Known value drift (do not silently reconcile)

These differences exist between the orphan C++ defaults and the JSON source of
truth. They are recorded here rather than changed, because changing them is a
parameter decision, not a structural move:

- `camera.json` uses `image_width=1152`, `image_height=648`; the
  `CameraDefaults` in `configs/cpp/camera_config.hpp` use `1920`/`1080`.
- `ModelDetectionDefaults::MODEL_PATH` in `configs/cpp/user_params_config.hpp`
  is a stale absolute path under `/home/fishnos/...`; the JSON source uses a
  repo-relative path resolved at runtime.

Resolve these with whoever owns the camera intrinsics / deployment paths before
wiring up a C++ consumer.
