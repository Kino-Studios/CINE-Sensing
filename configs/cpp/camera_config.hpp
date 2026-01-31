/**
 * @file camera_config.hpp
 * @brief Camera configuration accessor for CINE-Sensing
 *
 * IMPORTANT: JSON files in configs/json/ are the single source of truth.
 * This header provides convenience constants, but for runtime configuration,
 * use config_loader.hpp to load from camera.json.
 *
 * See: configs/json/camera.json
 */

#ifndef CINE_CAMERA_CONFIG_HPP
#define CINE_CAMERA_CONFIG_HPP

#include <array>

namespace cine {
namespace config {

constexpr const char* CAMERA_JSON = "camera.json";

/**
 * @brief Default values for camera config - load from JSON at runtime
 *
 * These are compile-time defaults. For runtime values, load from:
 *   configs/json/camera.json -> "camera_publisher.ros__parameters"
 */
namespace CameraDefaults {
    constexpr int CAMERA_ID = 0;
    constexpr int IMAGE_WIDTH = 1920;
    constexpr int IMAGE_HEIGHT = 1080;
    constexpr double FPS = 30.0;
    constexpr const char* IMAGE_FORMAT = "BGR8";
    constexpr int JPEG_QUALITY = 95;
    constexpr const char* CAMERA_TOPIC = "/camera/image_raw";
    constexpr const char* CAMERA_INFO_TOPIC = "/camera/camera_info";
    constexpr const char* CAMERA_FRAME_ID = "camera_optical_frame";
    constexpr bool AUTO_EXPOSURE = true;
    constexpr int EXPOSURE_TIME_US = 10000;
    constexpr double ANALOG_GAIN = 1.0;
    constexpr double DIGITAL_GAIN = 1.0;
    constexpr bool WHITE_BALANCE_AUTO = true;
    constexpr double WHITE_BALANCE_RED_GAIN = 1.0;
    constexpr double WHITE_BALANCE_BLUE_GAIN = 1.0;
    constexpr int BUFFER_SIZE = 1;
    constexpr double PUBLISH_RATE = 30.0;
}

} // namespace config
} // namespace cine

#endif
