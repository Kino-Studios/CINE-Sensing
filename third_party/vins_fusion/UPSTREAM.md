# Upstream record: VINS-Fusion (ROS 2 Humble, ARM fork)

## Lineage

1. [HKUST-Aerial-Robotics/VINS-Fusion](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion),
   the original ROS 1 visual-inertial odometry system.
2. [zinuok/VINS-Fusion-ROS2](https://github.com/zinuok/VINS-Fusion-ROS2), a ROS 2 port.
3. A "humble-arm" fork of that port, aimed at ROS 2 Humble on ARM boards, which this
   directory was copied from.

The base commit of the "humble-arm" fork is **unknown**: the code was imported into this
repository as a plain copy (commit `dcba7a0`, 2026-01-03) without recording which upstream
commit it came from.

## Licence

GNU General Public License v3 (see [`LICENCE`](LICENCE)). The upstream headers in every
source file are kept unchanged.

## Modifications by Kino-Studios

Modified by Kino-Studios, 2026. This notice is given under section 5a of the GPLv3: the
files below differ from the code as imported.

| Commit    | Date       | Files changed                                                                                                                                              |
| --------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `3c384fb` | 2026-01-31 | `camera_models/CMakeLists.txt`                                                                                                                              |
| `5cf04c1` | 2026-01-31 | `vins/src/estimator/{estimator,feature_manager,parameters}.{cpp,h}`, `vins/src/featureTracker/feature_tracker.{cpp,h}`, `vins/src/rosNodeTest.cpp`, `loop_fusion/src/pose_graph_node.cpp` |
| `9de76ae` | 2026-02-06 | `package.xml` of `vins`, `loop_fusion`, `camera_models`, `global_fusion`                                                                                    |
| `0c003e2` | 2026-02-23 | `vins/src/utility/image_encodings.hpp`, `loop_fusion/src/image_encodings.hpp` (encoding matching rewritten with C++11 `std::regex`)                         |
| `3b8c1cd` | 2026-10-15 | Port to ROS 2 Jazzy: `#include <cv_bridge/cv_bridge.h>` → `cv_bridge.hpp` in `loop_fusion/src/{parameters.h,pose_graph_node.cpp}`, `vins/src/{KITTIOdomTest.cpp,rosNodeTest.cpp,utility/visualization.h}` (Jazzy ships only the `.hpp` header); `package.xml` dependencies declared by rosdep key; `global_fusion/models/car.dae` (12.7 MB) moved to a release download and `global_fusion/CMakeLists.txt` now installs `models/` |
| `3b8c1cd` | 2026-10-16 | camodocal camera library (CC-BY-SA 2.0, not GPL-3.0 compatible) replaced by OpenVINS's camera classes: deleted `camera_models/{include/camodocal/,src/{calib,camera_models,chessboard,gpl,sparse_graph}/,src/intrinsic_calib.cc,cmake/,camera_calib_example/,LICENSE.camodocal}` (including the `Calibrations` tool); added `camera_models/include/camera_models/open_vins/` (see below), `LICENSE.open_vins`, and a first-party adapter; rewrote `camera_models/{CMakeLists.txt,package.xml}`; callers switched to `camera_models::loadCameraFromYaml` in `vins/src/featureTracker/feature_tracker.{cpp,h}` and `loop_fusion/src/{keyframe.h,parameters.h,pose_graph_node.cpp}`; `loop_fusion/package.xml` now declares `boost` itself (its DBoW2 copy includes `boost/dynamic_bitset.hpp`; the old `camera_models` had pulled Boost in); calibration and acknowledgement text in `README.md` |
| `a014059` | 2026-10-18 | `vins/CMakeLists.txt` installs `config/rpi_camera_v3/cam0_wide.yaml`; `vins/package.xml` adds `exec_depend` on `cine_sensing_config`; `vins/launch/{complete_vio,replay_vio}.launch.py` take `config_path` and `profile` arguments and regenerate the config at launch; `generate_vins_config.py` rewritten to read `cine_sensing_config` profiles and stop writing `cam0_intrinsics`; removed `vins/run_vins.py`, `vins/launch_complete_vio.py`, `config/rpi_camera_v3/rpi_v3_mono_config.yaml` |
| `a014059` | 2026-10-19 | `vins/launch/complete_vio.launch.py`: starts the estimator and loop fusion after a `vins_start_delay` (default 5 s), passes a `use_transform` argument (default false) to `imu_bridge`, and looks for the depth node in `cine_depth` instead of the retired `depth_publisher` package |
| `1fb2079` | 2026-10-22 | `README.md`: a note at the top on how this copy differs from the upstream text below it |
| `1aba6e7` | 2026-10-24 | `vins/launch/complete_vio.launch.py`: starts `cine_depth` only with `use_depth:=true` (default false), since depth normally runs on a separate GPU machine, and fails the launch if it is asked for but not installed |
| `1aba6e7` | 2026-10-24 | `config/rpi_camera_v3/cam0_wide.yaml`: `camera_name` changed from `rpi_camera_v3_calibrated` to `rpi_camera_v3_wide`, since no calibration run is recorded for these intrinsics; the name is a label only |

The date is when the work was done; rows that share a commit are separate pieces of work
that landed in that one commit after the history was rewritten.

Run `git log -p <commit> -- third_party/vins_fusion` (or the pre-move path
`sensing_ws/src/VINS-Fusion-ROS2-humble-arm`) to see each change in full.

Kino-Studios also added first-party files inside this tree: the launch files and
`generate_vins_config.py` under `vins/launch/`, the diagnostic and unit tests under
`vins/tests/` (including `tests/unit/test_generate_vins_config.py`), the
Raspberry Pi Camera v3 configuration under `config/rpi_camera_v3/`, and the camera adapter
in `camera_models/` (`include/camera_models/camera.h`, `src/camera.cpp`, `tests/`).

## Ceres Solver version requirement

This code needs Ceres Solver **2.1 or older**. It uses `ceres::LocalParameterization`
(for example `loop_fusion/src/pose_graph.h`, `loop_fusion/src/pose_graph.cpp`,
`global_fusion/src/globalOpt.cpp`), which Ceres
removed in 2.2 in favour of `ceres::Manifold`. Ubuntu 24.04 ships Ceres 2.2, so Ceres 2.1
has to be built from source.

## OpenVINS camera classes

`camera_models/include/camera_models/open_vins/{CamBase.h,CamRadtan.h,CamEqui.h}` are copied
from [rpng/open_vins](https://github.com/rpng/open_vins), `ov_core/src/cam/`, at commit
`69488123ed9362dd44b6f28e7f4680abbff1442b` (master on 2026-10-16). Licence: GNU General Public
License v3 or later (see [`camera_models/LICENSE.open_vins`](camera_models/LICENSE.open_vins)),
used here under GPL-3.0-only. The files are byte-for-byte copies with no edits; they keep the
`ov_core` namespace and their relative `#include "CamBase.h"`.

They replace camodocal (CC-BY-SA 2.0), which VINS-Fusion shipped as `camera_models/`. Only the
`PINHOLE` and `KANNALA_BRANDT` camera YAML models carry over; `MEI`, `SCARAMUZZA` and
`PINHOLE_FULL` files now make `loadCameraFromYaml` throw. `camera_models/tests/test_camera.cpp`
checks the replacement against reference values camodocal itself produced before it was removed.
