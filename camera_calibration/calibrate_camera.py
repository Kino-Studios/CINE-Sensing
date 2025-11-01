import numpy as np
import cv2 as cv
import glob
import matplotlib.pyplot as plt
import os

def calibrate(showsPics=True):
    root = os.getcwd()
    calibration_path = os.path.join(root, 'images')
    images = glob.glob(os.path.join(calibration_path, '*.jpg'))

    n_rows = 9 # 10 boxes
    n_cols = 6 # 7 boxes
    term_criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    world_points = np.zeros((n_rows * n_cols, 3), np.float32)
    world_points[:, :2] = np.mgrid[0:n_rows, 0:n_cols].T.reshape(-1, 2)

    world_points_list = []
    image_points_list = []

    for fname in images:
        img = cv.imread(fname)
        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        corners_found, corners_org = cv.findChessboardCorners(img_gray, (n_rows, n_cols), None)

        if corners_found:
            world_points_list.append(world_points)
            corners_refined = cv.cornerSubPix(img_gray, corners_org, (11, 11), (-1, -1), term_criteria)
            image_points_list.append(corners_refined)

            if showsPics:
                cv.drawChessboardCorners(img, (n_rows, n_cols), corners_refined, corners_found)
                cv.imshow('Chessboard', img)
                cv.waitKey(500)
    
    cv.destroyAllWindows()

    # calibrate
    rep_error, camera_matrix, distort_coeff, rot_vecs, translation_vecs, = cv.calibrateCamera(
        world_points_list, image_points_list, img_gray.shape[::-1], None, None
    )

    # save params
    curr_folder = os.path.dirname(os.path.abspath(__file__))
    param_path = os.path.join(curr_folder, 'calib_data', 'calibration.npz')
    np.savez(param_path,
            rep_error=rep_error,
            camera_matrix=camera_matrix,
            distort_coeff=distort_coeff,
            rot_vecs=rot_vecs,
            translation_vecs=translation_vecs)

    return camera_matrix, distort_coeff

def run_calibration():
    calibrate(showsPics=False)

def remove_distortion(camera_matrix, distort_coeff):
    root = os.getcwd()
    image_path = os.path.join(root, 'images/*.jpg')
    image = cv.imread(image_path)

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