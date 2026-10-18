// Copyright (C) 2026 Kino-Studios
// SPDX-License-Identifier: GPL-3.0-only
//
// Checks that the OpenVINS-backed camera reproduces camodocal, the camera
// library VINS-Fusion used before it was replaced for licence reasons.
//
// The reference files tests/fixtures/reference_lift_projective.csv and
// tests/fixtures/reference_space_to_plane.csv were written by camodocal itself
// (the camera_models sources as vendored before the swap, recoverable from
// git history), on 2026-10-16, with:
//
//   docker run --rm -e MAKEFLAGS=-j4 \
//     -v <scratch>:/scratch -v <camera_models>/tests/fixtures:/data \
//     cine-verify:jazzy bash /scratch/reference_generator/run_in_container.sh
//
// where run_in_container.sh compiled generate_reference.cpp against
// camodocal's src/camera_models/*.cc and src/gpl/*.cc and ran it on /data.
// The generator lifts a 7x7 pixel grid (corners included) plus the principal
// point, and projects 25 points spread over the field of view at depths of
// 0.5 m and 6 m, for each of the three camera YAMLs in tests/fixtures.
//
// The generator keeps a lifted pixel only if camodocal's own round trip,
// spaceToPlane(liftProjective(pixel)), lands within 1e-4 px of it; it drops
// the rest rather than recording garbage. This only bites on the cine
// calibration: its distortion polynomial r(1 + k1 r^2 + k2 r^4), with k1 and
// k2 both negative, peaks near a distorted radius of 1.065, so pixels beyond
// that normalised radius (the left and right image edges) have no preimage in
// either library, and the pixels just inside it are where neither library's
// fixed-point iteration converges.

#include <algorithm>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "camera_models/camera.h"

namespace {

const std::string kDataDir = CAMERA_MODELS_TEST_DATA_DIR;

struct ReferenceRow {
  std::string camera_file;
  std::vector<double> input;
  std::vector<double> expected;
};

// Reads "camera,<input_count inputs>,<remaining expected values>" rows.
std::vector<ReferenceRow> ReadReference(const std::string& file_name, int input_count) {
  std::ifstream file(kDataDir + "/" + file_name);
  if (!file) {
    throw std::runtime_error("cannot open " + file_name);
  }
  std::vector<ReferenceRow> rows;
  std::string line;
  std::getline(file, line);
  while (std::getline(file, line)) {
    std::stringstream stream(line);
    std::string field;
    ReferenceRow row;
    std::getline(stream, row.camera_file, ',');
    for (int column = 0; std::getline(stream, field, ','); ++column) {
      (column < input_count ? row.input : row.expected).push_back(std::stod(field));
    }
    rows.push_back(row);
  }
  return rows;
}

// Largest per-component difference between the camera's lifted rays and
// camodocal's, over every reference row for this camera.
double MaxLiftError(const std::string& camera_file) {
  const camera_models::CameraPtr camera = camera_models::loadCameraFromYaml(kDataDir + "/" + camera_file);
  double max_error = 0.0;
  int row_count = 0;
  for (const ReferenceRow& row : ReadReference("reference_lift_projective.csv", 2)) {
    if (row.camera_file != camera_file) continue;
    Eigen::Vector3d ray;
    camera->liftProjective(Eigen::Vector2d(row.input[0], row.input[1]), ray);
    const Eigen::Vector3d expected(row.expected[0], row.expected[1], row.expected[2]);
    max_error = std::max(max_error, (ray - expected).cwiseAbs().maxCoeff());
    ++row_count;
  }
  if (row_count == 0) {
    throw std::runtime_error("no lift reference rows for " + camera_file);
  }
  std::cout << "[ MEASURED ] " << camera_file << " liftProjective max error " << max_error << " over "
            << row_count << " pixels\n";
  return max_error;
}

// Largest per-component pixel difference between the camera's projections
// and camodocal's, over every reference row for this camera.
double MaxProjectionError(const std::string& camera_file) {
  const camera_models::CameraPtr camera = camera_models::loadCameraFromYaml(kDataDir + "/" + camera_file);
  double max_error = 0.0;
  int row_count = 0;
  for (const ReferenceRow& row : ReadReference("reference_space_to_plane.csv", 3)) {
    if (row.camera_file != camera_file) continue;
    Eigen::Vector2d pixel;
    camera->spaceToPlane(Eigen::Vector3d(row.input[0], row.input[1], row.input[2]), pixel);
    const Eigen::Vector2d expected(row.expected[0], row.expected[1]);
    max_error = std::max(max_error, (pixel - expected).cwiseAbs().maxCoeff());
    ++row_count;
  }
  if (row_count == 0) {
    throw std::runtime_error("no projection reference rows for " + camera_file);
  }
  std::cout << "[ MEASURED ] " << camera_file << " spaceToPlane max error " << max_error << " px over "
            << row_count << " points\n";
  return max_error;
}

TEST(CameraTest, LiftProjectiveMatchesCamodocalReferenceForRpiWideCamera) {
  EXPECT_LE(MaxLiftError("pinhole_rpi_camera_v3_wide.yaml"), 1e-5);
}

TEST(CameraTest, LiftProjectiveMatchesCamodocalReferenceForCineCalibration) {
  EXPECT_LE(MaxLiftError("pinhole_cine_calibration.yaml"), 1e-5);
}

TEST(CameraTest, LiftProjectiveMatchesCamodocalReferenceForKannalaBrandtCamera) {
  EXPECT_LE(MaxLiftError("kannala_brandt_synthetic.yaml"), 1e-5);
}

TEST(CameraTest, SpaceToPlaneMatchesCamodocalReferenceForRpiWideCamera) {
  EXPECT_LE(MaxProjectionError("pinhole_rpi_camera_v3_wide.yaml"), 0.01);
}

TEST(CameraTest, SpaceToPlaneMatchesCamodocalReferenceForCineCalibration) {
  EXPECT_LE(MaxProjectionError("pinhole_cine_calibration.yaml"), 0.01);
}

TEST(CameraTest, SpaceToPlaneMatchesCamodocalReferenceForKannalaBrandtCamera) {
  EXPECT_LE(MaxProjectionError("kannala_brandt_synthetic.yaml"), 0.01);
}

TEST(CameraTest, PinholeLiftReturnsRayOnNormalisedPlane) {
  const camera_models::CameraPtr camera =
      camera_models::loadCameraFromYaml(kDataDir + "/pinhole_rpi_camera_v3_wide.yaml");
  Eigen::Vector3d ray;

  camera->liftProjective(Eigen::Vector2d(0.0, 0.0), ray);

  EXPECT_EQ(ray.z(), 1.0);
}

TEST(CameraTest, LoadingUnsupportedModelThrows) {
  const std::string path = kDataDir + "/mei_unsupported.yaml";
  try {
    camera_models::loadCameraFromYaml(path);
    FAIL() << "expected std::runtime_error";
  } catch (const std::runtime_error& error) {
    EXPECT_PRED_FORMAT2(testing::IsSubstring, "MEI", error.what());
    EXPECT_PRED_FORMAT2(testing::IsSubstring, path, error.what());
  }
}

TEST(CameraTest, LoadingMissingFileThrows) {
  const std::string path = kDataDir + "/no_such_camera.yaml";
  try {
    camera_models::loadCameraFromYaml(path);
    FAIL() << "expected std::runtime_error";
  } catch (const std::runtime_error& error) {
    EXPECT_PRED_FORMAT2(testing::IsSubstring, path, error.what());
  }
}

}  // namespace
