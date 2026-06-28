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

import argparse
import logging
import os
import time

import numpy as np

# Try to import rclpy for live ROS2 operation; fall back to offline CSV mode if unavailable
HAVE_RCLPY = True
try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Imu
except Exception:
    HAVE_RCLPY = False

EXPECTED_GRAVITY = 9.80665
WINDOW_SIZE = 100
DEFAULT_CURRENT_CONFIG = {"acc_n": 0.5, "gyr_n": 0.02, "acc_w": 0.01, "gyr_w": 0.001}

logger = logging.getLogger(__name__)


def load_current_config() -> dict:
    """Return the active VINS noise config, falling back to safe defaults."""
    try:
        from configs.python import VinsConfig

        return {
            "acc_n": VinsConfig.ACC_N,
            "gyr_n": VinsConfig.GYR_N,
            "acc_w": VinsConfig.ACC_W,
            "gyr_w": VinsConfig.GYR_W,
        }
    except ImportError:
        return dict(DEFAULT_CURRENT_CONFIG)


def compute_noise_statistics(accel, gyro, timestamps, warmup_time: float = 10.0) -> dict:
    """Compute all IMU noise statistics from raw samples.

    Pure math with no side effects. Both the offline array entry point and the
    live ROS2 node feed their collected samples through this single function so
    the analysis logic exists in exactly one place.

    accel: (N,3) array-like of accelerometer samples [m/s^2]
    gyro:  (N,3) array-like of gyro samples [rad/s]
    timestamps: array-like of elapsed times corresponding to samples
    warmup_time: seconds discarded at start, subtracted from reported duration

    Returns a dict of derived values, including a plain ``measured`` dict keyed
    by config name (acc_n/acc_w/gyr_n/gyr_w) used for safe validation lookups.
    """
    accel = np.array(accel)
    gyro = np.array(gyro)
    timestamps = np.array(timestamps)

    duration = timestamps[-1] - warmup_time if len(timestamps) > 1 else 0.0
    sample_rate = len(accel) / duration if duration > 0 else 0.0

    accel_mean = np.mean(accel, axis=0)
    accel_std = np.std(accel, axis=0)
    gravity_mag = np.linalg.norm(accel_mean)
    gravity_error = abs(gravity_mag - EXPECTED_GRAVITY)
    acc_n_measured = np.sqrt(np.mean(accel_std**2))

    gyro_mean = np.mean(gyro, axis=0)
    gyro_std = np.std(gyro, axis=0)
    gyro_bias_mag = np.linalg.norm(gyro_mean)
    gyr_n_measured = np.sqrt(np.mean(gyro_std**2))

    num_windows = len(accel) // WINDOW_SIZE
    if num_windows >= 2:
        accel_window_means = np.array(
            [
                np.mean(accel[i * WINDOW_SIZE : (i + 1) * WINDOW_SIZE], axis=0)
                for i in range(num_windows)
            ]
        )
        acc_w_measured = np.std(np.diff(accel_window_means, axis=0), axis=0).mean() / np.sqrt(2)
        gyro_window_means = np.array(
            [
                np.mean(gyro[i * WINDOW_SIZE : (i + 1) * WINDOW_SIZE], axis=0)
                for i in range(num_windows)
            ]
        )
        gyr_w_measured = np.std(np.diff(gyro_window_means, axis=0), axis=0).mean() / np.sqrt(2)
    else:
        acc_w_measured = 0.0
        gyr_w_measured = 0.0

    measured = {
        "acc_n": acc_n_measured,
        "acc_w": acc_w_measured,
        "gyr_n": gyr_n_measured,
        "gyr_w": gyr_w_measured,
    }

    recommended = {
        "acc_n": min(max(acc_n_measured * 1.2, 0.08), 0.15),
        "gyr_n": min(max(gyr_n_measured * 1.2, 0.004), 0.02),
        "acc_w": min(max(acc_w_measured * 1.5, 0.00004), 0.001),
        "gyr_w": min(max(gyr_w_measured * 1.5, 0.00001), 0.0001),
    }

    return {
        "num_samples": len(accel),
        "duration": duration,
        "sample_rate": sample_rate,
        "accel_mean": accel_mean,
        "accel_std": accel_std,
        "gravity_mag": gravity_mag,
        "gravity_error": gravity_error,
        "gyro_mean": gyro_mean,
        "gyro_std": gyro_std,
        "gyro_bias_mag": gyro_bias_mag,
        "measured": measured,
        "recommended": recommended,
    }


