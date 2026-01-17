# VINS-Fusion Testing and Validation Guide
## Step-by-Step Procedure for RPi Camera V3 + Pixhawk IMU

Date: November 12, 2025

---

## OVERVIEW

This guide walks through systematic testing and validation of your VINS-Fusion configuration. Follow steps **IN ORDER** - each builds on the previous.

**Estimated Time:** 1-2 hours for complete validation

---

## PREREQUISITES

### Files Created:
- ✅ `PARAMETER_ANALYSIS.md` - Comprehensive parameter review
- ✅ `rpi_v3_mono_config_CORRECTED.yaml` - Fixed configuration
- ✅ `imu_noise_analyzer.py` - IMU noise measurement tool
- ✅ `feature_quality_test.py` - Feature tracking validator
- ✅ `solver_convergence_monitor.py` - Optimization monitor
- ✅ `static_drift_test.py` - Drift test (already existed)

### Setup:
```bash
cd /home/fishnos/CINE-Sensing
chmod +x autocine_ws/src/VINS-Fusion-ROS2-humble-arm/vins/tests/*.py
```

---

## PHASE 1: IMU VALIDATION (CRITICAL - DO THIS FIRST)

### Step 1.1: Prepare for IMU Test

**Setup:**
1. Place Pixhawk on STABLE surface (desk, table - not on drone)
2. Ensure NO VIBRATION for next 5 minutes
3. Start MAVROS:
```bash
# Terminal 1
ros2 launch mavros px4.launch fcu_url:=/dev/ttyACM0:921600
```

4. Start IMU bridge:
```bash
# Terminal 2
cd ~/CINE-Sensing
source source_scripts.sh
ros2 run fc_data imu_bridge
```

### Step 1.2: Run IMU Noise Analysis

```bash
# Terminal 3
cd ~/CINE-Sensing
source source_scripts.sh
python3 sensing_ws/src/VINS-Fusion-ROS2-humble-arm/vins/tests/imu_noise_analyzer.py
```

**What to expect:**
- Warm-up: 10 seconds (data discarded)
- Collection: 5 minutes (300 seconds)
- Progress updates every 500 samples
- Final analysis with recommended parameters

**Critical outputs:**
- `acc_n` - should be ~0.08-0.15 (NOT 0.5!)
- `acc_w` - should be ~0.0001 (NOT 0.01!)
- `gyr_n` - should be ~0.004-0.015 (NOT 0.02!)
- `gyr_w` - should be ~0.0001 (NOT 0.001!)

### Step 1.3: Update Configuration

**IF measured values differ from config by > 2x:**

```bash
# Backup current config
cp sensing_ws/src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/rpi_v3_mono_config.yaml \
   sensing_ws/src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/rpi_v3_mono_config_BACKUP.yaml

# Option A: Use pre-corrected config
cp sensing_ws/src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/rpi_v3_mono_config_CORRECTED.yaml \
   sensing_ws/src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/rpi_v3_mono_config.yaml

# Option B: Manually edit config file with measured values
nano sensing_ws/src/VINS-Fusion-ROS2-humble-arm/config/rpi_camera_v3/rpi_v3_mono_config.yaml
# Update acc_n, acc_w, gyr_n, gyr_w with values from analyzer
```

**Expected improvements:**
| Parameter | Before | After | Change |
|-----------|--------|-------|--------|
| acc_n | 0.5 | 0.1 | 5x reduction |
| acc_w | 0.01 | 0.0001 | 100x reduction |
| gyr_n | 0.02 | 0.01 | 2x reduction |
| gyr_w | 0.001 | 0.0001 | 10x reduction |

---

## PHASE 2: STATIC DRIFT TEST

### Step 2.1: Start VINS System

**IMPORTANT: Stop all previous terminals (Ctrl+C) first**

```bash
# Terminal 1: Run complete VINS stack
cd ~/CINE-Sensing
source source_scripts.sh
python3 sensing_ws/src/VINS-Fusion-ROS2-humble-arm/vins/run_vins.py
```

**Wait for initialization:**
- Look for "Initialization finished!" message
- Should take 3-10 seconds
- Feature tracking should show 200-300 features

### Step 2.2: Run Static Drift Test

```bash
# Terminal 2
cd ~/CINE-Sensing
source source_scripts.sh
python3 sensing_ws/src/VINS-Fusion-ROS2-humble-arm/vins/tests/static_drift_test.py
```

**Keep sensor COMPLETELY STILL for 30 seconds!**

**Expected results AFTER configuration fixes:**
- Final drift: < 0.2m (20cm) ✅
- Mean velocity: < 0.1 m/s ✅
- Max drift: < 0.5m ✅

**If results are poor:**
- Final drift > 2m → IMU bias calibration needed
- Velocity > 1 m/s → Check gravity frame (should be NED)
- Oscillating → Feature tracking issues (go to Phase 3)

