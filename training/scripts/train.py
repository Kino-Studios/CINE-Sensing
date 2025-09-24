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
       "learning_rate": 0.5,
       "steps": 100000,
       "batch_size": 50,
    }
    experiment.log_parameters(hyper_params)

    experiment.log_other("model_name", "Yolo11n")
    experiment.log_other("model_type", "YOLO11n")
    experiment.log_other("model_path", "training/checkpoints/yolo11n.pt")

    model.train(data="training/configs/HomeObjects-3K.yaml", epochs=3, imgsz=512, amp=True, batch=4)