def format_analysis_report(stats_result: dict, current_config: dict) -> list:
    """Render computed statistics into ordered report lines (no I/O)."""
    accel_mean = stats_result["accel_mean"]
    accel_std = stats_result["accel_std"]
    gyro_mean = stats_result["gyro_mean"]
    gyro_std = stats_result["gyro_std"]
    gravity_mag = stats_result["gravity_mag"]
    gravity_error = stats_result["gravity_error"]
    gyro_bias_mag = stats_result["gyro_bias_mag"]
    measured = stats_result["measured"]
    recommended = stats_result["recommended"]

    lines = []
    lines.append("\n" + "=" * 70)
    lines.append("IMU NOISE ANALYSIS - RESULTS")
    lines.append("=" * 70)
    lines.append(f"Total samples: {stats_result['num_samples']}")
    lines.append(f"Duration: {stats_result['duration']:.1f}s")
    if stats_result["duration"] > 0:
        lines.append(f"Sample rate: {stats_result['sample_rate']:.1f} Hz")

    lines.append("\n" + "-" * 70)
    lines.append("ACCELEROMETER STATISTICS")
    lines.append("-" * 70)
    lines.append(
        f"Mean (m/s²):  X={accel_mean[0]:8.4f}  Y={accel_mean[1]:8.4f}  Z={accel_mean[2]:8.4f}"
    )
    lines.append(
        f"Std Dev:      X={accel_std[0]:8.4f}  Y={accel_std[1]:8.4f}  Z={accel_std[2]:8.4f}"
    )
    lines.append(f"\nGravity magnitude: {gravity_mag:.4f} m/s²  (expected: {EXPECTED_GRAVITY:.4f})")

    if gravity_error > 0.5:
        lines.append(f"⚠️  Gravity error: {gravity_error:.4f} m/s² (> 0.5 m/s²)")
    else:
        lines.append(f"✅ Gravity alignment good (error: {gravity_error:.4f} m/s²)")

    lines.append("\n📊 MEASURED NOISE PARAMETERS:")
    lines.append(f"   acc_n (white noise):  {measured['acc_n']:.4f} m/s²")
    lines.append(f"   acc_w (bias drift):   {measured['acc_w']:.6f} m/s³/√Hz")

    lines.append("\n" + "-" * 70)
    lines.append("GYROSCOPE STATISTICS")
    lines.append("-" * 70)
    lines.append(
        f"Mean (rad/s): X={gyro_mean[0]:8.5f}  Y={gyro_mean[1]:8.5f}  Z={gyro_mean[2]:8.5f}"
    )
    lines.append(f"Std Dev:      X={gyro_std[0]:8.5f}  Y={gyro_std[1]:8.5f}  Z={gyro_std[2]:8.5f}")

    if gyro_bias_mag > 0.05:
        lines.append(
            f"⚠️  High gyro bias: {gyro_bias_mag:.5f} rad/s ({np.degrees(gyro_bias_mag):.2f}°/s)"
        )
    else:
        lines.append(
            f"✅ Gyro bias acceptable: {gyro_bias_mag:.5f} rad/s ({np.degrees(gyro_bias_mag):.2f}°/s)"
        )

    lines.append("\n📊 MEASURED NOISE PARAMETERS:")
    lines.append(f"   gyr_n (white noise):  {measured['gyr_n']:.6f} rad/s")
    lines.append(f"   gyr_w (bias drift):   {measured['gyr_w']:.8f} rad/s²/√Hz")

    lines.append("\n# IMU noise parameters (add to rpi_v3_mono_config.yaml)")
    lines.append(f"acc_n: {recommended['acc_n']:.4f}          # accelerometer measurement noise")
    lines.append(f"gyr_n: {recommended['gyr_n']:.6f}        # gyroscope measurement noise")
    lines.append(f"acc_w: {recommended['acc_w']:.8f}      # accelerometer bias random walk")
    lines.append(f"gyr_w: {recommended['gyr_w']:.8f}      # gyroscope bias random walk")
    lines.append(f"g_norm: {gravity_mag:.5f}         # measured gravity magnitude")

    lines.append(
        f"\n{'Parameter':<10} {'Current':<12} {'Measured':<12} {'Recommended':<12} {'Error Factor':<15}"
    )
    lines.append("-" * 70)
    for key in current_config.keys():
        current = current_config[key]
        recommended_val = recommended[key]
        measured_val = measured.get(key, 0.0)
        error_factor = current / recommended_val if recommended_val > 0 else 0
        status = "❌" if error_factor > 2.0 or error_factor < 0.5 else "✅"
        lines.append(
            f"{key:<10} {current:<12.6f} {measured_val:<12.6f} "
            f"{recommended_val:<12.6f} {error_factor:<6.1f}x {status}"
        )

    lines.append("\n" + "=" * 70)
    lines.append("ANALYSIS COMPLETE")
    lines.append("=" * 70)
    lines.append("\n📋 NEXT STEPS:")
    lines.append("1. Copy recommended parameters to rpi_v3_mono_config.yaml")
    lines.append("2. If error factors > 2x, update config IMMEDIATELY")
    lines.append("3. Run static_drift_test.py to validate improvements")

    return lines


