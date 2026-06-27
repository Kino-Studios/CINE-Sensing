import csv
import os

import numpy as np

_FIELDS = ["label", "final_drift_m", "drift_rate_cm_s", "mean_vel_m_s", "max_vel_m_s", "verdict"]


def _verdict(final_drift_m):
    if final_drift_m < 0.05:
        return "excellent"
    if final_drift_m < 0.2:
        return "good"
    if final_drift_m < 0.5:
        return "acceptable"
    if final_drift_m < 2.0:
        return "poor"
    return "fail"


def compute_drift_metrics(positions, velocities, duration_s):
    positions = np.asarray(positions, dtype=float)
    velocities = np.asarray(velocities, dtype=float)

    start = positions[0]
    drift_per_sample = np.linalg.norm(positions - start, axis=1)
    final_drift = float(drift_per_sample[-1])
    max_drift = float(np.max(drift_per_sample))

    speed = np.linalg.norm(velocities, axis=1)

    return {
        "final_drift_m": final_drift,
        "max_drift_m": max_drift,
        "drift_rate_cm_s": final_drift / duration_s * 100.0,
        "mean_vel_m_s": float(np.mean(speed)),
        "max_vel_m_s": float(np.max(speed)),
        "verdict": _verdict(final_drift),
    }


def append_results_row(csv_path, label, metrics):
    new_file = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)

    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(_FIELDS)
        writer.writerow([
            label,
            f"{metrics['final_drift_m']:.4f}",
            f"{metrics['drift_rate_cm_s']:.2f}",
            f"{metrics['mean_vel_m_s']:.4f}",
            f"{metrics['max_vel_m_s']:.4f}",
            metrics["verdict"],
        ])
