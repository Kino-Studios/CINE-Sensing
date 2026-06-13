#!/usr/bin/env python3
import os
import sys
import urllib.request

GITHUB_REPO = "vtsyp/CINE-Sensing"

_version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "VERSION")
RELEASE_TAG = "v" + open(_version_file).read().strip()

MODELS = [
    "homeobjects_yolo11n_trained.pt",
]

MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sensing_ws",
    "src",
    "yolo_detection",
    "models",
)

BASE_URL = f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}"


def download(filename, dest_dir):
    url = f"{BASE_URL}/{filename}"
    dest = os.path.join(dest_dir, filename)

    if os.path.exists(dest):
        print(f"already exists, skipping: {filename}")
        return

    print(f"downloading {filename}...")
    try:

        def progress(count, block_size, total_size):
            if total_size > 0:
                pct = min(count * block_size * 100 // total_size, 100)
                sys.stdout.write(f"\r  {pct}%")
                sys.stdout.flush()

        urllib.request.urlretrieve(url, dest, reporthook=progress)
        print(f"\r  done -> {dest}")
    except Exception as e:
        if os.path.exists(dest):
            os.remove(dest)
        print(f"\r  failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    os.makedirs(MODELS_DIR, exist_ok=True)
    for model in MODELS:
        download(model, MODELS_DIR)
    print("all models ready")
