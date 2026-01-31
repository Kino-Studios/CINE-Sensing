#!/usr/bin/env python3
"""
IMU Noise Analyzer for VINS-Fusion Parameter Validation

This script records static IMU data and calculates empirical noise statistics
to validate the configured IMU noise parameters in the VINS config file.

Usage:
    1. Place IMU on stable surface (NO MOVEMENT for 5 minutes)
    2. ros2 run vins imu_noise_analyzer
    3. Wait for analysis to complete
    4. Compare output to config file parameters

Author: VINS Diagnostics
Date: November 12, 2025
"""

import numpy as np
from scipy import stats
import time
import argparse
import os

# Try to import rclpy for live ROS2 operation; fall back to offline CSV mode if unavailable
HAVE_RCLPY = True
try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Imu
except Exception:
    HAVE_RCLPY = False

def run_analysis_from_arrays(accel, gyro, timestamps, warmup_time=10.0, collection_duration=300.0):
    """Perform the same comprehensive noise analysis but operate on provided numpy arrays.

    accel: (N,3) numpy array of accelerometer samples [m/s^2]
    gyro:  (N,3) numpy array of gyro samples [rad/s]
    timestamps: list or array of elapsed times corresponding to samples
    """
    if len(accel) < 100:
        print("❌ Not enough data for analysis (need >=100 samples)")
        return

    accel = np.array(accel)
    gyro = np.array(gyro)
    timestamps = np.array(timestamps)

    print("\n" + "=" * 70)
    print("IMU NOISE ANALYSIS - RESULTS")
    print("=" * 70)
    print(f"Total samples: {len(accel)}")
    duration = timestamps[-1] - warmup_time if len(timestamps) > 1 else 0.0
    print(f"Duration: {duration:.1f}s")
    if duration > 0:
        print(f"Sample rate: {len(accel) / duration:.1f} Hz")

    # ACCELEROMETER
    print("\n" + "-" * 70)
    print("ACCELEROMETER STATISTICS")
    print("-" * 70)

    accel_mean = np.mean(accel, axis=0)
    accel_std = np.std(accel, axis=0)

    print(f"Mean (m/s²):  X={accel_mean[0]:8.4f}  Y={accel_mean[1]:8.4f}  Z={accel_mean[2]:8.4f}")
    print(f"Std Dev:      X={accel_std[0]:8.4f}  Y={accel_std[1]:8.4f}  Z={accel_std[2]:8.4f}")

    gravity_mag = np.linalg.norm(accel_mean)
    expected_gravity = 9.80665
    gravity_error = abs(gravity_mag - expected_gravity)

    print(f"\nGravity magnitude: {gravity_mag:.4f} m/s²  (expected: {expected_gravity:.4f})")
    if gravity_error > 0.5:
        print(f"⚠️  Gravity error: {gravity_error:.4f} m/s² (> 0.5 m/s²)")
    else:
        print(f"✅ Gravity alignment good (error: {gravity_error:.4f} m/s²)")

    acc_n_measured = np.sqrt(np.mean(accel_std**2))
    print(f"\n📊 MEASURED NOISE PARAMETERS:")
    print(f"   acc_n (white noise):  {acc_n_measured:.4f} m/s²")

    # Bias stability
    window_size = 100
    num_windows = len(accel) // window_size
    if num_windows >= 2:
        window_means = np.array([np.mean(accel[i*window_size:(i+1)*window_size], axis=0)
                                  for i in range(num_windows)])
        acc_w_measured = np.std(np.diff(window_means, axis=0), axis=0).mean() / np.sqrt(2)
    else:
        acc_w_measured = 0.0

    print(f"   acc_w (bias drift):   {acc_w_measured:.6f} m/s³/√Hz")

    # GYROSCOPE
    print("\n" + "-" * 70)
    print("GYROSCOPE STATISTICS")
    print("-" * 70)

    gyro_mean = np.mean(gyro, axis=0)
    gyro_std = np.std(gyro, axis=0)

    print(f"Mean (rad/s): X={gyro_mean[0]:8.5f}  Y={gyro_mean[1]:8.5f}  Z={gyro_mean[2]:8.5f}")
    print(f"Std Dev:      X={gyro_std[0]:8.5f}  Y={gyro_std[1]:8.5f}  Z={gyro_std[2]:8.5f}")

    gyro_bias_mag = np.linalg.norm(gyro_mean)
    if gyro_bias_mag > 0.05:
        print(f"⚠️  High gyro bias: {gyro_bias_mag:.5f} rad/s ({np.degrees(gyro_bias_mag):.2f}°/s)")
    else:
        print(f"✅ Gyro bias acceptable: {gyro_bias_mag:.5f} rad/s ({np.degrees(gyro_bias_mag):.2f}°/s)")

    gyr_n_measured = np.sqrt(np.mean(gyro_std**2))
    print(f"\n📊 MEASURED NOISE PARAMETERS:")
    print(f"   gyr_n (white noise):  {gyr_n_measured:.6f} rad/s")

    if num_windows >= 2:
        gyro_window_means = np.array([np.mean(gyro[i*window_size:(i+1)*window_size], axis=0)
                                       for i in range(num_windows)])
        gyr_w_measured = np.std(np.diff(gyro_window_means, axis=0), axis=0).mean() / np.sqrt(2)
    else:
        gyr_w_measured = 0.0

    print(f"   gyr_w (bias drift):   {gyr_w_measured:.8f} rad/s²/√Hz")

    # Recommendations
    acc_n_recommended = min(max(acc_n_measured * 1.2, 0.08), 0.15)
    gyr_n_recommended = min(max(gyr_n_measured * 1.2, 0.004), 0.02)
    acc_w_recommended = min(max(acc_w_measured * 1.5, 0.00004), 0.001)
    gyr_w_recommended = min(max(gyr_w_measured * 1.5, 0.00001), 0.0001)

    print("\n# IMU noise parameters (add to rpi_v3_mono_config.yaml)")
    print(f"acc_n: {acc_n_recommended:.4f}          # accelerometer measurement noise")
    print(f"gyr_n: {gyr_n_recommended:.6f}        # gyroscope measurement noise")
    print(f"acc_w: {acc_w_recommended:.8f}      # accelerometer bias random walk")
    print(f"gyr_w: {gyr_w_recommended:.8f}      # gyroscope bias random walk")
    print(f"g_norm: {gravity_mag:.5f}         # measured gravity magnitude")

    # Validation against current config
    try:
        from configs.python import VinsConfig
        current_config = {
            'acc_n': VinsConfig.ACC_N,
            'gyr_n': VinsConfig.GYR_N,
            'acc_w': VinsConfig.ACC_W,
            'gyr_w': VinsConfig.GYR_W
        }
    except ImportError:
        current_config = {'acc_n': 0.5, 'gyr_n': 0.02, 'acc_w': 0.01, 'gyr_w': 0.001}

    recommended_config = {'acc_n': acc_n_recommended, 'gyr_n': gyr_n_recommended, 'acc_w': acc_w_recommended, 'gyr_w': gyr_w_recommended}

    print(f"\n{'Parameter':<10} {'Current':<12} {'Measured':<12} {'Recommended':<12} {'Error Factor':<15}")
    print("-" * 70)
    for key in current_config.keys():
        current = current_config[key]
        recommended = recommended_config[key]
        measured_val = locals().get(f"{key}_measured", 0.0)
        error_factor = current / recommended if recommended > 0 else 0
        status = "❌" if error_factor > 2.0 or error_factor < 0.5 else "✅"
        print(f"{key:<10} {current:<12.6f} {measured_val:<12.6f} {recommended:<12.6f} {error_factor:<6.1f}x {status}")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print("\n📋 NEXT STEPS:")
    print("1. Copy recommended parameters to rpi_v3_mono_config.yaml")
    print("2. If error factors > 2x, update config IMMEDIATELY")
    print("3. Run static_drift_test.py to validate improvements")

