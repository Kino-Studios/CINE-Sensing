import os
import sys
import subprocess
import cv2
import numpy as np
from ultralytics import YOLO

project_root = os.path.expanduser('~/CINE-Sensing')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from configs.python import CameraConfig


def capture_grayscale_photo(output_path, timeout_ms=10000):
    temp_path = output_path + ".tmp.png"

    cmd = [
        'rpicam-still',
        '--timeout', str(timeout_ms),
        '--width', str(CameraConfig.IMAGE_WIDTH),
        '--height', str(CameraConfig.IMAGE_HEIGHT),
        '--nopreview',
        '-o', temp_path,
    ]

    print(f"Capturing photo with {timeout_ms}ms timeout...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"rpicam-still failed: {result.stderr}")
        return False

    frame = cv2.imread(temp_path)
    if frame is None:
        print(f"Failed to read captured image: {temp_path}")
        return False

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(output_path, gray_frame)

    if os.path.exists(temp_path):
        os.remove(temp_path)

    print(f"Saved grayscale photo to {output_path}")
    return True


def detect_and_save(model_path, image_path, output_path, classes=None):
    print(f"Processing {image_path}...")

    model = YOLO(model_path)
    results = model(image_path, classes=classes, conf=0.1)
    res = results[0]
    boxes = res.boxes
    if len(boxes) > 0:
        print(f"Original boxes: {len(boxes)}")
        best_indices = {}

        for idx, (cls_id, conf) in enumerate(zip(boxes.cls.cpu().numpy(), boxes.conf.cpu().numpy())):
            cls_id = int(cls_id)
            if cls_id not in best_indices or conf > boxes.conf.cpu().numpy()[best_indices[cls_id]]:
                best_indices[cls_id] = idx

        selected_indices = list(best_indices.values())
        res.boxes = boxes[selected_indices]
        print(f"Filtered boxes: {len(res.boxes)}")
    res.save(filename=output_path)
    print(f"Saved result to {output_path}")


def main():
    model_path = os.path.join(project_root, "training/checkpoints/pre-export/homeobjects_yolo11n_trained.pt")
    output_dir = os.path.join(project_root, "yolo_output")
    capture_dir = os.path.join(project_root, "yolo_output", "captures")

    for d in [output_dir, capture_dir]:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"Created directory {d}")

    photo1_path = os.path.join(capture_dir, "capture_1.png")
    photo2_path = os.path.join(capture_dir, "capture_2.png")

    print("capturing photo 1")
    if not capture_grayscale_photo(photo1_path, timeout_ms=10000):
        print("Failed to capture photo 1, exiting.")
        return

    print("\ncapturing photo 2")
    if not capture_grayscale_photo(photo2_path, timeout_ms=10000):
        print("Failed to capture photo 2, exiting.")
        return

    print("\nrunning detect on photo 1")
    detect_output1 = os.path.join(output_dir, "detected_capture_1.jpg")
    detect_and_save(model_path, photo1_path, detect_output1, classes=[2])

    print("\nrunning detect on photo 2")
    detect_output2 = os.path.join(output_dir, "detected_capture_2.jpg")
    detect_and_save(model_path, photo2_path, detect_output2, classes=[2])

    print("\ndone")
    print(f"grayscale captures: {photo1_path}, {photo2_path}")
    print(f"detection results:  {detect_output1}, {detect_output2}")


if __name__ == "__main__":
    main()
