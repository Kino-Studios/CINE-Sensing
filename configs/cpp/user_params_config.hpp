/**
 * @file user_params_config.hpp
 * @brief User parameter configuration accessor for CINE-Sensing
 *
 * IMPORTANT: JSON files in configs/json/ are the single source of truth.
 * This header provides convenience constants, but for runtime configuration,
 * use config_loader.hpp to load from user_params.json.
 *
 * See: configs/json/user_params.json
 */

#ifndef CINE_USER_PARAMS_CONFIG_HPP
#define CINE_USER_PARAMS_CONFIG_HPP

#include <array>
#include <utility>

namespace cine {
namespace config {

// JSON config file for user parameters
constexpr const char* USER_PARAMS_JSON = "user_params.json";

/**
 * @brief Default values for model detection - load from JSON at runtime
 *
 * These are compile-time defaults. For runtime values, load from:
 *   configs/json/user_params.json -> "ModelDetectionConstants"
 */
namespace ModelDetectionDefaults {
    constexpr const char* MODEL_PATH =
        "/home/fishnos/bspline-cinematography-generator-research/training/checkpoints/pre-export/homeobjects_yolo11n_trained.pt";
    constexpr const char* CAMERA_IMAGE_TOPIC = "/camera/image_raw";
    constexpr const char* BOUNDING_BOX_TOPIC = "/object_detection/bounding_box";
    constexpr const char* IMAGE_ENCODING = "bgr8";
    constexpr int OBB_COORDS_LENGTH = 8;
    constexpr int NUM_BOUNDING_BOX_POINTS = 4;
    constexpr int QOS_DEPTH = 10;
    constexpr double CONFIDENCE_THRESHOLD = 0.25;
    constexpr double IOU_THRESHOLD = 0.4;
}

/**
 * @brief Default values for user-requested params - load from JSON at runtime
 */
namespace UserRequestedDefaults {
    constexpr int USER_OBJECT_ID = 2;
}

/**
 * @brief Default values for rule of thirds - load from JSON at runtime
 */
namespace RuleOfThirdsDefaults {
    constexpr double FRAME_WIDTH = 1152.0;
    constexpr double FRAME_HEIGHT = 648.0;
    constexpr double GRID_LINE_1_X = FRAME_WIDTH / 3.0;
    constexpr double GRID_LINE_2_X = 2.0 * FRAME_WIDTH / 3.0;
    constexpr double GRID_LINE_1_Y = FRAME_HEIGHT / 3.0;
    constexpr double GRID_LINE_2_Y = 2.0 * FRAME_HEIGHT / 3.0;
}

} // namespace config
} // namespace cine

#endif // CINE_USER_PARAMS_CONFIG_HPP
