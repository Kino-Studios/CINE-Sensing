# camera_models

The camera model library VINS-Fusion uses to turn pixels into viewing rays
(`liftProjective`) and 3-D points into pixels (`spaceToPlane`).

The maths comes from [OpenVINS](https://github.com/rpng/open_vins)'s camera classes,
copied unchanged into `include/camera_models/open_vins/` (GPL-3.0-or-later, see
[`LICENSE.open_vins`](LICENSE.open_vins); pinned commit in `../UPSTREAM.md`). A thin
adapter, `include/camera_models/camera.h`, gives them the interface VINS-Fusion
calls and reads the camera YAML files. It replaced the camodocal library, whose
CC-BY-SA 2.0 licence is not compatible with this project's GPL-3.0.

## Supported models

| `model_type`     | Model                                        | YAML keys                                                               |
| ---------------- | -------------------------------------------- | ----------------------------------------------------------------------- |
| `PINHOLE`        | Pinhole, radial-tangential distortion        | `distortion_parameters{k1,k2,p1,p2}`, `projection_parameters{fx,fy,cx,cy}` |
| `KANNALA_BRANDT` | Kannala-Brandt (equidistant) fisheye         | `projection_parameters{k2,k3,k4,k5,mu,mv,u0,v0}`                         |

Both also read `image_width` and `image_height`. Any other model (`MEI`,
`SCARAMUZZA`, `PINHOLE_FULL`) makes `loadCameraFromYaml` throw `std::runtime_error`.

## Calibration

The camodocal calibration tool is gone. Calibrate with the ROS
[`camera_calibration`](https://index.ros.org/p/camera_calibration/) package or with
[Kalibr](https://github.com/ethz-asl/kalibr) (`pinhole-radtan` maps to `PINHOLE`,
`pinhole-equi` to `KANNALA_BRANDT`), and write the result in the format above.

## Tests

`tests/test_camera.cpp` checks the adapter against reference values that camodocal
itself produced for the cameras in `tests/fixtures/`; run it with `colcon test
--packages-select camera_models`.
