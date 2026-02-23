import numpy as np
import os

# Use relative path to the calibration data
script_dir = os.path.dirname(os.path.abspath(__file__))
calib_file = os.path.join(script_dir, 'calib_data', 'calibration.npz')

# Load the data with allow_pickle=False for security
data = np.load(calib_file, allow_pickle=False)
print("Calibration Data:")
for key in data.files:
    print(f"{key}: {data[key]}")

data.close()
