import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trajectory_shape import chirality


def test_sign_flips_under_mirror_not_rotation():
    # A simple CCW square has positive signed area.
    sq = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
    assert chirality(sq) > 0
    # Mirror across the y-axis (x -> -x): sign must flip.
    mirrored = sq * np.array([-1.0, 1.0])
    assert chirality(mirrored) < 0
    # 90-degree rotation: sign must NOT flip.
    rot = sq @ np.array([[0.0, -1.0], [1.0, 0.0]])
    assert chirality(rot) > 0
