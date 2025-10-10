import os
from comet_ml import start
import torch
from ultralytics import YOLO

if __name__ == '__main__':
    # model = YOLO("training/checkpoints/yolo11n.pt")
    model = YOLO("runs/detect/train7/weights/last.pt")

    # Get API key from environment variable
    api_key = os.getenv("COMET_API_KEY", "")
    
    experiment = start(
      api_key=api_key,
      project_name="bspline-cinematography-generator-research-llm",
      workspace="fishnos"
    )

    hyper_params = {
       "learning_rate": 0.01,
       "steps": 100000,
       "batch_size": 4,
    }
    experiment.log_parameters(hyper_params)

    experiment.log_other("model_name", "Yolo11n")
    experiment.log_other("model_type", "YOLO11n")
    experiment.log_other("model_path", "training/checkpoints/yolo11n.pt")

    model.train(
      data="training/configs/HomeObjects-3K.yaml",
      epochs=60,
      resume=False,
      batch=8,
      lr0=0.008,
      lrf=0.2,
      cos_lr=False,
      optimizer="AdamW",
      patience=15,
      amp=True,
      device="mps",
      workers=0,
      mosaic=0.10, mixup=0.0, translate=0.10, scale=0.5,
      hsv_h=0.015, hsv_s=0.7, hsv_v=0.4, fliplr=0.5,
      project="runs/detect", name="train7_continue"  # new folder
    )