import os
import shutil
from ultralytics import YOLO

model = YOLO("/home/vtsyp/CINE-Sensing/training/checkpoints/pre-export/homeobjects_yolo11n_trained.pt")

model_export_path = model.export(format="edgetpu")

edgetpu_model_path = model_export_path.replace('_saved_model', '_saved_model/homeobjects_yolo11n_trained_full_integer_quant_edgetpu.tflite')
export_destination = "/home/vtsyp/CINE-Sensing/training/checkpoints/exports/homeobjects_yolo11n_edgetpu.tflite"

shutil.copy2(edgetpu_model_path, export_destination)
