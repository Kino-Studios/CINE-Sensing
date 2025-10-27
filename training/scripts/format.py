import os
from comet_ml import start
import torch
from ultralytics import YOLO

model = YOLO("training/checkpoints/pre-export/homeobjects_yolo11n_trained.pt")

model_export = model.export(format="edgetpu")
model_export.save("training/checkpoints/exports/homeobjects_yolo11n_pretrained.tflite")

edgetpu_model = YOLO("training/checkpoints/exports/homeobjects_yolo11n_pretrained.tflite")

results = edgetpu_model("https://ultralytics.com/images/bus.jpg")