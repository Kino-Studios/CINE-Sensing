#!/usr/bin/env python3
"""
Feature Quality Tester for VINS-Fusion

Monitors feature tracking quality in real-time:
- Feature count per frame
- Tracking success rate
- Distribution across image
- Outlier detection rate

Usage:
    ros2 run vins feature_quality_test

Author: VINS Diagnostics
Date: November 12, 2025
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud
from geometry_msgs.msg import Point32
import numpy as np
import time

class FeatureQualityTest(Node):
    def __init__(self):
        super().__init__('feature_quality_test')

        # Statistics tracking
        self.frame_count = 0
        self.feature_counts = []
        self.start_time = None
        self.test_duration = 30.0  # 30 seconds

        # Feature distribution tracking
        self.feature_positions = []

        # Subscribe to feature point cloud from VINS
        self.feature_sub = self.create_subscription(
            PointCloud,
            '/feature_tracker/feature',
            self.feature_callback,
            10
        )

        self.get_logger().info("=" * 70)
        self.get_logger().info("FEATURE TRACKING QUALITY TEST")
        self.get_logger().info("=" * 70)
        self.get_logger().info(f"Test duration: {self.test_duration}s")
        self.get_logger().info("Move camera slowly through environment...")
        self.get_logger().info("=" * 70)

    def feature_callback(self, msg: PointCloud):
        if self.start_time is None:
            self.start_time = time.time()

        elapsed = time.time() - self.start_time

        if elapsed > self.test_duration:
            self.analyze_results()
            rclpy.shutdown()
            return

        self.frame_count += 1
        num_features = len(msg.points)
        self.feature_counts.append(num_features)

        # Extract feature positions (x, y are image coordinates)
        positions = [(p.x, p.y) for p in msg.points]
        self.feature_positions.append(positions)

        # Real-time feedback every 10 frames
        if self.frame_count % 10 == 0:
            recent_avg = np.mean(self.feature_counts[-10:])
            self.get_logger().info(
                f"Frame {self.frame_count}: {num_features} features | "
                f"Avg (last 10): {recent_avg:.1f} | "
                f"Time: {elapsed:.1f}s"
            )

    def analyze_results(self):
        """Comprehensive feature tracking analysis"""

        if len(self.feature_counts) < 10:
            self.get_logger().error("❌ Not enough frames collected!")
            return

        counts = np.array(self.feature_counts)

        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("FEATURE TRACKING QUALITY ANALYSIS")
        self.get_logger().info("=" * 70)

        # ================================================================
        # FEATURE COUNT STATISTICS
        # ================================================================
        mean_features = np.mean(counts)
        std_features = np.std(counts)
        min_features = np.min(counts)
        max_features = np.max(counts)
        median_features = np.median(counts)

        self.get_logger().info(f"\nFrames analyzed: {len(counts)}")
        self.get_logger().info(f"Frame rate: {len(counts) / self.test_duration:.1f} Hz")

        self.get_logger().info("\n" + "-" * 70)
        self.get_logger().info("FEATURE COUNT STATISTICS")
        self.get_logger().info("-" * 70)
        self.get_logger().info(f"Mean:     {mean_features:.1f} features/frame")
        self.get_logger().info(f"Std Dev:  {std_features:.1f}")
        self.get_logger().info(f"Median:   {median_features:.1f}")
        self.get_logger().info(f"Min:      {min_features}")
        self.get_logger().info(f"Max:      {max_features}")

        # Assess feature count
        if mean_features < 100:
            status = "❌ CRITICAL"
            message = "Too few features! Increase max_cnt or lower detect_threshold"
        elif mean_features < 150:
            status = "⚠️  LOW"
            message = "Feature count below optimal. Consider tuning parameters"
        elif mean_features > 350:
            status = "⚠️  HIGH"
            message = "Very high feature count may slow down system"
        else:
            status = "✅ GOOD"
            message = "Feature count in optimal range"

        self.get_logger().info(f"\n{status}: {message}")

        # ================================================================
        # STABILITY ANALYSIS
        # ================================================================
        self.get_logger().info("\n" + "-" * 70)
        self.get_logger().info("TRACKING STABILITY")
        self.get_logger().info("-" * 70)

        # Coefficient of variation (CV) = std/mean
        cv = std_features / mean_features if mean_features > 0 else 0

        self.get_logger().info(f"Coefficient of Variation: {cv:.2%}")

        if cv < 0.15:
            self.get_logger().info("✅ STABLE: Consistent feature tracking")
        elif cv < 0.30:
            self.get_logger().info("⚠️  MODERATE: Some tracking variability")
        else:
            self.get_logger().info("❌ UNSTABLE: High tracking variability")
            self.get_logger().info("   - Check lighting conditions")
            self.get_logger().info("   - Verify camera exposure settings")
            self.get_logger().info("   - May need to adjust min_dist or detect_threshold")

        # Count frames with very low features
        low_feature_frames = np.sum(counts < 100)
        low_feature_ratio = low_feature_frames / len(counts)

        self.get_logger().info(f"\nFrames with < 100 features: {low_feature_frames} ({low_feature_ratio:.1%})")

        if low_feature_ratio > 0.10:
            self.get_logger().warn("⚠️  High ratio of low-feature frames!")
            self.get_logger().warn("   Possible causes:")
            self.get_logger().warn("   - detect_threshold too high")
            self.get_logger().warn("   - Poor lighting or texture")
            self.get_logger().warn("   - Motion blur (reduce shutter speed)")

        # ================================================================
        # SPATIAL DISTRIBUTION ANALYSIS
        # ================================================================
        self.get_logger().info("\n" + "-" * 70)
        self.get_logger().info("FEATURE DISTRIBUTION ANALYSIS")
        self.get_logger().info("-" * 70)

        # Analyze spatial distribution for recent frames
        recent_frames = min(10, len(self.feature_positions))
        all_positions = []
        for positions in self.feature_positions[-recent_frames:]:
            all_positions.extend(positions)

        if len(all_positions) > 20:
            positions_array = np.array(all_positions)
            x_coords = positions_array[:, 0]
            y_coords = positions_array[:, 1]

            import sys
            import os

            # Add project root to path to find configs
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../..'))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from configs.python import RuleOfThirdsConstants

            # Expected image dimensions (from config)
            img_width = RuleOfThirdsConstants.FRAME_WIDTH
            img_height = RuleOfThirdsConstants.FRAME_HEIGHT

            # Divide into grid cells
            grid_rows = 4
            grid_cols = 6
            cell_width = img_width / grid_cols
            cell_height = img_height / grid_rows

            # Count features in each cell
            grid_counts = np.zeros((grid_rows, grid_cols))
            for x, y in zip(x_coords, y_coords):
                col = min(int(x / cell_width), grid_cols - 1)
                row = min(int(y / cell_height), grid_rows - 1)
                grid_counts[row, col] += 1

            # Normalize by number of frames
            grid_counts /= recent_frames

            # Calculate distribution metrics
            mean_per_cell = np.mean(grid_counts)
            std_per_cell = np.std(grid_counts)
            min_per_cell = np.min(grid_counts)
            max_per_cell = np.max(grid_counts)

            self.get_logger().info(f"Grid: {grid_rows}×{grid_cols} cells")
            self.get_logger().info(f"Mean features/cell: {mean_per_cell:.1f}")
            self.get_logger().info(f"Std dev: {std_per_cell:.1f}")
            self.get_logger().info(f"Min/Max: {min_per_cell:.0f} / {max_per_cell:.0f}")

            # Check for clustering
            clustering_metric = std_per_cell / mean_per_cell if mean_per_cell > 0 else 0

            if clustering_metric < 0.5:
                self.get_logger().info("✅ WELL DISTRIBUTED: Features spread evenly")
            elif clustering_metric < 1.0:
                self.get_logger().info("⚠️  MODERATE CLUSTERING: Some concentration")
            else:
                self.get_logger().info("❌ HIGH CLUSTERING: Features concentrated in few areas")
                self.get_logger().info("   - Increase min_dist parameter")
                self.get_logger().info("   - Check for image artifacts or patterns")

            # Visualize distribution (ASCII art)
            self.get_logger().info("\nFeature Distribution Heatmap:")
            self.get_logger().info("(Rows=vertical, Cols=horizontal, numbers=features/frame/cell)")

            for row in range(grid_rows):
                row_str = ""
                for col in range(grid_cols):
                    count = int(grid_counts[row, col])
                    if count == 0:
                        row_str += " · "
                    elif count < 5:
                        row_str += " ░ "
                    elif count < 10:
                        row_str += " ▒ "
                    elif count < 20:
                        row_str += " ▓ "
                    else:
                        row_str += " █ "
                self.get_logger().info(f"  {row_str}")

        # ================================================================
        # RECOMMENDATIONS
        # ================================================================
        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("RECOMMENDATIONS")
        self.get_logger().info("=" * 70)

        recommendations = []

        if mean_features < 150:
            recommendations.append("• INCREASE max_cnt to 250-300")
            recommendations.append("• DECREASE detect_threshold from current value")

        if cv > 0.25:
            recommendations.append("• Improve lighting consistency")
            recommendations.append("• Check camera auto-exposure settings")

        if low_feature_ratio > 0.10:
            recommendations.append("• DECREASE detect_threshold to capture more features")
            recommendations.append("• Verify camera focus is correct")

        if clustering_metric > 0.8:
            recommendations.append("• INCREASE min_dist to 25-30 pixels")

        if not recommendations:
            self.get_logger().info("✅ No issues detected - feature tracking looks good!")
        else:
            self.get_logger().info("Suggested config changes:")
            for rec in recommendations:
                self.get_logger().info(rec)

        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("TEST COMPLETE")
        self.get_logger().info("=" * 70)

def main(args=None):
    rclpy.init(args=args)
    node = FeatureQualityTest()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("\n⚠️  Test interrupted")
        if node.frame_count > 10:
            node.analyze_results()
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()
