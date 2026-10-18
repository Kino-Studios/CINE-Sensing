# Upstream record: VINS-Fusion (ROS 2 Humble, ARM fork)

## Lineage

1. [HKUST-Aerial-Robotics/VINS-Fusion](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion),
   the original ROS 1 visual-inertial odometry system.
2. [zinuok/VINS-Fusion-ROS2](https://github.com/zinuok/VINS-Fusion-ROS2), a ROS 2 port.
3. A "humble-arm" fork of that port, aimed at ROS 2 Humble on ARM boards, which this
   directory was copied from.

The base commit of the "humble-arm" fork is **unknown**: the code was imported into this
repository as a plain copy (commit `ada6c39`, 2026-01-03) without recording which upstream
commit it came from.

## Licence

GNU General Public License v3 (see [`LICENCE`](LICENCE)). The upstream headers in every
source file are kept unchanged.

## Modifications by Kino-Studios

Modified by Kino-Studios, 2026. This notice is given under section 5a of the GPLv3: the
files below differ from the code as imported.

| Commit    | Date       | Files changed                                                                                                                                              |
| --------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `f321c35` | 2026-01-31 | `camera_models/CMakeLists.txt`                                                                                                                              |
| `78c65ae` | 2026-01-31 | `vins/src/estimator/{estimator,feature_manager,parameters}.{cpp,h}`, `vins/src/featureTracker/feature_tracker.{cpp,h}`, `vins/src/rosNodeTest.cpp`, `loop_fusion/src/pose_graph_node.cpp` |
| `7481a5f` | 2026-02-06 | `package.xml` of `vins`, `loop_fusion`, `camera_models`, `global_fusion`                                                                                    |
| `e8e64da` | 2026-02-23 | `vins/src/utility/image_encodings.hpp`, `loop_fusion/src/image_encodings.hpp` (encoding matching rewritten with C++11 `std::regex`)                         |
| (uncommitted) | 2026-10-15 | Port to ROS 2 Jazzy: `#include <cv_bridge/cv_bridge.h>` → `cv_bridge.hpp` in `loop_fusion/src/{parameters.h,pose_graph_node.cpp}`, `vins/src/{KITTIOdomTest.cpp,rosNodeTest.cpp,utility/visualization.h}` (Jazzy ships only the `.hpp` header); `package.xml` dependencies declared by rosdep key; `global_fusion/models/car.dae` (12.7 MB) moved to a release download and `global_fusion/CMakeLists.txt` now installs `models/` |
| (uncommitted) | 2026-10-16 | camodocal camera library (CC-BY-SA 2.0, not GPL-3.0 compatible) replaced by OpenVINS's camera classes: deleted `camera_models/{include/camodocal/,src/{calib,camera_models,chessboard,gpl,sparse_graph}/,src/intrinsic_calib.cc,cmake/,camera_calib_example/,LICENSE.camodocal}` (including the `Calibrations` tool); added `camera_models/include/camera_models/open_vins/` (see below), `LICENSE.open_vins`, and a first-party adapter; rewrote `camera_models/{CMakeLists.txt,package.xml}`; callers switched to `camera_models::loadCameraFromYaml` in `vins/src/featureTracker/feature_tracker.{cpp,h}` and `loop_fusion/src/{keyframe.h,parameters.h,pose_graph_node.cpp}`; `loop_fusion/package.xml` now declares `boost` itself (its DBoW2 copy includes `boost/dynamic_bitset.hpp`; the old `camera_models` had pulled Boost in); calibration and acknowledgement text in `README.md` |

Run `git log -p <commit> -- third_party/vins_fusion` (or the pre-move path
`sensing_ws/src/VINS-Fusion-ROS2-humble-arm`) to see each change in full.

Kino-Studios also added first-party files inside this tree: the launch files and
`generate_vins_config.py` under `vins/launch/`, `vins/run_vins.py`,
`vins/launch_complete_vio.py`, the diagnostic and unit tests under `vins/tests/`, the
Raspberry Pi Camera v3 configuration under `config/rpi_camera_v3/`, and the camera adapter
in `camera_models/` (`include/camera_models/camera.h`, `src/camera.cpp`, `tests/`, `README.md`).

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
