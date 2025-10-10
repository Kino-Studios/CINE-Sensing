import os
from comet_ml import start
import torch
from ultralytics import YOLO

if __name__ == '__main__':
    model = YOLO("training/checkpoints/yolo11n.pt")

    # Get API key from environment variable
    api_key = os.getenv("COMET_API_KEY", "")
    
    experiment = start(
      api_key=api_key,
      project_name="bspline-cinematography-generator-research-llm",
      workspace="fishnos"
    )

    hyper_params = {
       "learning_rate": 0.0001,
       "steps": 100000,
       "batch_size": 16,
    }
    experiment.log_parameters(hyper_params)

    experiment.log_other("model_name", "Yolo11n")
    experiment.log_other("model_type", "YOLO11n")
    experiment.log_other("model_path", "training/checkpoints/yolo11n.pt")

    model.train(
      data="training/configs/HomeObjects-3K.yaml", 
      epochs=100, 
      imgsz=640, 
      amp=False, 
      batch=4,
      lr0=0.0001,
      project="training/runs",
      name="yolo11n-homeobjects-3k",
      cos_lr=True,
      optimizer="AdamW",
      save=True,
    )