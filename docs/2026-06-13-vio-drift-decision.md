# VIO / IMU Drift — Decision Document

**Date:** 2026-06-13
**Status:** OPEN — requires on-hardware validation before any change below is adopted
**Scope:** Consolidates the ~11 drift-related branches from the S1 triage into one
actionable plan for when the operator is physically at the drone.

> ⚠️ **FLIGHT-BEHAVIOR WARNING**
> Every change cataloged here alters what the VIO stack actually computes (IMU
> axis frame, filter noise model, or which node publishes odometry). NONE of them
> can be validated without hardware, a running ROS 2 stack, and either live flight
> or a recorded bag. **Do not merge any of these to `main` based on code review
> alone.** Pick one variant per change-type, flash it, run the static drift test
> (below), compare numbers, and only then adopt. The S5 refactor already on `main`
> changed _representation only_ — it is numerically identical to the prior code
> and is NOT one of the decisions in this document.

---

## 1. The three orthogonal change-types

The drift branches cluster into three independent axes. They can in principle be
combined (one choice from each), EXCEPT for the conflict noted in §2.

### (A) IMU axis remap in `imu_bridge.py`

The bridge optionally remaps the raw MAVROS IMU (`/mavros/imu/data_raw`) into the
frame VINS-Fusion expects, then republishes to `/imu_bridge/data_raw`. Two
_different and mutually exclusive_ remaps exist across branches, plus disagreement
over whether the remap is gated by a `use_transform` parameter or always on.

Notation: each line is `output_axis <- input expression`.

#### Variant A1 — "swap X/Y, flip Z" (CURRENT on `main`)

```
accel.x <- +in.y      gyro.x <- +in.y
accel.y <- +in.x      gyro.y <- +in.x
accel.z <- -in.z      gyro.z <- -in.z
```

Matrix `R = [[0,1,0],[1,0,0],[0,0,-1]]`. This is a reflection (swap two axes + flip
the third). Present on: `main`, `fix-vio-imu-transform-…`, `fix-vio-imu-config-…`,
`fix/gyroscopic-misalignment-and-drift-…`. Gated behind `use_transform` (default
`False`) in the package source.

#### Variant A2 — "keep X, flip Y, flip Z" (180° about X)

```
accel.x <- +in.x      gyro.x <- +in.x
accel.y <- -in.y      gyro.y <- -in.y
accel.z <- -in.z      gyro.z <- -in.z
```

Matrix `R = [[1,0,0],[0,-1,0],[0,0,-1]]`. This is a proper 180° rotation about X
(the classic FLU↔FRD / ENU↔NED body flip). Present on:
`fix-gyroscopic-misalignment-vio-drift-…`, `fix/imu-drift-and-misconfiguration-…`.

> A1 and A2 are **mutually exclusive** — they are different physical claims about
> how the sensor is mounted relative to the camera. At most one is correct. A1 is a
> handedness-flipping reflection (determinant −1); A2 is a real rotation
> (determinant +1). A reflection in an IMU chain is a red flag — if the true
> mounting is a rotation, A1 will _look_ plausible statically but corrupt
> cross-axis coupling under motion. **This is the single most important thing to
> verify on hardware.**

#### Variant A3 — gating / parsing only (no math change)

`fix-vio-imu-transform-…` and `fix-vio-imu-config-…` add a `use_transform` launch
argument and plumb it through; `fix/gyroscopic-misalignment-and-drift-…`
additionally hardens `use_transform` parameter parsing to accept string `"true"`;
`fix-gyroscopic-vio-misalignment-…` hardcodes `use_transform=True` in the launch
file. These change _whether/when_ a remap runs, not the remap itself.

### (B) VINS IMU random-walk noise (`rpi_v3_mono_config.yaml`)

```
acc_w: 0.00002  ->  0.0001     (5x increase)
gyr_w: 0.00002  ->  0.0001     (5x increase)
```

(`acc_n: 0.1`, `gyr_n: 0.01` are NOT touched by any branch.) Raising the bias
random-walk loosens the filter's trust in IMU bias stability — a common mitigation
for static drift / bias estimation problems. Present on 6 branches:
`fix-gyroscopic-misalignment-vio-drift-…`, `fix-gyroscopic-vio-misalignment-…`,
`fix-imu-vio-drift-config-…`, `fix/imu-drift-and-misconfiguration-…`,
`fix/vio-drift-and-paths-…`, `vio-drift-improvement`. The `main` value remains
`0.00002`.

> This is a **retune of a Kalman-filter noise parameter**. It cannot be chosen
> correctly by inspection — the right value depends on the actual Allan-variance of
> _this_ IMU. Treat `0.0001` as a hypothesis to A/B test, not a fix.

### (C) `vio_publisher` consolidation

