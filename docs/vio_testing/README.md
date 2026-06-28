# VIO Testing Workflow

Repeatable, comparable VIO drift testing on the Pi 5. The principle: **record one bag,
replay it for every config.** Live flight is never A/B'd — different motion each run
makes metrics incomparable.

## One-time setup

1. Build: `cd sensing_ws && colcon build --symlink-install && cd ..`
2. Record the canonical bag — see [`RECORDING_PROTOCOL.md`](RECORDING_PROTOCOL.md).

## Run a labeled config

1. Set config values in `configs/json/vins.json` — the ONLY place. The VINS yaml is
   generated from it on every launch and carries a DO-NOT-EDIT banner.
2. `bash tools/vio_ab_run.sh <label>`
3. Read `vins_output/drift_results.csv` — one row per label
   (`label,final_drift_m,drift_rate_cm_s,mean_vel_m_s,max_vel_m_s,verdict`).

## Acceptance (per decision doc)

- Final drift `< 0.2 m` over 30 s = GOOD; `< 0.05 m` = EXCELLENT.
- Mean velocity `< 0.1 m/s` when static.

## Canonical setup (decided 2026-06-26)

- **Launcher:** `ros2 launch .../complete_vio.launch.py` is the one true path. It
  regenerates config from `configs/json/vins.json`. The replay harness
  (`replay_vio.launch.py`) mirrors it exactly. `run_vins.py` and `launch_complete_vio.py`
  use a _different_ config (the committed yaml) and `run_vins.py` also forces the IMU
  transform ON — treat them as non-canonical until reconciled.
- **IMU transform:** `use_transform = False` for the baseline (decision doc's safe
  no-op). The A1 reflection stays available to A/B later, not on by default.
- **Tuning:** NOT decided yet. The committed yaml and the JSON source of truth disagree
  (see below). Pick the winner from bag replay; do not change values blind.

## Open finding — config divergence (A/B candidate #1)

The launchers do not agree on VIO tuning. `configs/json/vins.json` (what the canonical
launcher uses) vs the hand-tuned committed `rpi_v3_mono_config.yaml` (what `run_vins.py`
uses):

| param        | vins.json (canonical) | committed yaml (hand-tuned) |
| ------------ | --------------------- | --------------------------- |
| min_parallax | 10.0                  | 8                           |
| max_cnt      | 150                   | 250                         |
| min_dist     | 30                    | 15                          |
| F_threshold  | 1.0                   | 1.5                         |
| equalize     | 0                     | 1                           |
| estimate_td  | 1 (estimate fresh)    | 0                           |
| td           | 0.0                   | -0.031551662509982356       |

First real use of this harness: record the bag, run `vio_ab_run.sh json_defaults` and
`vio_ab_run.sh hand_tuned` (the latter with the committed values pasted into vins.json),
compare drift, commit the winner to vins.json. Camera intrinsics are NOT in this dispute —
both paths read them from `cam0_wide.yaml` (fx 750.99…), which is consistent.

## Scope note

This harness changes NO filter behavior — no variant (A1/A2/noise/tuning) is adopted.
It produces the numbers that decide those variants. See
[`../2026-06-13-vio-drift-decision.md`](../2026-06-13-vio-drift-decision.md).