def run_analysis_from_arrays(accel, gyro, timestamps, warmup_time=10.0, collection_duration=300.0):
    """Perform the comprehensive noise analysis on provided numpy arrays.

    accel: (N,3) numpy array of accelerometer samples [m/s^2]
    gyro:  (N,3) numpy array of gyro samples [rad/s]
    timestamps: list or array of elapsed times corresponding to samples
    """
    if len(accel) < 100:
        print("❌ Not enough data for analysis (need >=100 samples)")

        return

    stats_result = compute_noise_statistics(accel, gyro, timestamps, warmup_time)
    current_config = load_current_config()

    for line in format_analysis_report(stats_result, current_config):
        print(line)


class IMUNoiseAnalyzer(Node):
    def __init__(self):
        super().__init__("imu_noise_analyzer")
        self.accel_data = []
        self.gyro_data = []
        self.timestamps = []
        self.start_time = None
        self.completed = False
        try:
            from configs.python import VinsConfig

            self.imu_sub = self.create_subscription(
                Imu, VinsConfig.IMU_TOPIC, self.imu_callback, 10
            )
        except ImportError:
            self.imu_sub = self.create_subscription(
                Imu, "/imu_bridge/data_raw", self.imu_callback, 10
            )
        self.collection_duration = 300.0
        self.warmup_time = 10.0

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
            run_analysis_from_arrays(
                self.accel_data,
                self.gyro_data,
                self.timestamps,
                self.warmup_time,
                self.collection_duration,
            )

            raise KeyboardInterrupt("Collection complete")

    def imu_callback(self, msg):
        if self.start_time is None:
            self.start_time = time.time()

            return

        elapsed = time.time() - self.start_time
        if elapsed < self.warmup_time:
            if int(elapsed) % 2 == 0:
                self.get_logger().info(
                    f"🔥 Warming up... {self.warmup_time - elapsed:.1f}s remaining"
                )

            return

        self.accel_data.append(
            [msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z]
        )
        self.gyro_data.append(
            [msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z]
        )
        self.timestamps.append(elapsed)

        if len(self.accel_data) % 500 == 0:
            progress = (
                (elapsed - self.warmup_time) / (self.collection_duration - self.warmup_time) * 100
            )
            samples = len(self.accel_data)
            self.get_logger().info(f"📊 {progress:.1f}% complete | {samples} samples collected")

    def analyze_data(self):
        """Perform comprehensive noise analysis and log the report."""
        if len(self.accel_data) < 100:
            self.get_logger().error("❌ Not enough data collected!")

            return

        stats_result = compute_noise_statistics(
            self.accel_data, self.gyro_data, self.timestamps, self.warmup_time
        )
        current_config = load_current_config()

        for line in format_analysis_report(stats_result, current_config):
            self.get_logger().info(line)


def main():
    parser = argparse.ArgumentParser(
        description="IMU Noise Analyzer (live ROS2 or offline CSV mode)"
    )
    parser.add_argument(
        "--csv", type=str, help="Path to CSV file with columns: time,ax,ay,az,gx,gy,gz"
    )
    parser.add_argument("--duration", type=float, default=300.0, help="Collection duration (s)")
    parser.add_argument(
        "--warmup", type=float, default=10.0, help="Warmup time (s) to discard at start)"
    )
    args = parser.parse_args()

    if args.csv:
        csv_path = args.csv
        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found: {csv_path}")

            return

        print(f"Loading IMU data from CSV: {csv_path}")
        try:
            data = np.loadtxt(csv_path, delimiter=",", skiprows=1)
            # Expect columns: time, ax, ay, az, gx, gy, gz
            if data.shape[1] < 7:
                print("❌ CSV must have at least 7 columns: time, ax, ay, az, gx, gy, gz")

                return
            timestamps = data[:, 0].tolist()
            accel = data[:, 1:4]
            gyro = data[:, 4:7]
            first_timestamp = timestamps[0]
            timestamps = (np.array(timestamps) - first_timestamp).tolist()
            run_analysis_from_arrays(
                accel, gyro, timestamps, warmup_time=args.warmup, collection_duration=args.duration
            )
        except Exception as exc:
            print(f"❌ Failed to load CSV: {exc}")

        return

    # Live ROS2 mode
    if not HAVE_RCLPY:
        print("❌ rclpy (ROS2) is not available in this Python environment.")
        print(
            "Run this script on the robot with ROS2 sourced, or export IMU to CSV and run with --csv <file>"
        )

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
            run_analysis_from_arrays(
                node.accel_data,
                node.gyro_data,
                node.timestamps,
                node.warmup_time,
                node.collection_duration,
            )
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


if __name__ == "__main__":
    main()
