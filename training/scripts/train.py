import os
from comet_ml import start
import torch
from ultralytics import YOLO

if __name__ == '__main__':
    # model = YOLO("training/checkpoints/pretrained/yolo11n.pt")
    model = YOLO("runs/detect/train34/weights/best.pt")

    api_key = os.getenv("COMET_API_KEY", "")
    
    experiment = start(
      api_key=api_key,
      project_name="bspline-cinematography-generator-research-llm",
      workspace="fishnos"
    )

    workers = 4
    batch_size = 4  # reduced to avoid memory issues
    epochs = 15
    fraction = 1.0
    imgsz = 640
    lr0 = 0.0001
    lrf = 0.01
    hsv_v = 0.5
    hsv_s = 0.7
    cos_lr = True
    optimizer = "AdamW"
    close_mosaic = 5
    patience = 5
    warmup_epochs = 1.0
    pretrained = False
    resume = False
    device = "mps" # change if windows
    save_period = 3
    freeze = 3
    rect = False
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
       "hsv_v": hsv_v,
       "hsv_s": hsv_s,
       "lr0": lr0,
       "lrf": lrf,
       "seed": seed,
       "cos_lr": cos_lr,
       "warmup_epochs": warmup_epochs,
       "close_mosaic": close_mosaic,
       "optimizer": optimizer,
       "patience": patience,
       "pretrained": pretrained,
       "resume": resume,
       "device": device,
       "save_period": save_period,
       "project": project,
       "rect": rect,
    }
    experiment.log_parameters(hyper_params)

    # try to make a small model and use that instead
    experiment.log_other("model_name", "Yolo11n")
    experiment.log_other("model_type", "YOLO11n")
    experiment.log_other("model_path", "training/checkpoints/pretrained/yolo11n.pt")

    results=model.train(
      data="training/configs/HomeObjects-3K.yaml",
      resume=resume,
      fraction=fraction,
      epochs=epochs,
      imgsz=imgsz,
      batch=batch_size,
      workers=workers,
      hsv_v=hsv_v,
      hsv_s=hsv_s,
      seed=seed,
      lr0=lr0,
      lrf=lrf,
      warmup_epochs=warmup_epochs,
      close_mosaic=close_mosaic,
      cos_lr=cos_lr,
      optimizer=optimizer,
      patience=patience,
      pretrained=pretrained,
      device=device,
      save_period=save_period,
      project=project,
      freeze=freeze,
      amp=True,
      cache=True,
      rect=rect,
      val=True,
      plots=True,
      save=True
    )