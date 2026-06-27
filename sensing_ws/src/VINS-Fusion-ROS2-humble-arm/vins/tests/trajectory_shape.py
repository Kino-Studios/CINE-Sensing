import numpy as np


def chirality(xy_points):
    """Signed enclosed area (shoelace) of a 2D path.

    Sign encodes handedness: it flips under a mirror reflection but is invariant
    under rotation and translation. Used to detect a mirrored VIO trajectory when
    comparing IMU axis-remap variants on the figure-8 motion segment.
    """
    p = np.asarray(xy_points, dtype=float)
    x = p[:, 0]
    y = p[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