**Interpreting results:**

| Final Drift | Status | Action |
|-------------|--------|--------|
| < 0.05m | ✅ EXCELLENT | Proceed to Phase 3 |
| 0.05-0.2m | ✅ GOOD | Proceed to Phase 3 |
| 0.2-0.5m | ⚠️ ACCEPTABLE | Run feature test, may need tuning |
| 0.5-2.0m | ⚠️ POOR | Re-check IMU parameters |
| > 2.0m | ❌ FAIL | Go back to Phase 1 |

---

## PHASE 3: FEATURE TRACKING VALIDATION

### Step 3.1: Run Feature Quality Test

**Keep VINS running from Phase 2, Terminal 1**

```bash
# Terminal 2
cd ~/CINE-Sensing
source source_scripts.sh
python3 sensing_ws/src/VINS-Fusion-ROS2-humble-arm/vins/tests/feature_quality_test.py
```

**During test:**
- Move camera SLOWLY through environment
- Point at textured surfaces (walls, furniture, NOT blank walls)
- Test runs for 30 seconds

**Expected results:**
- Mean features: 200-300 per frame
- Coefficient of variation: < 15%
- Low-feature frames: < 10%
- Well distributed across image

**Interpreting results:**

| Mean Features | Status | Action |
|---------------|--------|--------|
| < 100 | ❌ TOO LOW | Increase max_cnt, lower detect_threshold |
| 100-150 | ⚠️ LOW | Consider lowering detect_threshold |
| 150-350 | ✅ GOOD | No action needed |
| > 350 | ⚠️ HIGH | May slow system, increase detect_threshold |

**Common issues:**

1. **Clustered features:**
   - Increase `min_dist` from 15 → 25

2. **Unstable tracking (high CV):**
   - Check camera exposure (may be too high/low)
   - Increase shutter speed if motion blur visible

3. **Low feature count:**
   - Decrease `detect_threshold` from 10 → 6-8
   - Increase `max_cnt` from 200 → 300

---

## PHASE 4: SOLVER CONVERGENCE CHECK

### Step 4.1: Monitor Solver Performance

**Keep VINS running from Phase 2, Terminal 1**

```bash
# Terminal 2
cd ~/CINE-Sensing
source source_scripts.sh
python3 sensing_ws/src/VINS-Fusion-ROS2-humble-arm/vins/tests/solver_convergence_monitor.py
```

**During test:**
- Move sensor through normal trajectory
- Include rotation and translation
- Test runs for 60 seconds

**Also watch Terminal 1 (VINS output) for:**
- `Linear solver failure`
- `Cholesky factorization`
- `solve_ceres costs: XX ms`

**Expected results:**
- Solver failure rate: < 1%
- Cholesky failures: 0
- Iteration time: 20-60ms (should be < 100ms)

**If failures occur:**

| Failure Rate | Action |
|--------------|--------|
| 0% | ✅ Perfect - proceed to Phase 5 |
| < 1% | ✅ Good - occasional failures OK |
| 1-5% | ⚠️ Re-run IMU noise analyzer |
| > 5% | ❌ Go back to Phase 1 |

**Cholesky failures specifically indicate:**
- IMU noise parameters still too high
- OR poor feature tracking (check Phase 3)

---

## PHASE 5: DYNAMIC MOTION TEST

### Step 5.1: Figure-8 Pattern

**Prerequisites:**
- All previous tests passed
- Static drift < 0.2m
- No solver failures

**Test procedure:**
1. Start at origin, facing forward
2. Move slowly in figure-8 pattern (2m diameter)
3. Return to exact starting position
4. Total duration: ~30 seconds

**Monitor in Terminal 1:**
```bash
ros2 topic echo /odometry
```

**Expected behavior:**
- Smooth position estimates (no jumps)
- Return to near-origin at end (< 0.5m error)
- Velocity estimates match actual speed

**Success criteria:**
- Position drift < 10% of distance traveled
- No "jumping" in estimates
- Odometry maintains throughout motion

---

## TROUBLESHOOTING MATRIX

### Symptom: High Static Drift (> 1m)

**Possible causes (in order of likelihood):**

1. **IMU noise parameters too high** (90% of cases)
   - Solution: Re-run imu_noise_analyzer
   - Verify config matches measured values
   - Common error: Using default 0.5 instead of measured 0.1

2. **Wrong coordinate frame**
   - Check: Is IMU bridge running?
   - Verify: ENU→NED transformation active
   - Test: `ros2 topic echo /imu_bridge/data_raw`

3. **IMU not calibrated**
   - Solution: Calibrate IMU in PX4 (requires QGroundControl)
   - Check: Gyro bias should be < 0.05 rad/s

