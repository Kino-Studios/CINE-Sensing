#!/usr/bin/env python3
"""Camera calibration using OpenCV chessboard detection."""

import glob
import logging
import os

import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
_log = logging.getLogger(__name__)


def calibrate(shows_pics=True):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    calibration_path = os.path.join(script_dir, "images")
    images = glob.glob(os.path.join(calibration_path, "*.jpg"))

    print(f"Calibration path: {calibration_path}")
    print(f"Found {len(images)} images")

    if not images:
        _log.error("No images found in calibration/images directory")
        return None, None

    n_rows = 9  # 10 boxes
    n_cols = 6  # 7 boxes
    term_criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    world_points = np.zeros((n_rows * n_cols, 3), np.float32)
    world_points[:, :2] = np.mgrid[0:n_rows, 0:n_cols].T.reshape(-1, 2)

    world_points_list = []
    image_points_list = []
    image_shape = None
    successful_images = 0

    for fname in images:
        img = cv.imread(fname)
        if img is None:
            _log.warning("Could not read image %s", fname)
            continue

        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        corners_found, corners_org = cv.findChessboardCorners(img_gray, (n_rows, n_cols), None)

        if corners_found:
            successful_images += 1
            world_points_list.append(world_points.copy())
            corners_refined = cv.cornerSubPix(
                img_gray, corners_org, (11, 11), (-1, -1), term_criteria
            )
            image_points_list.append(corners_refined)
            if image_shape is None:
                image_shape = img_gray.shape[::-1]

            if shows_pics:
                cv.drawChessboardCorners(img, (n_rows, n_cols), corners_refined, corners_found)
                cv.imshow("Chessboard", img)
                cv.waitKey(500)
        else:
            print(f"No chessboard found in {os.path.basename(fname)}")

    cv.destroyAllWindows()

    print(f"Successfully detected chessboard in {successful_images}/{len(images)} images")

    if successful_images == 0:
        _log.error("No chessboards detected. Check image quality and chessboard dimensions.")
        return None, None

    (
        rep_error,
        camera_matrix,
        distort_coeff,
        rot_vecs,
        translation_vecs,
    ) = cv.calibrateCamera(world_points_list, image_points_list, image_shape, None, None)

    calib_data_dir = os.path.join(script_dir, "calib_data")
    os.makedirs(calib_data_dir, exist_ok=True)
    param_path = os.path.join(calib_data_dir, "calibration.npz")
    np.savez(
        param_path,
        rep_error=rep_error,
        camera_matrix=camera_matrix,
        distort_coeff=distort_coeff,
        rot_vecs=rot_vecs,
        translation_vecs=translation_vecs,
    )

    return camera_matrix, distort_coeff


def run_calibration():
    calibrate(shows_pics=False)


def remove_distortion(camera_matrix, distort_coeff):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "images", "*.jpg")
    images = glob.glob(image_path)

    if not images:
        return

    image = cv.imread(images[0])

    height, width = image.shape[:2]
    new_camera_matrix = cv.getOptimalNewCameraMatrix(
        camera_matrix, distort_coeff, (width, height), 1, (width, height)
    )
    img_undistorted = cv.undistort(image, camera_matrix, distort_coeff, None, new_camera_matrix)

    cv.line(image, (1769, 103), (1780, 922), (255, 255, 255), 2)
    cv.line(img_undistorted, (1769, 103), (1780, 922), (255, 255, 255), 2)

    plt.figure()
    plt.subplot(121)
    plt.imshow(image)
    plt.subplot(122)
    plt.imshow(img_undistorted)
    plt.show()


if __name__ == "__main__":
    run_calibration()
