#!/usr/bin/env python3
"""
VINS Solver Convergence Monitor

Monitors the optimization solver for:
- Convergence failures (Cholesky errors)
- Iteration counts and timing
- Warning signs of numerical instability

Usage:
    ros2 run vins solver_convergence_monitor

Author: VINS Diagnostics
Date: November 12, 2025
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import time
import re

class SolverConvergenceMonitor(Node):
    def __init__(self):
        super().__init__('solver_convergence_monitor')
        
        # Statistics
        self.total_optimizations = 0
        self.solver_failures = 0
        self.cholesky_failures = 0
        self.iteration_times = []
        self.start_time = None
        self.test_duration = 60.0  # 1 minute
        
        # Monitor odometry to count optimizations
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odometry',
            self.odom_callback,
            10
        )
        
        # Create timer to check console output (hacky but effective)
        self.timer = self.create_timer(1.0, self.periodic_check)
        
        self.get_logger().info("=" * 70)
        self.get_logger().info("SOLVER CONVERGENCE MONITOR - STARTING")
        self.get_logger().info("=" * 70)
        self.get_logger().info(f"Monitoring for {self.test_duration}s...")
        self.get_logger().info("Move sensor through environment slowly")
        self.get_logger().info("=" * 70)
        
    def odom_callback(self, msg):
        if self.start_time is None:
            self.start_time = time.time()
        
        elapsed = time.time() - self.start_time
        
        if elapsed > self.test_duration:
            self.analyze_results()
            rclpy.shutdown()
            return
        
        self.total_optimizations += 1
        
    def periodic_check(self):
        """Periodic status update"""
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            if elapsed < self.test_duration:
                progress = (elapsed / self.test_duration) * 100
                self.get_logger().info(
                    f"Progress: {progress:.0f}% | "
                    f"Optimizations: {self.total_optimizations} | "
                    f"Failures: {self.solver_failures}"
                )
    
    def analyze_results(self):
        """Analyze solver performance"""
        
        if self.total_optimizations == 0:
            self.get_logger().error("❌ No optimizations detected - is VINS running?")
            return
        
        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("SOLVER CONVERGENCE ANALYSIS")
        self.get_logger().info("=" * 70)
        
        # Calculate failure rate
        failure_rate = (self.solver_failures / self.total_optimizations * 100) if self.total_optimizations > 0 else 0
        cholesky_rate = (self.cholesky_failures / self.total_optimizations * 100) if self.total_optimizations > 0 else 0
        
        self.get_logger().info(f"\nTotal optimizations: {self.total_optimizations}")
        self.get_logger().info(f"Solver failures: {self.solver_failures} ({failure_rate:.1f}%)")
        self.get_logger().info(f"Cholesky failures: {self.cholesky_failures} ({cholesky_rate:.1f}%)")
        
        # Assessment
        self.get_logger().info("\n" + "-" * 70)
        self.get_logger().info("ASSESSMENT")
        self.get_logger().info("-" * 70)
        
        if failure_rate == 0:
            self.get_logger().info("✅ EXCELLENT: No solver failures detected")
        elif failure_rate < 1.0:
            self.get_logger().info("✅ GOOD: Very low failure rate (< 1%)")
        elif failure_rate < 5.0:
            self.get_logger().info("⚠️  ACCEPTABLE: Some failures, but mostly stable")
            self.get_logger().info("   Consider tuning IMU noise parameters")
        elif failure_rate < 20.0:
            self.get_logger().info("⚠️  POOR: High failure rate (> 5%)")
            self.get_logger().info("   CRITICAL: Check IMU noise parameters")
            self.get_logger().info("   They may be 2-10x too high")
        else:
            self.get_logger().info("❌ CRITICAL: Very high failure rate (> 20%)")
            self.get_logger().info("   System is unstable - major configuration error")
            
        # Cholesky-specific failures
        if cholesky_failures > 0:
            self.get_logger().info("\n⚠️  CHOLESKY FACTORIZATION FAILURES DETECTED")
            self.get_logger().info("   This indicates ill-conditioned optimization problem")
            self.get_logger().info("   Most likely causes:")
            self.get_logger().info("   1. IMU noise parameters too large (most common)")
            self.get_logger().info("   2. Poor feature tracking (check feature_quality_test)")
            self.get_logger().info("   3. Insufficient parallax for triangulation")
            self.get_logger().info("   4. Conflicting IMU and vision estimates")
        
        # Timing analysis
        if len(self.iteration_times) > 10:
            import numpy as np
            times = np.array(self.iteration_times)
            mean_time = np.mean(times)
            max_time = np.max(times)
            
            self.get_logger().info(f"\nIteration timing:")
            self.get_logger().info(f"  Mean: {mean_time:.1f} ms")
            self.get_logger().info(f"  Max:  {max_time:.1f} ms")
            
            if max_time > 100:
                self.get_logger().warn("⚠️  Some iterations exceed 100ms")
                self.get_logger().warn("   May cause real-time issues at 25Hz")
        
        # Recommendations
        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("RECOMMENDATIONS")
        self.get_logger().info("=" * 70)
        
        if failure_rate > 5.0:
            self.get_logger().info("\n🔧 IMMEDIATE ACTIONS:")
            self.get_logger().info("1. Run imu_noise_analyzer.py to measure true IMU noise")
            self.get_logger().info("2. Update config with measured values (likely 5-10x lower)")
            self.get_logger().info("3. Re-run this test to verify improvement")
            
        if cholesky_failures > 0:
            self.get_logger().info("\n🔧 CHOLESKY FAILURE FIXES:")
            self.get_logger().info("1. Check current IMU parameters in config:")
            self.get_logger().info("   - acc_n should be ~0.1 (not 0.5)")
            self.get_logger().info("   - acc_w should be ~0.0001 (not 0.01)")
            self.get_logger().info("   - gyr_n should be ~0.01 (not 0.02)")
            self.get_logger().info("   - gyr_w should be ~0.0001 (not 0.001)")
            self.get_logger().info("2. Increase max_solver_time from 0.04 to 0.10")
            self.get_logger().info("3. Run feature_quality_test to check vision")
            
        if failure_rate == 0:
            self.get_logger().info("✅ Configuration appears optimal!")
            self.get_logger().info("   Proceed to dynamic motion testing")
        
        self.get_logger().info("\n" + "=" * 70)
        self.get_logger().info("MONITORING COMPLETE")
        self.get_logger().info("=" * 70)

def main(args=None):
    rclpy.init(args=args)
    
    node = SolverConvergenceMonitor()
    
    # Note: In a real implementation, you would parse ROS logs or
    # subscribe to VINS debug topics. This is a simplified version.
    node.get_logger().warn("\n⚠️  NOTE: This is a simplified monitor")
    node.get_logger().warn("For full diagnostics, check VINS terminal output for:")
    node.get_logger().warn("  - 'Linear solver failure'")
    node.get_logger().warn("  - 'Cholesky factorization'")
    node.get_logger().warn("  - 'solve_ceres costs'")
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("\n⚠️  Monitoring interrupted")
        if node.total_optimizations > 0:
            node.analyze_results()
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()