### Symptom: Solver Failures

**Cholesky factorization errors:**

1. **Primary cause: IMU noise too permissive**
   ```yaml
   # WRONG (current)
   acc_n: 0.5

   # CORRECT (typical)
   acc_n: 0.1
   ```

2. **Secondary cause: Insufficient solver time**
   ```yaml
   # WRONG
   max_solver_time: 0.04

   # CORRECT
   max_solver_time: 0.10
   ```

3. **Tertiary cause: Poor features**
   - Run feature_quality_test
   - Ensure 200+ features tracked

### Symptom: "Wait for IMU" Never Ends

1. Check topics:
```bash
ros2 topic list | grep imu
# Should see: /imu_bridge/data_raw
```

2. Check IMU bridge:
```bash
ros2 node list | grep imu
# Should see: /imu_bridge
```

3. Check config:
```yaml
# In rpi_v3_mono_config.yaml
imu_topic: "/imu_bridge/data_raw"  # NOT /mavros/imu/data
```

### Symptom: Poor Feature Tracking (< 100 features)

**Ordered checklist:**

1. **Lighting:** Ensure adequate illumination
2. **Texture:** Point at textured surfaces (not blank walls)
3. **Focus:** Verify camera is in focus
4. **Config:**
   ```yaml
   max_cnt: 250           # Increase from 200
   detect_threshold: 6    # Decrease from 10
   min_dist: 20           # OK
   ```

---

## VALIDATION CHECKLIST

Before declaring system "working":

- [ ] IMU noise analyzer completed successfully
- [ ] Config updated with measured values (error factors < 2x)
- [ ] Static drift test: < 0.2m final drift
- [ ] Static drift test: < 0.1 m/s mean velocity
- [ ] Feature tracking: 200-300 features per frame
- [ ] Feature distribution: well-spread (clustering metric < 0.8)
- [ ] Solver convergence: < 1% failure rate
- [ ] Solver convergence: 0 Cholesky errors
- [ ] Dynamic motion test: figure-8 completed
- [ ] Position returns to origin (< 0.5m error)

---

## EXPECTED FINAL CONFIGURATION

```yaml
# Feature Tracking
max_cnt: 250
min_dist: 20
F_threshold: 1.0
detect_threshold: 10
min_parallax: 1.0

# Optimization
max_solver_time: 0.10
max_num_iterations: 8
keyframe_parallax: 10.0

# IMU Noise (MEASURED from imu_noise_analyzer)
acc_n: 0.08-0.15      # NOT 0.5
gyr_n: 0.004-0.015    # NOT 0.02
acc_w: 0.00004-0.001  # NOT 0.01
gyr_w: 0.00001-0.0001 # NOT 0.001

# Time Sync
estimate_td: 0        # NOT 1 (system clock)
estimate_extrinsic: 0 # Fixed extrinsics
```

---

## SUCCESS METRICS

### Minimum Viable Performance:
- Static drift (30s): < 0.5m
- Solver failures: < 5%
- Features tracked: > 150

### Good Performance:
- Static drift (30s): < 0.2m
- Solver failures: < 1%
- Features tracked: 200-300

### Excellent Performance:
- Static drift (30s): < 0.05m
- Solver failures: 0%
- Features tracked: 250-350

---

## NEXT STEPS AFTER VALIDATION

Once all tests pass:

1. **Calibrate Scale:**
   - Move known distance (e.g., 1m)
   - Compare odometry estimate
   - Adjust if needed (typically within 5-10%)

2. **Extended Testing:**
   - 5-minute continuous run
   - Various lighting conditions
   - Different motion speeds

3. **Integration:**
   - Connect to path planner
   - Test with cinematography goals
   - Implement safety checks

---

## REFERENCE VALUES

### Hardware Specifications:

**RPi Camera V3:**
- Resolution: 1152×648 (configured)
- Frame rate: 25 Hz
- FOV: ~75° diagonal

**Pixhawk IMU (MPU6000/6500):**
- Accelerometer range: ±8g
- Gyroscope range: ±2000°/s
- Sample rate: 200-1000 Hz
- Noise density: See datasheet values in config

### Timing Budgets:

At 25 Hz camera rate:
- Frame period: 40ms
- Processing budget: ~30-35ms
- Solver budget: 20-30ms (configured: 100ms max)

---

## SUPPORT

If issues persist after following this guide:

1. Review `PARAMETER_ANALYSIS.md` for theoretical background
2. Check VINS-Fusion GitHub issues
3. Verify all dependencies are correct versions
4. Consider hardware issues (IMU calibration, camera focus)

**Most common error:** IMU noise parameters still too high!
**Quick check:** Multiply your acc_n, gyr_n, acc_w, gyr_w by 0.2 and retry.

---

Last updated: November 12, 2025
