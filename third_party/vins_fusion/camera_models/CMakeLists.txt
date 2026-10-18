cmake_minimum_required(VERSION 3.5)
project(camera_models)

set(CMAKE_CXX_STANDARD 14)
add_compile_options(-Wextra -Wpedantic -Wno-deprecated-copy)

find_package(ament_cmake REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(OpenCV REQUIRED)

add_library(camera_models src/camera.cpp)
target_include_directories(camera_models PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_include_directories(camera_models SYSTEM PUBLIC ${EIGEN3_INCLUDE_DIRS})
target_link_libraries(camera_models ${OpenCV_LIBS})

ament_export_include_directories(include)
ament_export_libraries(camera_models)
ament_export_dependencies(Eigen3 OpenCV)

install(TARGETS camera_models
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

install(DIRECTORY include/
  DESTINATION include/)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_camera tests/test_camera.cpp)
  target_compile_definitions(test_camera PRIVATE
    CAMERA_MODELS_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/tests/fixtures")
  target_link_libraries(test_camera camera_models)
endif()

ament_package()
