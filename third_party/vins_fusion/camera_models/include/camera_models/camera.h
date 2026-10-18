// Copyright (C) 2026 Kino-Studios
//
// This program is free software: you can redistribute it and/or modify it
// under the terms of the GNU General Public License as published by the Free
// Software Foundation, version 3.
//
// This program is distributed in the hope that it will be useful, but WITHOUT
// ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
// FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
// more details.
//
// You should have received a copy of the GNU General Public License along
// with this program. If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-License-Identifier: GPL-3.0-only

#ifndef CAMERA_MODELS_CAMERA_H_
#define CAMERA_MODELS_CAMERA_H_

#include <memory>
#include <string>

#include <Eigen/Core>

namespace ov_core {
class CamBase;
}  // namespace ov_core

namespace camera_models {

enum class ModelType {
  // Pinhole with radial-tangential distortion (k1, k2, p1, p2).
  kPinhole,
  // Kannala-Brandt equidistant fisheye (k2..k5 in camodocal's naming).
  kKannalaBrandt,
};

// Intrinsics in OpenVINS order: fx, fy, cx, cy, then four distortion terms
// (k1, k2, p1, p2 for pinhole; the theta^3..theta^9 coefficients for
// Kannala-Brandt).
using Intrinsics = Eigen::Matrix<double, 8, 1>;

// A calibrated monocular camera, backed by OpenVINS's camera classes and
// exposing the two calls VINS-Fusion made on camodocal's cameras.
class Camera {
 public:
  Camera(ModelType model_type, int image_width, int image_height, const Intrinsics& intrinsics);
  ~Camera();

  Camera(const Camera&) = delete;
  Camera& operator=(const Camera&) = delete;

  // Lifts a pixel to its projective ray. As in camodocal, the pinhole model
  // returns the ray on the normalised plane (x, y, 1) and the Kannala-Brandt
  // model returns it with unit length.
  void liftProjective(const Eigen::Vector2d& pixel, Eigen::Vector3d& ray) const;

  // Projects a point in the camera frame (z > 0) to a pixel.
  void spaceToPlane(const Eigen::Vector3d& point, Eigen::Vector2d& pixel) const;

  ModelType model_type() const { return model_type_; }

 private:
  ModelType model_type_;
  std::unique_ptr<ov_core::CamBase> open_vins_camera_;
};

using CameraPtr = std::shared_ptr<Camera>;

// Reads a camodocal-format camera YAML (model_type PINHOLE or KANNALA_BRANDT).
// Throws std::runtime_error naming the file if it cannot be opened, or naming
// the file and the model if the model is not supported.
CameraPtr loadCameraFromYaml(const std::string& path);

}  // namespace camera_models

#endif  // CAMERA_MODELS_CAMERA_H_
