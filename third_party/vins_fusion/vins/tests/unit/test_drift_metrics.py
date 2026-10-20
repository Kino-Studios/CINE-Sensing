import numpy as np
from drift_metrics import append_results_row, compute_drift_metrics


def test_zero_motion_is_excellent():
    pos = np.zeros((10, 3))
    vel = np.zeros((10, 3))
    m = compute_drift_metrics(pos, vel, duration_s=30.0)
    assert m["final_drift_m"] == 0.0
    assert m["mean_vel_m_s"] == 0.0
    assert m["verdict"] == "excellent"


def test_one_meter_drift_buckets_to_poor():
    pos = np.zeros((2, 3))
    pos[1] = [1.0, 0.0, 0.0]
    vel = np.zeros((2, 3))
    m = compute_drift_metrics(pos, vel, duration_s=30.0)
    assert abs(m["final_drift_m"] - 1.0) < 1e-9
    assert abs(m["drift_rate_cm_s"] - (100.0 / 30.0)) < 1e-6
    assert m["verdict"] == "poor"


def test_append_writes_header_then_row(tmp_path):
    csv = tmp_path / "results.csv"
    m = compute_drift_metrics(np.zeros((2, 3)), np.zeros((2, 3)), 30.0)
    append_results_row(str(csv), "baseline", m)
    append_results_row(str(csv), "A2_remap", m)
    lines = csv.read_text().strip().splitlines()
    assert lines[0].startswith("label,final_drift_m")
    assert lines[1].startswith("baseline,")
    assert lines[2].startswith("A2_remap,")
    assert len(lines) == 3  # header + 2 rows


def test_append_records_the_config_profile_of_the_run(tmp_path):
    csv = tmp_path / "results.csv"
    m = compute_drift_metrics(np.zeros((2, 3)), np.zeros((2, 3)), 30.0)
    append_results_row(str(csv), "tuned", m, profile="rpi_v3_tune_maxcnt250")
    header, row = csv.read_text().strip().splitlines()
    assert header.endswith(",verdict,profile")
    assert row.endswith(",excellent,rpi_v3_tune_maxcnt250")
