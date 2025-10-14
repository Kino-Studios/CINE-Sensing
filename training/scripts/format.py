import os
from comet_ml import start
import torch
from ultralytics import YOLO

model = YOLO("runs/detect/train34/weights/best.pt")

model_export = model.export(format="tflite", int8=True)
model_export.save("training/checkpoints/exports/home_object_detection.tflite")