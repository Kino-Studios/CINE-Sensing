/**
 * @file gyroscope_config.hpp
 * @brief Gyroscope configuration accessor for CINE-Sensing
 *
 * IMPORTANT: JSON files in configs/json/ are the single source of truth.
 * This header provides convenience constants, but for runtime configuration,
 * use config_loader.hpp to load from gyroscope.json.
 *
 * See: configs/json/gyroscope.json
 */

#ifndef CINE_GYROSCOPE_CONFIG_HPP
#define CINE_GYROSCOPE_CONFIG_HPP

namespace cine {
namespace config {

// JSON config file for gyroscope parameters
constexpr const char* GYROSCOPE_JSON = "gyroscope.json";

/**
 * @brief Default values for gyroscope config - load from JSON at runtime
 *
 * These are compile-time defaults. For runtime values, load from:
 *   configs/json/gyroscope.json -> "gyroscope_data_publisher.ros__parameters"
 */
namespace GyroscopeDefaults {
    constexpr int BAUD_RATE = 921600;
    constexpr const char* SERIAL_PORT = "/dev/ttyAMA0";
    constexpr int SERIAL_PORT_BAUD_RATE = 921600;
}

} // namespace config
} // namespace cine

#endif // CINE_GYROSCOPE_CONFIG_HPP
