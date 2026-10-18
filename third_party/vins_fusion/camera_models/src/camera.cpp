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

#include "camera_models/camera.h"

#include <stdexcept>

#include <opencv2/core/persistence.hpp>

#include "camera_models/open_vins/CamEqui.h"
#include "camera_models/open_vins/CamRadtan.h"

namespace camera_models {

Camera::Camera(ModelType model_type, int image_width, int image_height, const Intrinsics& intrinsics)
    : model_type_(model_type) {
  if (model_type == ModelType::kPinhole) {
    open_vins_camera_ = std::make_unique<ov_core::CamRadtan>(image_width, image_height);
  } else {
    open_vins_camera_ = std::make_unique<ov_core::CamEqui>(image_width, image_height);
  }
  open_vins_camera_->set_value(intrinsics);
}

Camera::~Camera() = default;

void Camera::liftProjective(const Eigen::Vector2d& pixel, Eigen::Vector3d& ray) const {
  const Eigen::Vector2d normalized = open_vins_camera_->undistort_d(pixel);
  ray << normalized.x(), normalized.y(), 1.0;
  if (model_type_ == ModelType::kKannalaBrandt) {
    ray.normalize();
  }
}

void Camera::spaceToPlane(const Eigen::Vector3d& point, Eigen::Vector2d& pixel) const {
  pixel = open_vins_camera_->distort_d(point.head<2>() / point.z());
}

CameraPtr loadCameraFromYaml(const std::string& path) {
  cv::FileStorage storage(path, cv::FileStorage::READ);
  if (!storage.isOpened()) {
    throw std::runtime_error("camera_models: cannot open camera file " + path);
  }
  std::string model_name;
  storage["model_type"] >> model_name;
  const int image_width = static_cast<int>(storage["image_width"]);
  const int image_height = static_cast<int>(storage["image_height"]);

  Intrinsics intrinsics;
  if (model_name == "PINHOLE") {
    const cv::FileNode projection = storage["projection_parameters"];
    const cv::FileNode distortion = storage["distortion_parameters"];
    intrinsics << static_cast<double>(projection["fx"]), static_cast<double>(projection["fy"]),
        static_cast<double>(projection["cx"]), static_cast<double>(projection["cy"]),
        static_cast<double>(distortion["k1"]), static_cast<double>(distortion["k2"]),
        static_cast<double>(distortion["p1"]), static_cast<double>(distortion["p2"]);
    return std::make_shared<Camera>(ModelType::kPinhole, image_width, image_height, intrinsics);
  }
  if (model_name == "KANNALA_BRANDT") {
    const cv::FileNode projection = storage["projection_parameters"];
    intrinsics << static_cast<double>(projection["mu"]), static_cast<double>(projection["mv"]),
        static_cast<double>(projection["u0"]), static_cast<double>(projection["v0"]),
        static_cast<double>(projection["k2"]), static_cast<double>(projection["k3"]),
        static_cast<double>(projection["k4"]), static_cast<double>(projection["k5"]);
    return std::make_shared<Camera>(ModelType::kKannalaBrandt, image_width, image_height, intrinsics);
  }
  // camodocal treated a missing model_type as MEI.
  const std::string reported_model = model_name.empty() ? "MEI (no model_type given)" : model_name;
  throw std::runtime_error("camera_models: camera model " + reported_model + " in " + path +
                           " is not supported; use PINHOLE or KANNALA_BRANDT");
}

}  // namespace camera_models