Several branches refactor/consolidate the odometry-publishing path
(`vio_publisher.py`) and the launch wiring (renames `fc_data` ↔ `imu_publisher`,
merging the standalone `imu_bridge` node back into the combined launch file).
`vio-drift-improvement` is the largest and also rewrites the analysis/diagnostic
scripts. This is plumbing/structure, largely independent of (A) and (B), but it
determines _which_ node and frame the static drift test subscribes to, so land it
first if adopted so the test harness is stable.

---

## 2. Mutual-exclusion / conflict matrix

| Pair                                  | Compatible? | Why                                                                                                                                                                                                                                         |
| ------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A1 vs A2 (remap math)                 | ❌ NO       | Different physical mounting claims; one reflection, one rotation. Pick exactly one.                                                                                                                                                         |
| A-remap vs A3 `use_transform` parsing | ⚠️ Coupled  | The parsing/gating branches assume a _specific_ remap is the thing being toggled. You cannot land two remap-math variants behind one `use_transform` flag — the flag has no way to select A1 vs A2. Decide the math FIRST, then the gating. |
| A (any) vs B (noise)                  | ✅ Yes      | Orthogonal: frame vs filter noise. Can combine.                                                                                                                                                                                             |
| A/B vs C (consolidation)              | ✅ Yes      | Structural. Land C first for a stable test harness.                                                                                                                                                                                         |
| B value `0.0001` vs `0.00002`         | ❌ NO       | Same key, two values. One config wins.                                                                                                                                                                                                      |

Net: a final config is **(one of A1/A2) + (one of the two noise sets) + (C or not)**.
The dangerous illusion is thinking A1 and A2 can coexist behind `use_transform` —
they cannot.

---

## 3. Recommended validation procedure

Tool: `third_party/vins_fusion/vins/tests/static_drift_test.py`
(already in repo). It subscribes to `/odometry`, requires the sensor held
**completely still for 30 s**, and reports:

- **Final drift** (m) and **Max drift** (m) from start position
- **Drift rate** (cm/s)
- **Mean / Max velocity** (m/s) — should be ~0 when static
- A diagnosis bucket (`<0.05 m` excellent … `>2 m` fail)

### Procedure

1. **Establish the baseline (main, unchanged).** Build, run the full VIO stack,
   place the rig on a rigid static surface, run:
   ```
   ros2 run <pkg> static_drift_test        # or: python3 .../static_drift_test.py
   ```
   Record Final drift, Drift rate, Mean velocity. This is your control number.
2. **Test change-types one at a time** (never bundle — you cannot attribute the
   result otherwise):
   - **Remap:** run baseline vs A1 vs A2. The _correct_ remap should give the
     lowest static drift AND the lowest mean velocity, and — critically — should
     stay low under a slow controlled translation/rotation (static-only cannot
     distinguish a reflection from a rotation; add a short hand-held figure-8 and
     check the trajectory shape is not mirrored).
   - **Noise:** with the chosen remap fixed, run `acc_w/gyr_w = 0.00002` vs
     `0.0001`. Lower static drift wins; watch that the looser value doesn't
     introduce jitter under motion.
   - **Consolidation (C):** verify `/odometry` still publishes on the same topic/
     frame the test expects; it should not change drift, only structure.
3. **Acceptance target:** Final drift `< 0.2 m` over 30 s (test's "GOOD" bucket),
   mean velocity `< 0.1 m/s`. Below `0.05 m` is excellent.
4. **Record** the before/after table in this doc (template below) and only then
   pick winners and open a single integration PR.

### Results table (fill on hardware)

| Config                        | Final drift (m) | Drift rate (cm/s) | Mean vel (m/s) | Verdict |
| ----------------------------- | --------------- | ----------------- | -------------- | ------- |
| baseline (main)               |                 |                   |                |         |
| A1 remap                      |                 |                   |                |         |
| A2 remap                      |                 |                   |                |         |
| noise 0.0001 (+ chosen remap) |                 |                   |                |         |

---

## 4. Recommendation (provisional, pending §3)

- **Remap:** I cannot pick A1 vs A2 blind, and lean _suspicious of A1_ because a
  determinant-−1 reflection in an IMU mount is physically unusual — but this MUST
  be settled by the motion test in §3, not by this hunch. Default `main` keeps the
  remap gated `use_transform=False`, i.e. effectively off, which is the safe
  no-op until validated.
- **Noise:** treat `0.0001` as the leading hypothesis (6 branches converged on it)
  but confirm against this IMU's Allan variance / the A/B static test.
- **Consolidation:** adopt the structural cleanup (C) first if it stabilizes the
  launch/test harness, since it's behavior-neutral for the filter.
- **Extrinsics (`body_T_cam0`):** provenance is only _inferred_ (likely the Kalibr
  dataset in `calibration/kalibr_bags/`); no checked-in calibration output
  reproduces the exact numbers. Re-derive from a fresh Kalibr cam-IMU run while at
  the hardware and record the source.

**Bottom line:** the code currently on `main` is the safe baseline. Do not adopt
any A/B change without the §3 numbers in hand.
