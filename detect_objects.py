import os
import cv2
from ultralytics import YOLO

def detect_and_save(model_path, image_path, output_path, classes=None):
    """
    Load model, run inference on image, and save annotated result.
    """
    print(f"Processing {image_path}...")

    # Load model
    model = YOLO(model_path)

    # Run inference
    # If classes is None, detects all classes.
    results = model(image_path, classes=classes, conf=0.1)

    # Save the annotated image
    # results is a list, we take the first item
    res = results[0]

    # Filter detections: keep only one (highest confidence) instance per class
    boxes = res.boxes
    if len(boxes) > 0:
        print(f"Original boxes: {len(boxes)}")
        best_indices = {}
        for idx, (cls_id, conf) in enumerate(zip(boxes.cls.cpu().numpy(), boxes.conf.cpu().numpy())):
            cls_id = int(cls_id)
            if cls_id not in best_indices or conf > boxes.conf.cpu().numpy()[best_indices[cls_id]]:
                best_indices[cls_id] = idx

        # Update the result object with filtered boxes
        selected_indices = list(best_indices.values())
        res.boxes = boxes[selected_indices]
        print(f"Filtered boxes: {len(res.boxes)}")

    # Save the plotted image
    res.save(filename=output_path)
    print(f"Saved result to {output_path}")

def main():
    # Paths
    project_root = "/home/fishnos/CINE-Sensing"
    model_path = os.path.join(project_root, "training/checkpoints/pre-export/homeobjects_yolo11n_trained.pt")
    input_dir = os.path.join(project_root, "sensing_ws")
    output_dir = os.path.join(project_root, "yolo_output")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory {output_dir}")

    # Task 1: oof.jpg - Chair only (ID 2)
    oof_input = os.path.join(input_dir, "oof.jpg")
    oof_output = os.path.join(output_dir, "detected_oof_chair.jpg")
    detect_and_save(model_path, oof_input, oof_output, classes=[2])

    # Task 2: takeoff.jpg - All objects
    takeoff_input = os.path.join(input_dir, "takeoff.jpg")
    takeoff_output = os.path.join(output_dir, "detected_takeoff_all.jpg")
    detect_and_save(model_path, takeoff_input, takeoff_output, classes=[0, 2, 7, 8, 11])

if __name__ == "__main__":
    main()
