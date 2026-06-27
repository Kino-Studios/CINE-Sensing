#!/usr/bin/env python3
import argparse
import os
import sys

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import numpy as np
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drift_metrics import append_results_row, compute_drift_metrics


class StaticDriftTest(Node):
    def __init__(self, duration_s, label, results_csv):
        super().__init__('static_drift_test')
        self.duration_s = duration_s
        self.label = label
        self.results_csv = results_csv
        self.positions = []
        self.velocities = []
        self.start_time = None
        self.start_position = None

        self.odom_sub = self.create_subscription(Odometry, '/odometry', self.odom_cb, 10)
        
    def odom_cb(self, msg):
        if self.start_time is None:
            self.start_time = time.time()
            self.start_position = np.array([
                msg.pose.pose.position.x,
                msg.pose.pose.position.y,
                msg.pose.pose.position.z
            ])
            print("\n" + "="*60)
            print("STATIC DRIFT TEST")
            print("="*60)
            print(f"Keep sensor COMPLETELY STILL for {self.duration_s:.0f} seconds")
            print("="*60 + "\n")
            return
        
        elapsed = time.time() - self.start_time
        
        pos = np.array([
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z
        ])
        
        vel = np.array([
            msg.twist.twist.linear.x,
            msg.twist.twist.linear.y,
            msg.twist.twist.linear.z
        ])
        
        self.positions.append(pos)
        self.velocities.append(vel)
        
        if int(elapsed) % 5 == 0 and len(self.positions) > 0:
            drift = np.linalg.norm(pos - self.start_position)
            vel_mag = np.linalg.norm(vel)
            print(f"[{elapsed:.1f}s] Drift: {drift:.4f}m, Velocity: {vel_mag:.4f}m/s")
        
        if elapsed > self.duration_s:
            self.analyze_results()
            rclpy.shutdown()
    
    def analyze_results(self):
        if len(self.positions) == 0:
            print("No odometry received — is /odometry publishing?")
            return

        positions = [self.start_position] + self.positions
        metrics = compute_drift_metrics(positions, self.velocities, self.duration_s)

        print("\n" + "=" * 60)
        print(f"STATIC DRIFT TEST RESULTS ({self.duration_s:.0f}s) — label={self.label}")
        print("=" * 60)
        print(f"Final drift:   {metrics['final_drift_m']:.4f} m")
        print(f"Max drift:     {metrics['max_drift_m']:.4f} m")
        print(f"Drift rate:    {metrics['drift_rate_cm_s']:.2f} cm/s")
        print(f"Mean velocity: {metrics['mean_vel_m_s']:.4f} m/s")
        print(f"Max velocity:  {metrics['max_vel_m_s']:.4f} m/s")
        print(f"Verdict:       {metrics['verdict'].upper()}")
        append_results_row(self.results_csv, self.label, metrics)
        print(f"Appended row to {self.results_csv}")
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=float, default=30.0)
    parser.add_argument('--label', type=str, default='baseline')
    parser.add_argument('--results-csv', type=str, default='vins_output/drift_results.csv')
    args, _ = parser.parse_known_args()

    rclpy.init()
    node = StaticDriftTest(args.duration, args.label, args.results_csv)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass

if __name__ == '__main__':
    main()
