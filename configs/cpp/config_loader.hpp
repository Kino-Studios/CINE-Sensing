/**
 * @file config_loader.hpp
 * @brief JSON configuration loader for CINE-Sensing C++ components
 *
 * This header provides utilities to load configuration from JSON files.
 * JSON files in configs/json/ are the single source of truth.
 *
 * Usage:
 *   #include "config_loader.hpp"
 *   auto config = cine::config::load_json("user_params.json");
 *   double threshold = config["ModelDetectionConstants"]["CONFIDENCE_THRESHOLD"];
 *
 * Note: Requires nlohmann/json library (https://github.com/nlohmann/json)
 *       or you can use ROS2's built-in JSON parsing.
 */

#ifndef CINE_CONFIG_LOADER_HPP
#define CINE_CONFIG_LOADER_HPP

#include <fstream>
#include <stdexcept>

// If using nlohmann/json:
// #include <nlohmann/json.hpp>
// using json = nlohmann::json;

// Alternative: Use ROS2 parameter files directly via launch files

namespace cine {
namespace config {

/**
 * @brief Get the path to the JSON config directory
 *
 * This should be set at runtime based on your package location.
 * For ROS2, use ament_index to find the package share directory.
 */
inline std::string get_config_dir() {
    // Default path - override in your application
    return "configs/json/";
}

/**
 * @brief Load JSON config file paths for reference
 *
 * The actual JSON loading depends on your JSON library choice.
 * Common options:
 *   - nlohmann/json (header-only, easy to use)
 *   - RapidJSON (fast, low memory)
 *   - ROS2 parameter server (for ROS2 nodes)
 */
struct ConfigPaths {
    static constexpr const char* USER_PARAMS = "user_params.json";
    static constexpr const char* CAMERA = "camera.json";
    static constexpr const char* GYROSCOPE = "gyroscope.json";
};

/**
 * @brief Example function to load config using nlohmann/json
 *
 * Uncomment and use if you have nlohmann/json installed:
 *
 * inline json load_json(const std::string& filename) {
 *     std::ifstream file(get_config_dir() + filename);
 *     if (!file.is_open()) {
 *         throw std::runtime_error("Cannot open config: " + filename);
 *     }
 *     json config;
 *     file >> config;
 *     return config;
 * }
 */

} // namespace config
} // namespace cine

#endif // CINE_CONFIG_LOADER_HPP
