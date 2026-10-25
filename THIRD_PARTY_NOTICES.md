# Third-party notices

CINE-Sensing is distributed under the GNU General Public License v3.0 (`LICENSE`).
It contains, builds against, or downloads the third-party work listed below. Each
entry names the licence and where its full text lives.

## Code shipped in this repository

| Component | Licence | Location | Notes |
| --- | --- | --- | --- |
| VINS-Fusion (HKUST Aerial Robotics Group) | GPL-3.0 | `third_party/vins_fusion/`, licence in `third_party/vins_fusion/LICENCE` | Modified; every change is listed in `third_party/vins_fusion/UPSTREAM.md`. |
| DBoW2 (Dorian Galvez-Lopez) | BSD-style with a notification clause | `third_party/vins_fusion/loop_fusion/src/ThirdParty/`, licence in `LICENSE.DBoW2` there | Bundled by VINS-Fusion for loop closure. Its author has been notified of this redistribution, as clause 3 of its licence requires. |
| OpenVINS camera classes (Robot Perception and Navigation Group) | GPL-3.0-or-later | `third_party/vins_fusion/camera_models/include/camera_models/open_vins/`, licence in `third_party/vins_fusion/camera_models/LICENSE.open_vins` | Replaced the camodocal camera library (CC-BY-SA 2.0) on 2026-10-16. |
| GeographicLib (Charles Karney) | MIT | `third_party/vins_fusion/global_fusion/ThirdParty/GeographicLib/`, licence in `LICENSE.txt` there | Bundled by VINS-Fusion for global fusion. |

## Built or downloaded, not shipped

| Component | Licence | How it arrives |
| --- | --- | --- |
| Ceres Solver 2.1.0 | BSD-3-Clause | Built from the upstream tarball by `tools/install_ceres_2_1.sh`. |
| Ultralytics YOLO | AGPL-3.0 | Installed from PyPI (`requirements.txt`). |
| YOLO11n detector weights (`yolo11n.pt`) | AGPL-3.0 (Ultralytics) | Downloaded by Ultralytics itself on first use; not redistributed here. |
| HomeObjects-3K dataset (Ultralytics) | AGPL-3.0 | Not shipped or downloaded; used only to train the project's own detector weights, which are not distributed. |
| VINS-Fusion data files (`brief_k10L6.bin`, `car.dae`, `hummingbird.mesh`) | GPL-3.0, as part of VINS-Fusion | Downloaded by `tools/download_assets.py` from this project's GitHub Release. |

Citations for these works are in `references.bib`.
