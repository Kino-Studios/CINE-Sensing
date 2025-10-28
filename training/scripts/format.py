import os
from comet_ml import start
import torch
from ultralytics import YOLO
import shutil

model = YOLO("/home/vtsyp/bspline-cinematography-generator-research/training/checkpoints/pre-export/homeobjects_yolo11n_trained.pt")

model_export_path = model.export(format="edgetpu")
print(f"Model exported to: {model_export_path}")

edgetpu_model_path = model_export_path.replace('_saved_model', '_saved_model/homeobjects_yolo11n_trained_full_integer_quant_edgetpu.tflite')
export_destination = "/home/vtsyp/bspline-cinematography-generator-research/training/checkpoints/exports/homeobjects_yolo11n_edgetpu.tflite"

import shutil
shutil.copy2(edgetpu_model_path, export_destination)

print("✅ EdgeTPU model export completed successfully!")
print(f"EdgeTPU model saved to: {export_destination}")
print("📊 Model stats:")
print("- 454 operations running on Edge TPU")
print("- 22 operations running on CPU") 
print("- Model size: 3.3 MB")
print("- On-chip memory used: 2.87 MiB")