import os
from comet_ml import start
import torch
from ultralytics import YOLO

if __name__ == '__main__':
    # model = YOLO("training/checkpoints/yolo11n.pt")
    model = YOLO("training/checkpoints/yolo11n.pt")

    # Get API key from environment variable
    api_key = os.getenv("COMET_API_KEY", "")
    
    experiment = start(
      api_key=api_key,
      project_name="bspline-cinematography-generator-research-llm",
      workspace="fishnos"
    )

    learning_rate = 0.0001
    batch_size = 8  # reduced to avoid memory issues
    epochs = 20
    imgsz = 640
    lr0 = 0.0001
    lrf = 0.1
    cos_lr = False
    optimizer = "AdamW"
    patience = 5
    pretrained = True
    device = "mps" # change if windows
    save_period = 3
    project = "runs/detect"
    search_space = {
      "lr0": (1e-4, 1e-2),     
      "lrf": (0.01, 0.1),       
      "warmup_epochs": (1.0, 3.0), 
      "momentum": (0.8, 0.95),
      "weight_decay": (1e-4, 1e-3) 
    }

    hyper_params = {
       "steps": 100000,
       "batch_size": batch_size,
       "epochs": epochs,
       "imgsz": imgsz,
       "lr0": lr0,
       "lrf": lrf,
       "cos_lr": cos_lr,
       "optimizer": optimizer,
       "patience": patience,
       "pretrained": pretrained,
       "device": device,
       "save_period": save_period,
       "project": project,
    }
    experiment.log_parameters(hyper_params)

    # try to make a small model and use that instead
    experiment.log_other("model_name", "Yolo11n")
    experiment.log_other("model_type", "YOLO11n")
    experiment.log_other("model_path", "training/checkpoints/yolo11n.pt")

    results=model.tune(
      data="training/configs/HomeObjects-3K.yaml",
      resume=False,
      epochs=epochs,
      imgsz=imgsz,
      batch=batch_size,
      lr0=lr0,
      lrf=lrf,
      cos_lr=cos_lr,
      optimizer=optimizer,
      patience=patience,
      pretrained=pretrained,
      device=device,
      save_period=save_period,
      project=project,
      amp=True,
      cache=False,
      val=False,
      plots=False,
      save=False
    )