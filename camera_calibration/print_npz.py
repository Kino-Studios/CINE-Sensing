import numpy as np
import os

data = np.load('/home/fishnos/CINE-Sensing/camera_calibration/calib_data/calibration.npz')
print("Calibration Data:")
for key in data.files:
    print(f"{key}: {data[key]}")

data.close()