class IMUNoiseAnalyzer(Node):
    def __init__(self):
        super().__init__('imu_noise_analyzer')
        self.accel_data = []
        self.gyro_data = []
        self.timestamps = []
        self.start_time = None
        self.completed = False
        try:
            from configs.python import VinsConfig
            self.imu_sub = self.create_subscription(Imu, VinsConfig.IMU_TOPIC, self.imu_callback, 10)
        except ImportError:
            self.imu_sub = self.create_subscription(Imu, '/imu_bridge/data_raw', self.imu_callback, 10)
        self.collection_duration = 300.0
        self.warmup_time = 10.0

        # Create timer to check for completion
        self.completion_timer = self.create_timer(1.0, self.check_completion)

        self.get_logger().info("=" * 70)
        self.get_logger().info("IMU NOISE ANALYSIS - STARTING")
        self.get_logger().info("=" * 70)
        self.get_logger().info("⚠️  CRITICAL: Keep IMU completely stationary!")
        self.get_logger().info(f"📊 Collection time: {self.collection_duration}s")
        self.get_logger().info(f"🔥 Warm-up period: {self.warmup_time}s (discarded)")
        self.get_logger().info("=" * 70)

    def check_completion(self):
        """Check if data collection is complete"""
        if self.completed:
            return

        if self.start_time is None:
            return

        elapsed = time.time() - self.start_time
        if elapsed >= self.collection_duration:
            self.completed = True
            self.completion_timer.cancel()
            self.get_logger().info("\n📊 Collection complete! Running analysis...")
            run_analysis_from_arrays(self.accel_data, self.gyro_data, self.timestamps, self.warmup_time, self.collection_duration)
            raise KeyboardInterrupt("Collection complete")

    def imu_callback(self, msg):
        if self.start_time is None:
            self.start_time = time.time()
            return

        elapsed = time.time() - self.start_time
        if elapsed < self.warmup_time:
            if int(elapsed) % 2 == 0:
                self.get_logger().info(f"🔥 Warming up... {self.warmup_time - elapsed:.1f}s remaining")
            return

        self.accel_data.append([msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z])
        self.gyro_data.append([msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z])
        self.timestamps.append(elapsed)

        if len(self.accel_data) % 500 == 0:
            progress = (elapsed - self.warmup_time) / (self.collection_duration - self.warmup_time) * 100
            samples = len(self.accel_data)
            self.get_logger().info(f"📊 {progress:.1f}% complete | {samples} samples collected")

    def analyze_data(self):
        """Perform comprehensive noise analysis"""

        if len(self.accel_data) < 100:
            self.get_logger().error("❌ Not enough data collected!")
            return

        accel = np.array(self.accel_data)
        gyro = np.array(self.gyro_data)

        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("IMU NOISE ANALYSIS - RESULTS")
        self.get_logger().info("=" * 70)
        self.get_logger().info(f"Total samples: {len(accel)}")
        self.get_logger().info(f"Duration: {self.timestamps[-1] - self.warmup_time:.1f}s")
        self.get_logger().info(f"Sample rate: {len(accel) / (self.timestamps[-1] - self.warmup_time):.1f} Hz")

        # ================================================================
        # ACCELEROMETER ANALYSIS
        # ================================================================
        self.get_logger().info("\n" + "-" * 70)
        self.get_logger().info("ACCELEROMETER STATISTICS")
        self.get_logger().info("-" * 70)

        # Mean (should be close to [0, 0, -9.81] in NED frame)
        accel_mean = np.mean(accel, axis=0)
        accel_std = np.std(accel, axis=0)

        self.get_logger().info(f"Mean (m/s²):  X={accel_mean[0]:8.4f}  Y={accel_mean[1]:8.4f}  Z={accel_mean[2]:8.4f}")
        self.get_logger().info(f"Std Dev:      X={accel_std[0]:8.4f}  Y={accel_std[1]:8.4f}  Z={accel_std[2]:8.4f}")

        # Check gravity alignment
        gravity_mag = np.linalg.norm(accel_mean)
        expected_gravity = 9.80665
        gravity_error = abs(gravity_mag - expected_gravity)

        self.get_logger().info(f"\nGravity magnitude: {gravity_mag:.4f} m/s²  (expected: {expected_gravity:.4f})")

        if gravity_error > 0.5:
            self.get_logger().warn(f"⚠️  Gravity error: {gravity_error:.4f} m/s² (> 0.5 m/s²)")
            self.get_logger().warn("    IMU may be poorly calibrated or moving!")
        else:
            self.get_logger().info(f"✅ Gravity alignment good (error: {gravity_error:.4f} m/s²)")

        # White noise (measurement noise) - use std dev
        acc_n_measured = np.sqrt(np.mean(accel_std**2))  # RMS of std devs

        self.get_logger().info(f"\n📊 MEASURED NOISE PARAMETERS:")
        self.get_logger().info(f"   acc_n (white noise):  {acc_n_measured:.4f} m/s²")

        # Bias stability - look at slow drift over time
        # Split into windows and look at mean variation
        window_size = 100
        num_windows = len(accel) // window_size
        window_means = np.array([np.mean(accel[i*window_size:(i+1)*window_size], axis=0)
                                  for i in range(num_windows)])
        acc_w_measured = np.std(np.diff(window_means, axis=0), axis=0).mean() / np.sqrt(2)

        self.get_logger().info(f"   acc_w (bias drift):   {acc_w_measured:.6f} m/s³/√Hz")

        # ================================================================
        # GYROSCOPE ANALYSIS
        # ================================================================
        self.get_logger().info("\n" + "-" * 70)
        self.get_logger().info("GYROSCOPE STATISTICS")
        self.get_logger().info("-" * 70)

        gyro_mean = np.mean(gyro, axis=0)
        gyro_std = np.std(gyro, axis=0)

        self.get_logger().info(f"Mean (rad/s): X={gyro_mean[0]:8.5f}  Y={gyro_mean[1]:8.5f}  Z={gyro_mean[2]:8.5f}")
        self.get_logger().info(f"Std Dev:      X={gyro_std[0]:8.5f}  Y={gyro_std[1]:8.5f}  Z={gyro_std[2]:8.5f}")

        # Check for excessive bias
        gyro_bias_mag = np.linalg.norm(gyro_mean)
        if gyro_bias_mag > 0.05:  # 2.8 degrees/sec
            self.get_logger().warn(f"⚠️  High gyro bias: {gyro_bias_mag:.5f} rad/s ({np.degrees(gyro_bias_mag):.2f}°/s)")
            self.get_logger().warn("    Consider recalibrating IMU!")
        else:
            self.get_logger().info(f"✅ Gyro bias acceptable: {gyro_bias_mag:.5f} rad/s ({np.degrees(gyro_bias_mag):.2f}°/s)")

        # White noise
        gyr_n_measured = np.sqrt(np.mean(gyro_std**2))

        self.get_logger().info(f"\n📊 MEASURED NOISE PARAMETERS:")
        self.get_logger().info(f"   gyr_n (white noise):  {gyr_n_measured:.6f} rad/s")

        # Bias stability
        gyro_window_means = np.array([np.mean(gyro[i*window_size:(i+1)*window_size], axis=0)
                                       for i in range(num_windows)])
        gyr_w_measured = np.std(np.diff(gyro_window_means, axis=0), axis=0).mean() / np.sqrt(2)

        self.get_logger().info(f"   gyr_w (bias drift):   {gyr_w_measured:.8f} rad/s²/√Hz")

        # ================================================================
        # CONFIGURATION RECOMMENDATIONS
        # ================================================================
        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("RECOMMENDED VINS CONFIG PARAMETERS")
        self.get_logger().info("=" * 70)

        # Add safety margins
        acc_n_recommended = min(max(acc_n_measured * 1.2, 0.08), 0.15)  # Clip to reasonable range
        gyr_n_recommended = min(max(gyr_n_measured * 1.2, 0.004), 0.02)
        acc_w_recommended = min(max(acc_w_measured * 1.5, 0.00004), 0.001)
        gyr_w_recommended = min(max(gyr_w_measured * 1.5, 0.00001), 0.0001)

        print("\n# IMU noise parameters (add to rpi_v3_mono_config.yaml)")
        print(f"acc_n: {acc_n_recommended:.4f}          # accelerometer measurement noise")
        print(f"gyr_n: {gyr_n_recommended:.6f}        # gyroscope measurement noise")
        print(f"acc_w: {acc_w_recommended:.8f}      # accelerometer bias random walk")
        print(f"gyr_w: {gyr_w_recommended:.8f}      # gyroscope bias random walk")
        print(f"g_norm: {gravity_mag:.5f}         # measured gravity magnitude")

        # ================================================================
        # VALIDATION AGAINST CURRENT CONFIG
        # ================================================================
        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("VALIDATION AGAINST CURRENT CONFIG")
        self.get_logger().info("=" * 70)

        # Typical values from current config (read from VinsConfig if available)
        try:
            from configs.python import VinsConfig
            current_config = {
                'acc_n': VinsConfig.ACC_N,
                'gyr_n': VinsConfig.GYR_N,
                'acc_w': VinsConfig.ACC_W,
                'gyr_w': VinsConfig.GYR_W
            }
        except ImportError:
            current_config = {
                'acc_n': 0.5,
                'gyr_n': 0.02,
                'acc_w': 0.01,
                'gyr_w': 0.001
            }

        recommended_config = {
            'acc_n': acc_n_recommended,
            'gyr_n': gyr_n_recommended,
            'acc_w': acc_w_recommended,
            'gyr_w': gyr_w_recommended
        }

        print(f"\n{'Parameter':<10} {'Current':<12} {'Measured':<12} {'Recommended':<12} {'Error Factor':<15}")
        print("-" * 70)

        for key in current_config.keys():
            current = current_config[key]
            recommended = recommended_config[key]
            measured_val = eval(f"{key}_measured")
            error_factor = current / recommended if recommended > 0 else 0

            status = "❌" if error_factor > 2.0 or error_factor < 0.5 else "✅"

            print(f"{key:<10} {current:<12.6f} {measured_val:<12.6f} {recommended:<12.6f} {error_factor:<6.1f}x {status}")

        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("ANALYSIS COMPLETE")
        self.get_logger().info("=" * 70)
        self.get_logger().info("\n📋 NEXT STEPS:")
        self.get_logger().info("1. Copy recommended parameters to rpi_v3_mono_config.yaml")
        self.get_logger().info("2. If error factors > 2x, update config IMMEDIATELY")
        self.get_logger().info("3. Run static_drift_test.py to validate improvements")
        self.get_logger().info("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='IMU Noise Analyzer (live ROS2 or offline CSV mode)')
    parser.add_argument('--csv', type=str, help='Path to CSV file with columns: time,ax,ay,az,gx,gy,gz')
    parser.add_argument('--duration', type=float, default=300.0, help='Collection duration (s)')
    parser.add_argument('--warmup', type=float, default=10.0, help='Warmup time (s) to discard at start)')
    args = parser.parse_args()

    if args.csv:
        csv_path = args.csv
        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found: {csv_path}")
            return

        print(f"Loading IMU data from CSV: {csv_path}")
        try:
            data = np.loadtxt(csv_path, delimiter=',', skiprows=1)
            # Expect columns: time, ax, ay, az, gx, gy, gz
            if data.shape[1] < 7:
                print("❌ CSV must have at least 7 columns: time, ax, ay, az, gx, gy, gz")
                return
            timestamps = data[:, 0].tolist()
            accel = data[:, 1:4]
            gyro = data[:, 4:7]
            # Normalize timestamps to elapsed seconds
            t0 = timestamps[0]
            timestamps = (np.array(timestamps) - t0).tolist()
            run_analysis_from_arrays(accel, gyro, timestamps, warmup_time=args.warmup, collection_duration=args.duration)
        except Exception as e:
            print(f"❌ Failed to load CSV: {e}")
        return

    # Live ROS2 mode
    if not HAVE_RCLPY:
        print("❌ rclpy (ROS2) is not available in this Python environment.")
        print("Run this script on the robot with ROS2 sourced, or export IMU to CSV and run with --csv <file>")
        return

    rclpy.init()
    node = IMUNoiseAnalyzer()
    shutdown_called = False
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        if len(node.accel_data) > 100:
            print("Running partial analysis...")
            run_analysis_from_arrays(node.accel_data, node.gyro_data, node.timestamps, node.warmup_time, node.collection_duration)
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        if not shutdown_called:
            try:
                rclpy.shutdown()
                shutdown_called = True
            except Exception:
                pass

if __name__ == '__main__':
    main()
